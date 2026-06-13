"""Build a combined train-only prepared dir by symlinking:
  - All MOSA training recordings (role=train per manifest) from MOSA_full/violin/
  - All 9 MusicNet solo-violin recordings (already prepared)

Excludes role=test recordings (set_10) so they never leak into training.
Output layout: <out>/audio/*.wav + <out>/notes/*.csv

MusicNet files keep their "mn_" prefix so the trainer can identify them and
keep them all in train (not val), since we only have 9 of them.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 4:
        print("usage: build_train_prepared.py <manifest.csv> <musicnet_prepared> <out>", file=sys.stderr)
        sys.exit(2)
    manifest = Path(sys.argv[1])
    mn_prep = Path(sys.argv[2])
    out = Path(sys.argv[3])

    audio_out = out / "audio"; audio_out.mkdir(parents=True, exist_ok=True)
    notes_out = out / "notes"; notes_out.mkdir(parents=True, exist_ok=True)

    # 1) MOSA train rows from manifest
    n_mosa = 0
    with open(manifest) as f:
        for r in csv.DictReader(f):
            if r["dataset"] != "MOSA" or r["role"] != "train":
                continue
            wav = Path(r["filepath"]).resolve()
            ann = Path(r["annotation_path"]).resolve()
            dest_wav = audio_out / wav.name
            dest_ann = notes_out / ann.name
            if dest_wav.exists() or dest_wav.is_symlink(): dest_wav.unlink()
            if dest_ann.exists() or dest_ann.is_symlink(): dest_ann.unlink()
            dest_wav.symlink_to(wav)
            dest_ann.symlink_to(ann)
            n_mosa += 1

    # 2) MusicNet solo-violin (all 9 - none of these are in our test set_10)
    n_mn = 0
    for wav in sorted((mn_prep / "audio").glob("*.wav")):
        ann = mn_prep / "notes" / f"{wav.stem}.csv"
        if not ann.exists():
            continue
        dest_wav = audio_out / wav.name
        dest_ann = notes_out / ann.name
        if dest_wav.exists() or dest_wav.is_symlink(): dest_wav.unlink()
        if dest_ann.exists() or dest_ann.is_symlink(): dest_ann.unlink()
        dest_wav.symlink_to(wav.resolve())
        dest_ann.symlink_to(ann.resolve())
        n_mn += 1

    print(f"[build] linked {n_mosa} MOSA + {n_mn} MusicNet solo-violin  {out}")
    print(f"        audio={len(list(audio_out.glob('*.wav')))} notes={len(list(notes_out.glob('*.csv')))}")


if __name__ == "__main__":
    main()
