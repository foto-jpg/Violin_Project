"""Evaluate CREPE (pretrained or fine-tuned) on the spec's test sets.

Spec-compliant output:
  OUTPUT_DIR/baseline_metrics.json   (when --mode pretrained)
  OUTPUT_DIR/finetuned_metrics.json  (when --mode finetuned)
  matching .md sibling for human reading

Test sets evaluated:
  - MOSA_test     : manifest rows dataset=MOSA, role=test
  - MusicNet_test : manifest rows dataset=MusicNet, role=test (polyphonic mix; GT filters to violin program=41)
  - Bach10        : <bach10>/<piece>/<piece>-violin.wav + -GTF0s.mat (row 0 = violin, MIDI per 10ms frame)
  - URMP          : null (skipped by user decision)

Per spec section 2.3 audio preprocessing: 16 kHz mono, voicing threshold 0.5.
Aggregation: per-recording RPA/RCA/MAE then mean across recordings; n_frames = total voiced frames used.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import scipy.io
import soundfile as sf
import torch
import torchcrepe

# import metrics from existing module
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
BACH10_GT_HOP_SEC = 0.01  # 10 ms


def _piecewise_f0_from_notes(notes, n_frames, hop_sec):
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
                on = float(r["onset_sec"]); off = float(r["offset_sec"]); m = float(r["midi"])
            except (KeyError, ValueError):
                continue
            if off > on and m > 0:
                notes.append((on, off, m))
    notes.sort()
    return _piecewise_f0_from_notes(notes, n_frames, hop_sec)


def gt_f0_musicnet(label_csv: Path, n_frames: int, hop_sec: float):
    notes = []
    with open(label_csv) as f:
        for r in csv.DictReader(f):
            try:
                if int(r["instrument"]) != VIOLIN_PROGRAM:
                    continue
                on = float(r["start_time"]) / MUSICNET_NATIVE_SR
                off = float(r["end_time"]) / MUSICNET_NATIVE_SR
                m = float(r["note"])
            except (KeyError, ValueError):
                continue
            if off > on and m > 0:
                notes.append((on, off, m))
    notes.sort()
    return _piecewise_f0_from_notes(notes, n_frames, hop_sec)


def gt_f0_bach10(mat_path: Path, n_frames: int, hop_sec: float):
    gt_midi = scipy.io.loadmat(str(mat_path))["GTF0s"][0]   # violin row, per-10ms MIDI
    true_hz = np.zeros(n_frames, dtype=np.float32)
    voiced = np.zeros(n_frames, dtype=bool)
    for i in range(n_frames):
        gt_i = min(int(round((i * hop_sec) / BACH10_GT_HOP_SEC)), len(gt_midi) - 1)
        m = float(gt_midi[gt_i])
        if m > 0:
            true_hz[i] = float(librosa.midi_to_hz(m))
            voiced[i] = True
    return true_hz, voiced


def load_model(checkpoint: Optional[Path], device: str):
    model = torchcrepe.Crepe("full")
    if checkpoint is None:
        weights = os.path.join(os.path.dirname(torchcrepe.__file__), "assets", "full.pth")
        sd = torch.load(weights, map_location=device, weights_only=True)
    else:
        sd = torch.load(str(checkpoint), map_location=device, weights_only=True)
    model.load_state_dict(sd)
    return model.to(device).eval()


def predict_f0(model, audio: np.ndarray, device: str):
    torchcrepe.infer.model = model
    torchcrepe.infer.capacity = "full"
    audio_t = torch.from_numpy(audio).float().unsqueeze(0).to(device)
    last_err = None
    for bs in (512, 128, 32, 8):
        try:
            pitch, periodicity = torchcrepe.predict(
                audio_t, sample_rate=SAMPLE_RATE, hop_length=HOP_LENGTH,
                fmin=FMIN, fmax=FMAX, model="full",
                decoder=torchcrepe.decode.weighted_argmax,
                return_periodicity=True, device=device, batch_size=bs,
            )
            periodicity = torchcrepe.filter.median(periodicity, 3)
            pitch = torchcrepe.filter.mean(pitch, 3)
            return pitch.squeeze(0).cpu().numpy(), periodicity.squeeze(0).cpu().numpy()
        except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
            if "out of memory" not in str(e).lower() and "cuda" not in str(e).lower():
                raise
            last_err = e; torch.cuda.empty_cache()
    raise last_err  # type: ignore[misc]


def evaluate_recording(audio_path: Path, ann_path: Path, dataset: str,
                       model, device: str) -> dict | None:
    audio, _ = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
    if audio.size == 0:
        return None
    pred_hz, conf = predict_f0(model, audio, device)
    n = len(pred_hz); hop_sec = HOP_LENGTH / SAMPLE_RATE

    if dataset == "MOSA":
        true_hz, voiced_gt = gt_f0_mosa(ann_path, n, hop_sec)
    elif dataset == "MusicNet":
        true_hz, voiced_gt = gt_f0_musicnet(ann_path, n, hop_sec)
    elif dataset == "Bach10":
        true_hz, voiced_gt = gt_f0_bach10(ann_path, n, hop_sec)
    else:
        return None

    voiced = voiced_gt & (conf >= CONF_THRESHOLD) & np.isfinite(pred_hz) & (pred_hz > 0)
    n_used = int(voiced.sum())
    if n_used == 0:
        return None
    return {
        "rpa": float(raw_pitch_accuracy(pred_hz, true_hz, voiced)),
        "rca": float(raw_chroma_accuracy(pred_hz, true_hz, voiced)),
        "mae": float(pitch_mae_cents(pred_hz, true_hz, voiced)),
        "frames_used": n_used,
    }


def load_test_rows(manifest_path: Path):
    test_rows = []
    with open(manifest_path) as f:
        for r in csv.DictReader(f):
            if r["role"] == "test":
                test_rows.append(r)
    return test_rows


def add_bach10(rows, bach10_root: Path):
    if not bach10_root.exists():
        return 0
    n = 0
    for piece_dir in sorted(bach10_root.iterdir()):
        if not piece_dir.is_dir() or not piece_dir.name[:2].isdigit():
            continue
        wav = piece_dir / f"{piece_dir.name}-violin.wav"
        mat = piece_dir / f"{piece_dir.name}-GTF0s.mat"
        if wav.exists() and mat.exists():
            rows.append({"dataset": "Bach10", "filepath": str(wav),
                         "annotation_path": str(mat)})
            n += 1
    return n


def aggregate_per_dataset(per_recording):
    out = {}
    for d in ("MOSA", "MusicNet", "Bach10"):
        recs = [r for r in per_recording if r["dataset"] == d]
        if not recs:
            continue
        rpas = [r["rpa"] for r in recs if not np.isnan(r["rpa"])]
        rcas = [r["rca"] for r in recs if not np.isnan(r["rca"])]
        maes = [r["mae"] for r in recs if not np.isnan(r["mae"])]
        nfr  = sum(r["frames_used"] for r in recs)
        out[d] = {
            "RPA": float(np.mean(rpas)) if rpas else None,
            "RCA": float(np.mean(rcas)) if rcas else None,
            "MAE_cents": float(np.mean(maes)) if maes else None,
            "n_frames": int(nfr),
            "n_recordings": len(recs),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--bach10-root", type=Path, default=None)
    ap.add_argument("--mode", choices=["pretrained", "finetuned"], required=True)
    ap.add_argument("--checkpoint", type=Path, default=None,
                    help="required when --mode finetuned")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--limit", type=int, default=0, help="limit recordings per dataset (debug)")
    args = ap.parse_args()

    if args.mode == "finetuned" and (args.checkpoint is None or not args.checkpoint.exists()):
        raise SystemExit("--mode finetuned requires --checkpoint pointing at a valid .pt file")

    device = args.device if torch.cuda.is_available() else "cpu"
    print(f"[eval] mode={args.mode}  device={device}")

    rows = load_test_rows(args.manifest)
    if args.bach10_root:
        n_b = add_bach10(rows, args.bach10_root)
        print(f"[eval] added {n_b} Bach10 pieces")

    # Rename MOSA/MusicNet "dataset" stays the same - they are mapped to the test sets per spec.
    if args.limit > 0:
        by_ds = {}
        for r in rows:
            by_ds.setdefault(r["dataset"], []).append(r)
        rows = [r for ds in by_ds.values() for r in ds[:args.limit]]
        print(f"[eval] limited to {args.limit} per dataset  {len(rows)} total")

    print(f"[eval] {len(rows)} recordings: " + ", ".join(
        f"{d}={sum(1 for r in rows if r['dataset']==d)}"
        for d in ("MOSA", "MusicNet", "Bach10")))

    ckpt = args.checkpoint if args.mode == "finetuned" else None
    model = load_model(ckpt, device)

    per_recording = []
    for i, r in enumerate(rows, 1):
        try:
            m = evaluate_recording(Path(r["filepath"]), Path(r["annotation_path"]),
                                   r["dataset"], model, device)
        except Exception as e:
            print(f"  [{i:3d}/{len(rows)}] {r['dataset']:10s} {Path(r['filepath']).name:30s} ! {type(e).__name__}: {e}")
            continue
        if m is None:
            continue
        m["dataset"] = r["dataset"]
        m["file"] = Path(r["filepath"]).name
        per_recording.append(m)
        if i % 10 == 0 or i == len(rows):
            print(f"  [{i:3d}/{len(rows)}] {r['dataset']:10s} {m['file']:30s} "
                  f"RPA={m['rpa']:.3f} RCA={m['rca']:.3f} MAE={m['mae']:5.1f}c")

    agg = aggregate_per_dataset(per_recording)
    test_sets_block = {}
    for name_in, name_out in (("MOSA","MOSA_test"), ("MusicNet","MusicNet_test"), ("Bach10","Bach10")):
        if name_in in agg:
            test_sets_block[name_out] = agg[name_in]
    test_sets_block["URMP"] = None  # skipped by user decision

    model_label = "crepe-full pretrained" if args.mode == "pretrained" else f"crepe-full finetuned ({args.checkpoint.name})"
    blob = {
        "model": model_label,
        "test_sets": test_sets_block,
        "preprocessing": {"sr": SAMPLE_RATE, "hop_ms": int(1000 * HOP_LENGTH / SAMPLE_RATE),
                          "voicing_threshold": CONF_THRESHOLD},
        "ran_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / (
        "baseline_metrics.json" if args.mode == "pretrained" else "finetuned_metrics.json"
    )
    out_md = out_json.with_suffix(".md")
    with open(out_json, "w") as f:
        json.dump(blob, f, indent=2)

    md_lines = [
        f"# {model_label}\n",
        f"Ran: {blob['ran_at']}",
        f"Preprocessing: 16 kHz mono, hop 10 ms, voicing threshold {CONF_THRESHOLD}",
        "",
        "| Test set        | n_rec |  RPA  |  RCA  | MAE_cents | n_frames |",
        "|-----------------|------:|------:|------:|----------:|---------:|",
    ]
    for k, v in test_sets_block.items():
        if v is None:
            md_lines.append(f"| {k:15s} |     - |   N/A |   N/A |       N/A |        - |")
        else:
            md_lines.append(
                f"| {k:15s} | {v['n_recordings']:5d} | {v['RPA']:.3f} | {v['RCA']:.3f} | {v['MAE_cents']:9.1f} | {v['n_frames']:8d} |"
            )
    with open(out_md, "w") as f:
        f.write("\n".join(md_lines) + "\n")

    # per-recording detail csv
    detail = out_json.with_name(out_json.stem + "_detail.csv")
    with open(detail, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dataset","file","rpa","rca","mae","frames_used"])
        w.writeheader()
        for r in per_recording: w.writerow(r)

    print(f"\n[eval] wrote {out_json}")
    print(f"        {out_md}")
    print(f"        {detail}")


if __name__ == "__main__":
    main()
