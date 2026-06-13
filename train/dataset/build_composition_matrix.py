from __future__ import annotations

import argparse
import csv
import random
import tarfile
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import soundfile as sf

N_SETS = 10
TEST_SET = N_SETS
SEED = 42


@dataclass
class ManifestRow:
    dataset: str
    filepath: str
    set_id: int
    role: str
    duration_sec: float
    piece_id: str
    performer_id: str
    annotation_path: str


def _wav_duration(path: Path) -> float:
    info = sf.info(str(path))
    return float(info.frames) / float(info.samplerate)


def scan_mosa(root: Path) -> tuple[list[dict], list[tuple[str, str]]]:
    audio_dir = root / "audio"
    notes_dir = root / "notes"
    kept: list[dict] = []
    excluded: list[tuple[str, str]] = []

    if not audio_dir.exists():
        return kept, [("<root>", f"audio dir not found: {audio_dir}")]

    for wav in sorted(audio_dir.glob("*.wav")):
        stem = wav.stem
        ann = notes_dir / f"{stem}.csv"
        if not ann.exists():
            excluded.append((str(wav), "missing note CSV (no F0 ground truth)"))
            continue

        parts = stem.split("_")
        if len(parts) >= 2:
            performer_id = parts[0]
            piece_id = "_".join(parts[:2])
        else:
            performer_id = ""
            piece_id = stem

        try:
            dur = _wav_duration(wav)
        except Exception as e:
            excluded.append((str(wav), f"duration probe failed: {e}"))
            continue

        kept.append({
            "dataset": "MOSA",
            "filepath": str(wav.resolve()),
            "duration_sec": round(dur, 2),
            "piece_id": piece_id,
            "performer_id": performer_id,
            "annotation_path": str(ann.resolve()),
            "_group": piece_id,
        })
    return kept, excluded


def _extract_musicnet_if_needed(root: Path) -> Path:
    tarball = root / "musicnet.tar.gz"
    expected = root / "musicnet"
    if expected.exists() and any(expected.iterdir()):
        return expected
    if not tarball.exists():
        return root
    print(f"  [musicnet] extracting {tarball.name}  {expected} …")
    with tarfile.open(tarball, "r:gz") as tf:
        tf.extractall(root)
    return expected


def _musicnet_label_uses_violin(label_csv: Path, program_violin: int = 41) -> bool:
    try:
        with open(label_csv) as f:
            r = csv.DictReader(f)
            for row in r:
                inst = row.get("instrument")
                if inst is None:
                    continue
                try:
                    if int(inst) == program_violin:
                        return True
                except ValueError:
                    continue
    except Exception:
        return False
    return False


def scan_musicnet(root: Path) -> tuple[list[dict], list[tuple[str, str]]]:
    kept: list[dict] = []
    excluded: list[tuple[str, str]] = []
    meta_path = root / "musicnet_metadata.csv"
    if not meta_path.exists():
        return kept, [("<root>", f"musicnet_metadata.csv not found at {meta_path}")]

    base = _extract_musicnet_if_needed(root)
    if not (base / "train_data").exists() and not (base / "test_data").exists():
        return kept, [("<root>", f"MusicNet not extracted under {base}; need musicnet.tar.gz")]

    meta_by_id: dict[str, dict] = {}
    with open(meta_path) as f:
        for row in csv.DictReader(f):
            meta_by_id[row["id"]] = row

    for subdir in ("train_data", "test_data"):
        audio_dir = base / subdir
        label_dir = base / subdir.replace("_data", "_labels")
        if not audio_dir.exists():
            continue
        for wav in sorted(audio_dir.glob("*.wav")):
            rec_id = wav.stem
            label = label_dir / f"{rec_id}.csv"
            if not label.exists():
                excluded.append((str(wav), "missing label CSV"))
                continue
            if not _musicnet_label_uses_violin(label):
                excluded.append((str(wav), "no violin (program 41) rows"))
                continue
            try:
                dur = _wav_duration(wav)
            except Exception as e:
                excluded.append((str(wav), f"duration probe failed: {e}"))
                continue

            m = meta_by_id.get(rec_id, {})
            composer = m.get("composer", "")
            composition = m.get("composition", "")
            piece_id = f"{composer}::{composition}".strip(":")
            performer_id = m.get("ensemble", "")

            kept.append({
                "dataset": "MusicNet",
                "filepath": str(wav.resolve()),
                "duration_sec": round(dur, 2),
                "piece_id": piece_id or rec_id,
                "performer_id": performer_id,
                "annotation_path": str(label.resolve()),
                "_group": piece_id or rec_id,
            })
    return kept, excluded


