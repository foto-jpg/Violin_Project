from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import torch
import torchcrepe

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from training.metrics import (
    pitch_mae_cents,
    raw_chroma_accuracy,
    raw_pitch_accuracy,
)

SAMPLE_RATE = 16000
HOP_LENGTH = 160
FMIN, FMAX = 50.0, 2000.0
CONF_THRESHOLD = 0.5
VIOLIN_PROGRAM = 41
MUSICNET_NATIVE_SR = 44100


def _piecewise_f0(notes: list[tuple[float, float, float]], n_frames: int,
                  hop_sec: float) -> tuple[np.ndarray, np.ndarray]:
    true_hz = np.zeros(n_frames, dtype=np.float32)
    voiced = np.zeros(n_frames, dtype=bool)
    for onset, offset, midi in notes:
        i0 = max(0, int(round(onset / hop_sec)))
        i1 = min(n_frames, int(round(offset / hop_sec)))
        if i1 <= i0:
            continue
        f = float(librosa.midi_to_hz(midi))
        for i in range(i0, i1):
            if not voiced[i] or f > true_hz[i]:
                true_hz[i] = f
                voiced[i] = True
    return true_hz, voiced


def gt_f0_mosa(notes_csv: Path, n_frames: int, hop_sec: float):
    notes = []
    with open(notes_csv) as f:
        for r in csv.DictReader(f):
            try:
                onset = float(r["onset_sec"])
                offset = float(r["offset_sec"])
                midi = float(r["midi"])
            except (KeyError, ValueError):
                continue
            if offset > onset and midi > 0:
                notes.append((onset, offset, midi))
    notes.sort()
    return _piecewise_f0(notes, n_frames, hop_sec)


def gt_f0_musicnet(label_csv: Path, n_frames: int, hop_sec: float):
    notes = []
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
                notes.append((onset, offset, midi))
    notes.sort()
    return _piecewise_f0(notes, n_frames, hop_sec)


def load_model(checkpoint: Optional[Path], device: str):
    model = torchcrepe.Crepe("full")
    if checkpoint is not None:
        sd = torch.load(checkpoint, map_location=device, weights_only=True)
        model.load_state_dict(sd)
    else:
        weights = os.path.join(os.path.dirname(torchcrepe.__file__), "assets", "full.pth")
        model.load_state_dict(torch.load(weights, map_location=device, weights_only=True))
    return model.to(device).eval()


def _predict_on(model, audio: np.ndarray, device: str, batch_size: int):
    torchcrepe.infer.model = model
    torchcrepe.infer.capacity = "full"
    audio_t = torch.from_numpy(audio).float().unsqueeze(0).to(device)
    pitch, periodicity = torchcrepe.predict(
        audio_t, sample_rate=SAMPLE_RATE, hop_length=HOP_LENGTH,
        fmin=FMIN, fmax=FMAX, model="full",
        decoder=torchcrepe.decode.weighted_argmax,
        return_periodicity=True, device=device, batch_size=batch_size,
    )
    periodicity = torchcrepe.filter.median(periodicity, 3)
    pitch = torchcrepe.filter.mean(pitch, 3)
    return pitch.squeeze(0).cpu().numpy(), periodicity.squeeze(0).cpu().numpy()


def predict_f0(model, audio: np.ndarray, device: str):
    last_err = None
    for bs in (512, 128, 32):
        try:
            return _predict_on(model, audio, device, bs)
        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            msg = str(e).lower()
            if "out of memory" not in msg and "cuda" not in msg:
                raise
            last_err = e
            torch.cuda.empty_cache()
            print(f"    [oom] batch {bs} failed, retrying smaller…")
    print("    [oom] falling back to CPU for this recording")
    cpu_model = model.to("cpu")
    try:
        return _predict_on(cpu_model, audio, "cpu", 64)
    finally:
        try:
            model.to(device)
        except Exception:
            pass


def evaluate_recording(audio_path: Path, ann_path: Path, dataset: str,
                       model, device: str) -> dict | None:
    audio, _ = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
    if audio.size == 0:
        return None
    pred_hz, conf = predict_f0(model, audio, device)
    n = len(pred_hz)
    hop_sec = HOP_LENGTH / SAMPLE_RATE

    if dataset == "MOSA":
        true_hz, voiced_gt = gt_f0_mosa(ann_path, n, hop_sec)
    elif dataset == "MusicNet":
        true_hz, voiced_gt = gt_f0_musicnet(ann_path, n, hop_sec)
    elif dataset in ("URMP", "Bach10"):
        true_hz, voiced_gt = gt_f0_mosa(ann_path, n, hop_sec)
    else:
        return None

    voiced = voiced_gt & (conf >= CONF_THRESHOLD) & np.isfinite(pred_hz) & (pred_hz > 0)
    if voiced.sum() == 0:
        return None
    return {
        "rpa": raw_pitch_accuracy(pred_hz, true_hz, voiced),
        "rca": raw_chroma_accuracy(pred_hz, true_hz, voiced),
        "mae": pitch_mae_cents(pred_hz, true_hz, voiced),
        "frames_used": int(voiced.sum()),
    }


