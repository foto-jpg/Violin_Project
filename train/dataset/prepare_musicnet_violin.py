"""Prepare the 9 Solo Violin recordings from MusicNet for CREPE fine-tuning.

Steps per recording:
  1. Resample WAV from 44.1 kHz to 16 kHz mono.
  2. Convert MusicNet label CSV (start_time/end_time in samples, instrument, note)
     to the MOSA-style notes CSV: onset_sec, offset_sec, midi.
     Keep notes where instrument == 41 (violin program).

Output layout matches what CrepeFrameDataset / scan_mosa() expect:
  <out>/audio/<id>.wav
  <out>/notes/<id>.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import librosa
import soundfile as sf

SAMPLE_RATE = 16000
MUSICNET_NATIVE_SR = 44100
VIOLIN_PROGRAM = 41

SOLO_VIOLIN_IDS = ["2186", "2191", "2241", "2242", "2243", "2244", "2288", "2289", "2659"]


def find_pair(musicnet_root: Path, rec_id: str) -> tuple[Path, Path] | None:
    for data_split, label_split in (("train_data", "train_labels"),
                                     ("test_data", "test_labels")):
        wav = musicnet_root / "musicnet" / data_split / f"{rec_id}.wav"
        csv_path = musicnet_root / "musicnet" / label_split / f"{rec_id}.csv"
        if wav.exists() and csv_path.exists():
            return wav, csv_path
    return None


def convert_labels(label_csv: Path) -> list[tuple[float, float, float]]:
    rows = []
    with open(label_csv) as f:
        for r in csv.DictReader(f):
            try:
                inst = int(r["instrument"])
            except (KeyError, ValueError):
                continue
            if inst != VIOLIN_PROGRAM:
                continue
            try:
                onset = float(r["start_time"]) / MUSICNET_NATIVE_SR
                offset = float(r["end_time"]) / MUSICNET_NATIVE_SR
                midi = float(r["note"])
            except (KeyError, ValueError):
                continue
            if offset > onset and midi > 0:
                rows.append((onset, offset, midi))
    rows.sort()
    return rows


def main():
    if len(sys.argv) != 3:
        print("usage: prepare_musicnet_violin.py <MusicNet root> <out dir>", file=sys.stderr)
        sys.exit(2)
    mn_root = Path(sys.argv[1])
    out = Path(sys.argv[2])
    audio_out = out / "audio"; audio_out.mkdir(parents=True, exist_ok=True)
    notes_out = out / "notes"; notes_out.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    for rec_id in SOLO_VIOLIN_IDS:
        pair = find_pair(mn_root, rec_id)
        if pair is None:
            print(f"  [skip] {rec_id}: wav or label missing")
            continue
        wav_path, csv_path = pair
        notes = convert_labels(csv_path)
        if not notes:
            print(f"  [skip] {rec_id}: no violin (program=41) notes")
            continue

        y, _ = librosa.load(str(wav_path), sr=SAMPLE_RATE, mono=True)
        out_wav = audio_out / f"mn_{rec_id}.wav"
        sf.write(out_wav, y, SAMPLE_RATE)
        out_csv = notes_out / f"mn_{rec_id}.csv"
        with open(out_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["onset_sec", "offset_sec", "midi"])
            for on, off, m in notes:
                w.writerow([f"{on:.6f}", f"{off:.6f}", f"{m:.1f}"])
        n_ok += 1
        print(f"  [ok] mn_{rec_id}: {len(y)/SAMPLE_RATE:.1f}s, {len(notes)} violin notes")

    print(f"[prepare-mn] wrote {n_ok} recordings to {out}")


if __name__ == "__main__":
    main()
