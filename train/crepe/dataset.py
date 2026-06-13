from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

CREPE_BINS = 360
_CENTS_MAPPING = (np.arange(CREPE_BINS) * 20) + 1997.3794084376191
SAMPLE_RATE = 16000
FRAME_LEN = 1024


def hz_to_cents(f_hz: np.ndarray | float) -> np.ndarray | float:
    return 1200.0 * np.log2(np.asarray(f_hz) / 10.0)


def midi_to_hz(m: float) -> float:
    return 440.0 * 2.0 ** ((m - 69.0) / 12.0)


def cents_to_bin_target(cents: float, sigma_cents: float = 25.0) -> np.ndarray:
    target = np.exp(-((_CENTS_MAPPING - cents) ** 2) / (2.0 * sigma_cents ** 2))
    target[target < 1e-3] = 0.0
    return target.astype(np.float32)


def _read_align_notetime(csv_path: Path) -> list[tuple[float, float, float]]:
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            try:
                onset = float(r["onset"]); offset = float(r["offset"])
                midi = float(r.get("midi_number") or r.get("midi"))
            except (KeyError, TypeError, ValueError):
                continue
            if offset > onset and midi > 0:
                rows.append((onset, offset, midi))
    rows.sort()
    return rows


def prepare_mosa(mosa_root: Path, out_dir: Path) -> None:
    import librosa
    import soundfile as sf

    unpacked = mosa_root / "_unpacked"
    search_root = unpacked if unpacked.exists() else mosa_root
    out_audio = out_dir / "audio"; out_audio.mkdir(parents=True, exist_ok=True)
    out_notes = out_dir / "notes"; out_notes.mkdir(parents=True, exist_ok=True)

    wavs = sorted(p for p in search_root.rglob("*_audio.wav"))
    if not wavs:
        wavs = sorted(search_root.rglob("*.wav"))
    print(f"[prepare] found {len(wavs)} audio files under {search_root}")

    n_ok = 0
    for wav in wavs:
        stem = wav.stem.replace("_audio", "")
        take_dir = wav.parent

        align = next(take_dir.rglob(f"{stem}*_align_notetime.csv"), None)
        if align is not None:
            note_rows = _read_align_notetime(align)
        else:
            ncsv = next(take_dir.rglob(f"{stem}*_note.csv"), None)
            note_rows = []
            if ncsv is not None:
                with open(ncsv) as f:
                    for r in csv.DictReader(f):
                        try:
                            on = float(r.get("Onset", 0)); off = float(r.get("Offset", on))
                            midi = float(r.get("MIDI number") or r.get("MIDI"))
                        except (TypeError, ValueError):
                            continue
                        if off > on and midi > 0:
                            note_rows.append((on, off, midi))
                note_rows.sort()
        if not note_rows:
            print(f"  [warn] no usable note annotation for {stem}; skipping")
            continue

        y, _ = librosa.load(str(wav), sr=SAMPLE_RATE, mono=True)
        sf.write(out_audio / f"{stem}.wav", y, SAMPLE_RATE)
        with open(out_notes / f"{stem}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["onset_sec", "offset_sec", "midi"])
            w.writerows(note_rows)
        n_ok += 1
        print(f"  [ok] {stem}: {len(y)/SAMPLE_RATE:.1f}s, {len(note_rows)} notes")

    print(f"[prepare] wrote {n_ok} recordings to {out_dir}")


class CrepeFrameDataset:

    def __init__(self, prepared_dir: str | Path, hop_ms: float = 10.0,
                 unvoiced_keep_prob: float = 0.1, sigma_cents: float = 25.0,
                 seed: int = 0):
        import torch
        self.prepared_dir = Path(prepared_dir)
        self.hop = int(SAMPLE_RATE * hop_ms / 1000.0)
        self.unvoiced_keep_prob = unvoiced_keep_prob
        self.sigma_cents = sigma_cents
        self._rng = np.random.default_rng(seed)
        self._index: list[tuple[Path, int, float]] = []
        self._audio_cache: dict[Path, np.ndarray] = {}
        self._build_index()

    def _build_index(self) -> None:
        audio_dir = self.prepared_dir / "audio"
        notes_dir = self.prepared_dir / "notes"
        for wav in sorted(audio_dir.glob("*.wav")):
            csv_path = notes_dir / f"{wav.stem}.csv"
            if not csv_path.exists():
                continue
            import soundfile as sf
            info = sf.info(str(wav))
            n_samples = int(info.frames)
            notes = []
            with open(csv_path) as f:
                for r in csv.DictReader(f):
                    notes.append((float(r["onset_sec"]), float(r["offset_sec"]), float(r["midi"])))
            for start in range(0, max(0, n_samples - FRAME_LEN), self.hop):
                t = (start + FRAME_LEN / 2) / SAMPLE_RATE
                midi = next((m for (a, b, m) in notes if a <= t < b), -1.0)
                if midi < 0 and self._rng.random() > self.unvoiced_keep_prob:
                    continue
                self._index.append((wav, start, midi))
        self._rng.shuffle(self._index)
        n_v = sum(1 for _, _, m in self._index if m >= 0)
        print(f"[dataset] {len(self._index)} frames ({n_v} voiced / "
              f"{len(self._index) - n_v} unvoiced) from "
              f"{len(set(p for p, _, _ in self._index))} recordings")

    def _load_audio(self, path: Path) -> np.ndarray:
        if path not in self._audio_cache:
            import soundfile as sf
            y, _ = sf.read(str(path), dtype="float32")
            if y.ndim > 1:
                y = y.mean(axis=1)
            self._audio_cache[path] = y
        return self._audio_cache[path]

    def __len__(self) -> int:
        return len(self._index)

    def __getitem__(self, i: int):
        import torch
        path, start, midi = self._index[i]
        y = self._load_audio(path)
        frame = y[start:start + FRAME_LEN].astype(np.float32)
        if frame.shape[0] < FRAME_LEN:
            frame = np.pad(frame, (0, FRAME_LEN - frame.shape[0]))
        frame = frame - frame.mean()
        std = frame.std()
        if std > 1e-8:
            frame = frame / std
        if midi >= 0:
            target = cents_to_bin_target(hz_to_cents(midi_to_hz(midi)), self.sigma_cents)
        else:
            target = np.zeros(CREPE_BINS, dtype=np.float32)
        return torch.from_numpy(frame), torch.from_numpy(target)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Prepare the MOSA violin subset for CREPE fine-tuning")
    ap.add_argument("--mosa-root", required=True, type=Path, help="datasets/MOSA (must contain _unpacked/ or raw files)")
    ap.add_argument("--out", required=True, type=Path, help="output dir, e.g. datasets/MOSA/violin")
    args = ap.parse_args()
    prepare_mosa(args.mosa_root, args.out)