def load_test_rows(manifest_path: Path) -> list[dict]:
    rows = []
    with open(manifest_path) as f:
        for r in csv.DictReader(f):
            if r["role"] == "test":
                rows.append(r)
    return rows


def add_external_dataset(extra_rows: list[dict], root: Optional[Path], name: str):
    if not root or not root.exists():
        return
    audio_dir = root / "audio"
    notes_dir = root / "notes"
    if not audio_dir.exists() or not notes_dir.exists():
        return
    for wav in sorted(audio_dir.glob("*.wav")):
        ann = notes_dir / f"{wav.stem}.csv"
        if not ann.exists():
            continue
        extra_rows.append({
            "dataset": name,
            "filepath": str(wav.resolve()),
            "annotation_path": str(ann.resolve()),
        })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True,
                    help="Fine-tuned weights .pt produced by finetune_crepe.py")
    ap.add_argument("--urmp-root", type=Path, default=None)
    ap.add_argument("--bach10-root", type=Path, default=None)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    args = ap.parse_args()

    device = args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu"
    print(f"[eval] device = {device}")

    rows = load_test_rows(args.manifest)
    add_external_dataset(rows, args.urmp_root, "URMP")
    add_external_dataset(rows, args.bach10_root, "Bach10")
    print(f"[eval] {len(rows)} test recordings across datasets: "
          f"{sorted(set(r['dataset'] for r in rows))}")

    per_recording: list[dict] = []
    for model_name, ckpt in [("Pretrain", None), ("Finetuned", args.checkpoint)]:
        print(f"\n[eval] === Model: {model_name} ===")
        model = load_model(ckpt, device)
        for r in rows:
            try:
                m = evaluate_recording(Path(r["filepath"]), Path(r["annotation_path"]),
                                       r["dataset"], model, device)
            except Exception as e:
                print(f"  ! {r['dataset']}/{Path(r['filepath']).name}: {e}")
                continue
            if m is None:
                continue
            per_recording.append({
                "model": model_name, "dataset": r["dataset"],
                "file": Path(r["filepath"]).name, **m,
            })
            print(f"  {r['dataset']:10s}  {Path(r['filepath']).name:40s}  "
                  f"RPA {m['rpa']:.3f}  RCA {m['rca']:.3f}  MAE {m['mae']:5.1f}c")

    datasets_ordered = ["MOSA", "MusicNet", "URMP", "Bach10"]
    datasets_present = [d for d in datasets_ordered if any(r["dataset"] == d for r in per_recording)]
    metric_names = ["RPA", "RCA", "MAE"]
    metric_keys = {"RPA": "rpa", "RCA": "rca", "MAE": "mae"}

    def agg(model: str, dataset: str, key: str) -> float:
        vals = [r[key] for r in per_recording
                if r["model"] == model and r["dataset"] == dataset
                and not np.isnan(r[key])]
        return float(np.mean(vals)) if vals else float("nan")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        w = csv.writer(f)
        header = ["Model"]
        for d in datasets_present:
            for m in metric_names:
                unit = "%" if m != "MAE" else "cents"
                header.append(f"{d}_{m}_{unit}")
        w.writerow(header)
        for model_name in ("Pretrain", "Finetuned"):
            row = [f"Model ({model_name})"]
            for d in datasets_present:
                for m in metric_names:
                    v = agg(model_name, d, metric_keys[m])
                    if np.isnan(v):
                        row.append("")
                    elif m == "MAE":
                        row.append(f"{v:.1f}")
                    else:
                        row.append(f"{v*100:.1f}")
            w.writerow(row)

    detail_path = args.output.with_name(args.output.stem + "_detail.csv")
    with open(detail_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "dataset", "file",
                                          "rpa", "rca", "mae", "frames_used"])
        w.writeheader()
        for r in per_recording:
            w.writerow(r)

    print(f"\n[eval] wrote {args.output}")
    print(f"       {detail_path}")


if __name__ == "__main__":
    main()
