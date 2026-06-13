"""Fine-tune torchcrepe (full) per finetune_and_report_spec.md Section 3.

Differences from the prior backend/training/finetune_crepe.py:
  * CSV step + epoch logging (training_log.csv, training_log_epoch.csv).
  * Spec checkpoint policy: best.pt, last.pt, epoch_NN.pt every 5 epochs.
  * AdamW optimizer, cosine LR schedule with linear warmup.
  * Hard wall-clock budget (--time-budget-hours).
  * Recording-level val split restricted to MOSA recordings (filenames not starting
    with "mn_"). All MusicNet solo-violin recordings stay in train.
  * Val metrics include RPA, RCA, MAE_cents - early stopping driven by val RPA.

Loss: per-bin binary cross-entropy on the 360-bin Gaussian-smoothed target.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import torchcrepe
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from training.dataset import CrepeFrameDataset, CREPE_BINS, _CENTS_MAPPING

VAL_RPA_TOL_CENTS = 50.0


def cosine_lr(step: int, max_steps: int, warmup_steps: int, base_lr: float) -> float:
    if step < warmup_steps:
        return base_lr * (step + 1) / warmup_steps
    p = (step - warmup_steps) / max(1, max_steps - warmup_steps)
    return base_lr * 0.5 * (1.0 + math.cos(math.pi * min(1.0, p)))


def bin_to_cents(probs: torch.Tensor, cmap: torch.Tensor) -> torch.Tensor:
    return (probs * cmap).sum(1) / probs.sum(1).clamp_min(1e-8)


def evaluate(model, val_dl, device, cmap):
    model.eval()
    losses = []
    pred_c, true_c = [], []
    with torch.no_grad():
        for frames, targets in val_dl:
            frames = frames.to(device); targets = targets.to(device)
            probs = model(frames, embed=False)
            eps = 1e-7
            probs_c = probs.clamp(eps, 1 - eps)
            loss = -(targets * probs_c.log() + (1 - targets) * (1 - probs_c).log()).mean()
            losses.append(loss.item())
            voiced = targets.sum(dim=1) > 0
            if voiced.any():
                pred_c.append(bin_to_cents(probs[voiced], cmap))
                true_c.append(bin_to_cents(targets[voiced], cmap))
    val_loss = float(np.mean(losses)) if losses else float("nan")
    if pred_c:
        pred_c = torch.cat(pred_c); true_c = torch.cat(true_c)
        diff = (pred_c - true_c).abs()
        rpa = float((diff <= VAL_RPA_TOL_CENTS).float().mean().item())
        chroma_diff = ((diff + 600.0) % 1200.0) - 600.0
        rca = float((chroma_diff.abs() <= VAL_RPA_TOL_CENTS).float().mean().item())
        mae = float(diff.mean().item())
    else:
        rpa = rca = mae = float("nan")
    return val_loss, rpa, rca, mae


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path, help="combined train-only prepared dir (audio/ + notes/)")
    ap.add_argument("--out", required=True, type=Path, help="output dir for logs + checkpoints/")
    ap.add_argument("--model-size", default="full")
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--max-epochs", type=int, default=30)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--weight-decay", type=float, default=1e-5)
    ap.add_argument("--warmup-steps", type=int, default=1000)
    ap.add_argument("--val-frac", type=float, default=0.15, help="MOSA recordings held for val")
    ap.add_argument("--hop-ms", type=float, default=10.0)
    ap.add_argument("--validate-every", type=int, default=500)
    ap.add_argument("--ckpt-every", type=int, default=2000)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--time-budget-hours", type=float, default=12.0)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "checkpoints").mkdir(exist_ok=True)
    log_step_path = args.out / "training_log.csv"
    log_epoch_path = args.out / "training_log_epoch.csv"

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    device = args.device if torch.cuda.is_available() else "cpu"
    print(f"[finetune] device={device}  model={args.model_size}  lr={args.lr}  bs={args.batch_size}  budget={args.time_budget_hours}h")

    # ---- dataset
    ds = CrepeFrameDataset(args.data, hop_ms=args.hop_ms, seed=args.seed)
    if len(ds) == 0:
        raise SystemExit(f"no frames found under {args.data}")

    # MOSA val split (recording-level)
    mosa_recs = sorted({p for (p, _, _) in ds._index if not p.name.startswith("mn_")})
    mn_recs   = sorted({p for (p, _, _) in ds._index if p.name.startswith("mn_")})
    rng = random.Random(args.seed)
    shuffled = mosa_recs.copy(); rng.shuffle(shuffled)
    n_val = max(1, int(len(shuffled) * args.val_frac))
    val_recs = set(shuffled[:n_val])
    print(f"[finetune] MOSA: {len(mosa_recs)} recordings   val={n_val}, train={len(mosa_recs)-n_val}")
    print(f"[finetune] MusicNet solo-violin: {len(mn_recs)} (all train)")

    train_idx = [i for i, (p, _, _) in enumerate(ds._index) if p not in val_recs]
    val_idx   = [i for i, (p, _, _) in enumerate(ds._index) if p in val_recs]
    print(f"[finetune] {len(train_idx)} train frames / {len(val_idx)} val frames")

    train_dl = DataLoader(Subset(ds, train_idx), batch_size=args.batch_size,
                          shuffle=True, num_workers=args.num_workers, pin_memory=(device != "cpu"),
                          persistent_workers=(args.num_workers > 0))
    val_dl   = DataLoader(Subset(ds, val_idx), batch_size=args.batch_size,
                          shuffle=False, num_workers=args.num_workers, pin_memory=(device != "cpu"),
                          persistent_workers=(args.num_workers > 0))

    # ---- model
    import os
    model = torchcrepe.Crepe(args.model_size)
    w = os.path.join(os.path.dirname(torchcrepe.__file__), "assets", f"{args.model_size}.pth")
    model.load_state_dict(torch.load(w, map_location=device, weights_only=True))
    model.to(device)

    cmap = torch.as_tensor(_CENTS_MAPPING, device=device, dtype=torch.float32)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    steps_per_epoch = max(1, len(train_dl))
    max_steps = steps_per_epoch * args.max_epochs

    # ---- logging files
    with open(log_step_path, "w", newline="") as f:
        csv.writer(f).writerow(["step", "epoch", "split", "loss", "RPA", "RCA", "MAE_cents", "learning_rate", "wall_time_sec"])
    with open(log_epoch_path, "w", newline="") as f:
        csv.writer(f).writerow(["epoch", "train_loss", "val_loss", "val_RPA", "val_RCA", "val_MAE_cents", "lr_end", "wall_time_sec"])

    def append_step(step, epoch, split, loss, rpa, rca, mae, lr, t):
        with open(log_step_path, "a", newline="") as fh:
            csv.writer(fh).writerow([step, epoch, split, f"{loss:.6f}", f"{rpa:.4f}", f"{rca:.4f}", f"{mae:.2f}", f"{lr:.2e}", f"{t:.1f}"])

    def append_epoch(epoch, tr_loss, va_loss, va_rpa, va_rca, va_mae, lr, t):
        with open(log_epoch_path, "a", newline="") as fh:
            csv.writer(fh).writerow([epoch, f"{tr_loss:.6f}", f"{va_loss:.6f}", f"{va_rpa:.4f}", f"{va_rca:.4f}", f"{va_mae:.2f}", f"{lr:.2e}", f"{t:.1f}"])

    # ---- train
    t0 = time.time()
    deadline = t0 + args.time_budget_hours * 3600.0
    best_rpa = -1.0
    best_epoch = -1
    bad_epochs = 0
    final_epoch = 0
    stop_reason = "unknown"
    global_step = 0
    peak_vram_mb = 0
    eps = 1e-7

    for epoch in range(1, args.max_epochs + 1):
        final_epoch = epoch
        model.train()
        tr_loss_sum = 0.0; tr_n = 0
        roll_loss = []; roll_rpa = []; roll_rca = []; roll_mae = []

        for batch_i, (frames, targets) in enumerate(train_dl):
            global_step += 1
            lr = cosine_lr(global_step, max_steps, args.warmup_steps, args.lr)
            for g in opt.param_groups: g["lr"] = lr

            frames = frames.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            probs = model(frames, embed=False)
            probs_c = probs.clamp(eps, 1 - eps)
            loss = -(targets * probs_c.log() + (1 - targets) * (1 - probs_c).log()).mean()

            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()

            tr_loss_sum += loss.item(); tr_n += 1
            with torch.no_grad():
                voiced = targets.sum(dim=1) > 0
                if voiced.any():
                    pc = bin_to_cents(probs[voiced], cmap).detach()
                    tc = bin_to_cents(targets[voiced], cmap)
                    diff = (pc - tc).abs()
                    roll_loss.append(loss.item())
                    roll_rpa.append(float((diff <= VAL_RPA_TOL_CENTS).float().mean()))
                    chroma_diff = ((diff + 600.0) % 1200.0) - 600.0
                    roll_rca.append(float((chroma_diff.abs() <= VAL_RPA_TOL_CENTS).float().mean()))
                    roll_mae.append(float(diff.mean()))

            if torch.cuda.is_available():
                peak_vram_mb = max(peak_vram_mb, torch.cuda.max_memory_allocated(device) / 1024**2)

            if global_step % 100 == 0:
                t_now = time.time() - t0
                rl = np.mean(roll_loss[-100:]) if roll_loss else float("nan")
                rp = np.mean(roll_rpa[-100:]) if roll_rpa else float("nan")
                rc = np.mean(roll_rca[-100:]) if roll_rca else float("nan")
                rm = np.mean(roll_mae[-100:]) if roll_mae else float("nan")
                append_step(global_step, epoch, "train", rl, rp, rc, rm, lr, t_now)
                print(f"  step {global_step:6d} ep {epoch:2d} batch {batch_i:5d}/{steps_per_epoch}  "
                      f"loss={rl:.4f} RPA={rp:.3f} MAE={rm:5.1f}c lr={lr:.2e} t={t_now:.0f}s")

            if global_step % args.validate_every == 0:
                va_loss, va_rpa, va_rca, va_mae = evaluate(model, val_dl, device, cmap)
                t_now = time.time() - t0
                append_step(global_step, epoch, "val", va_loss, va_rpa, va_rca, va_mae, lr, t_now)
                print(f"  -- val @ step {global_step}: loss={va_loss:.4f} RPA={va_rpa:.3f} RCA={va_rca:.3f} MAE={va_mae:5.1f}c")
                if va_rpa > best_rpa:
                    best_rpa = va_rpa; best_epoch = epoch
                    torch.save(model.state_dict(), args.out / "checkpoints" / "best.pt")
                model.train()

            if global_step % args.ckpt_every == 0:
                torch.save(model.state_dict(), args.out / "checkpoints" / "last.pt")

            if time.time() >= deadline:
                stop_reason = "time_budget"
                torch.save(model.state_dict(), args.out / "checkpoints" / "last.pt")
                torch.save(model.state_dict(), args.out / "checkpoints" / "final.pt")
                break

        if stop_reason == "time_budget":
            break

        # end of epoch: validate + record
        va_loss, va_rpa, va_rca, va_mae = evaluate(model, val_dl, device, cmap)
        tr_loss = tr_loss_sum / max(tr_n, 1)
        t_now = time.time() - t0
        append_epoch(epoch, tr_loss, va_loss, va_rpa, va_rca, va_mae, lr, t_now)
        print(f"epoch {epoch:2d} done  train_loss={tr_loss:.4f}  "
              f"val_loss={va_loss:.4f} val_RPA={va_rpa:.3f} val_MAE={va_mae:.1f}c  "
              f"wall={t_now/60:.1f}min")

        # checkpoint policy
        torch.save(model.state_dict(), args.out / "checkpoints" / "last.pt")
        if epoch % 5 == 0:
            torch.save(model.state_dict(), args.out / "checkpoints" / f"epoch_{epoch:02d}.pt")
        if va_rpa > best_rpa:
            best_rpa = va_rpa; best_epoch = epoch
            torch.save(model.state_dict(), args.out / "checkpoints" / "best.pt")
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                stop_reason = "early_stopping"
                break

    if stop_reason == "unknown":
        stop_reason = "max_epochs"

    # Save final summary
    summary = {
        "total_epochs": final_epoch,
        "best_epoch": best_epoch,
        "best_val_rpa": best_rpa,
        "stop_reason": stop_reason,
        "wall_clock_sec": time.time() - t0,
        "peak_vram_mb": peak_vram_mb,
        "config": vars(args),
    }
    import json
    summary_path = args.out / "training_summary.json"
    def jdef(o):
        if isinstance(o, Path): return str(o)
        return str(o)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=jdef)
    print(f"[finetune] DONE. {summary}")


if __name__ == "__main__":
    main()