def split_into_sets(records: list[dict], n_sets: int = N_SETS,
                    seed: int = SEED) -> list[int]:
    rng = random.Random(seed)

    by_group: dict[str, list[int]] = defaultdict(list)
    for i, rec in enumerate(records):
        by_group[rec["_group"]].append(i)

    def group_dur(g: str) -> float:
        return sum(records[i]["duration_sec"] for i in by_group[g])

    groups_sorted = sorted(by_group.keys(), key=lambda g: (-group_dur(g), rng.random()))
    set_totals = [0.0] * n_sets
    set_of = [0] * len(records)

    total = sum(group_dur(g) for g in groups_sorted)
    target_test = total / n_sets
    test_dur = 0.0
    test_groups: set[str] = set()
    candidates = list(groups_sorted)
    rng.shuffle(candidates)
    for g in candidates:
        if test_dur >= target_test and test_groups:
            break
        test_groups.add(g)
        test_dur += group_dur(g)
    if len(test_groups) == len(groups_sorted) and len(groups_sorted) > 1:
        biggest = max(test_groups, key=group_dur)
        test_groups.discard(biggest)
        test_dur -= group_dur(biggest)

    for g in test_groups:
        for i in by_group[g]:
            set_of[i] = n_sets
        set_totals[n_sets - 1] += group_dur(g)

    remaining = [g for g in groups_sorted if g not in test_groups]
    for g in remaining:
        s = min(range(n_sets - 1), key=lambda k: (set_totals[k], rng.random()))
        for i in by_group[g]:
            set_of[i] = s + 1
        set_totals[s] += group_dur(g)

    return set_of


def write_manifest(rows: list[ManifestRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "dataset", "filepath", "set_id", "role",
            "duration_sec", "piece_id", "performer_id", "annotation_path",
        ])
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def write_set_stats(rows: list[ManifestRow], path: Path) -> None:
    by: dict[tuple[str, int], tuple[int, float]] = defaultdict(lambda: (0, 0.0))
    datasets: list[str] = []
    for r in rows:
        key = (r.dataset, r.set_id)
        n, d = by[key]
        by[key] = (n + 1, d + r.duration_sec)
        if r.dataset not in datasets:
            datasets.append(r.dataset)

    header = "| Dataset    | " + " | ".join(f"set_{s}" for s in range(1, N_SETS + 1)) + " |"
    divider = "|------------|" + "|".join(["-------"] * N_SETS) + "|"
    out = ["# Set statistics (files / minutes per cell)", "", header, divider]
    for ds in datasets:
        cells = []
        for s in range(1, N_SETS + 1):
            n, d = by.get((ds, s), (0, 0.0))
            if n == 0:
                cells.append("-")
            else:
                cells.append(f"{n} files / {d/60.0:.1f} min")
        out.append(f"| {ds:<10} | " + " | ".join(cells) + " |")
    path.write_text("\n".join(out) + "\n")


def write_matrix(rows: list[ManifestRow], path: Path) -> None:
    datasets: list[str] = []
    for r in rows:
        if r.dataset not in datasets:
            datasets.append(r.dataset)
    header = "| Dataset    | " + " | ".join(f"set_{s}" for s in range(1, N_SETS + 1)) + " |"
    divider = "|------------|" + "|".join(["-------"] * N_SETS) + "|"
    out = ["# Training composition matrix", "", header, divider]
    for ds in datasets:
        cells = [("TRAIN" if s < TEST_SET else "TEST") for s in range(1, N_SETS + 1)]
        out.append(f"| {ds:<10} | " + " | ".join(cells) + " |")
    path.write_text("\n".join(out) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mosa-root", type=Path, required=True)
    ap.add_argument("--musicnet-root", type=Path, default=None,
                    help="If absent / not downloaded yet, MusicNet rows are skipped.")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    all_rows: list[ManifestRow] = []
    all_excluded: list[tuple[str, str, str]] = []

    print("=== Scanning MOSA ===")
    mosa_kept, mosa_excl = scan_mosa(args.mosa_root)
    print(f"  MOSA: kept {len(mosa_kept)} / {len(mosa_kept) + len(mosa_excl)} files")
    if mosa_kept:
        set_ids = split_into_sets(mosa_kept, seed=args.seed)
        for rec, sid in zip(mosa_kept, set_ids):
            all_rows.append(ManifestRow(
                dataset=rec["dataset"], filepath=rec["filepath"],
                set_id=sid, role=("test" if sid == TEST_SET else "train"),
                duration_sec=rec["duration_sec"],
                piece_id=rec["piece_id"], performer_id=rec["performer_id"],
                annotation_path=rec["annotation_path"],
            ))
    all_excluded.extend(("MOSA", f, r) for f, r in mosa_excl)

    if args.musicnet_root and args.musicnet_root.exists():
        print("=== Scanning MusicNet ===")
        mn_kept, mn_excl = scan_musicnet(args.musicnet_root)
        print(f"  MusicNet: kept {len(mn_kept)} / {len(mn_kept) + len(mn_excl)} files")
        if mn_kept:
            set_ids = split_into_sets(mn_kept, seed=args.seed)
            for rec, sid in zip(mn_kept, set_ids):
                all_rows.append(ManifestRow(
                    dataset=rec["dataset"], filepath=rec["filepath"],
                    set_id=sid, role=("test" if sid == TEST_SET else "train"),
                    duration_sec=rec["duration_sec"],
                    piece_id=rec["piece_id"], performer_id=rec["performer_id"],
                    annotation_path=rec["annotation_path"],
                ))
        all_excluded.extend(("MusicNet", f, r) for f, r in mn_excl)
    else:
        print("=== MusicNet: skipped (root not present) ===")

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    write_manifest(all_rows, out / "manifest.csv")
    write_set_stats(all_rows, out / "set_statistics.md")
    write_matrix(all_rows, out / "training_composition_matrix.md")

    excl_log = out / "exclusions.csv"
    with open(excl_log, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["dataset", "file", "reason"])
        for ds, fp, reason in all_excluded:
            w.writerow([ds, fp, reason])

    print("\n=== Summary ===")
    by_ds: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
    for r in all_rows:
        n, d = by_ds[r.dataset]
        by_ds[r.dataset] = (n + 1, d + r.duration_sec)
    for ds, (n, d) in by_ds.items():
        print(f"  {ds:10s}  {n:4d} files  {d/60.0:6.1f} min  ({d:.0f} sec)")
    print(f"  excluded total: {len(all_excluded)}")
    print(f"\nwrote: {out/'manifest.csv'}")
    print(f"       {out/'set_statistics.md'}")
    print(f"       {out/'training_composition_matrix.md'}")
    print(f"       {out/'exclusions.csv'}")

    print("\n=== Sanity checks ===")
    seen = set()
    leakage = False
    for r in all_rows:
        if r.filepath in seen:
            print(f"  LEAKAGE: {r.filepath} appears twice"); leakage = True
        seen.add(r.filepath)
    if not leakage:
        print("   no file appears in more than one set")

    missing_ann = [r for r in all_rows if not Path(r.annotation_path).exists()]
    if missing_ann:
        print(f"   {len(missing_ann)} rows have missing annotation_path")
    else:
        print("   all annotation_path entries exist on disk")

    for ds in by_ds:
        per_set = defaultdict(float)
        for r in all_rows:
            if r.dataset == ds:
                per_set[r.set_id] += r.duration_sec
        nonempty = [(s, d) for s, d in per_set.items() if d > 0]
        if not nonempty:
            continue
        avg = sum(d for _, d in nonempty) / len(nonempty)
        worst = min(per_set.values()), max(per_set.values())
        ratio_lo = worst[0] / avg if avg > 0 else 0
        ratio_hi = worst[1] / avg if avg > 0 else 0
        flag = "" if (ratio_lo >= 0.5 and ratio_hi <= 1.5) or len(nonempty) < N_SETS else ""
        print(f"  {flag} {ds}: per-set total range "
              f"{worst[0]/60:.1f}-{worst[1]/60:.1f} min (avg {avg/60:.1f}) "
              f"across {len(nonempty)} non-empty sets")


if __name__ == "__main__":
    main()
