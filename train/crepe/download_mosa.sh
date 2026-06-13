#!/usr/bin/env bash
# ── MOSA Dataset downloader ────────────────────────────────────────────────
#
# MOSA = "Music mOtion with Semantic Annotation" (NTU, 2024).
# Contains violin + piano performances with aligned audio (.wav), MIDI/note
# annotations, and 3D motion. For CREPE fine-tuning we only need the *violin*
# audio + note (pitch/onset/offset) annotations.
#
# The dataset is distributed on Zenodo. As of writing the record is large
# (~tens of GB) so this script downloads it into ./datasets/MOSA and unpacks
# only the violin subset.
#
# USAGE:
# 1. Find the current Zenodo record URL for "MOSA dataset":
# https://zenodo.org/   search "MOSA Music mOtion Semantic Annotation"
# (the authors also link it from the paper's GitHub repo).
# 2. Put the record's files API URL in MOSA_ZENODO_URL below, or pass it:
# MOSA_ZENODO_URL="https://zenodo.org/api/records/<ID>" ./download_mosa.sh
# 3. Run this script from the repo root.
#
# Everything lands in:  <repo>/datasets/MOSA/
# ├── raw/                # downloaded archives
# ├── violin/audio/*.wav  # 16 kHz mono (resampled here)
# └── violin/notes/*.csv  # onset_sec, offset_sec, midi  (one row per note)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$REPO_ROOT/datasets/MOSA"
RAW="$DEST/raw"
mkdir -p "$RAW" "$DEST/violin/audio" "$DEST/violin/notes"

MOSA_ZENODO_URL="${MOSA_ZENODO_URL:-}"   # <-- fill in or pass via env

if [[ -z "$MOSA_ZENODO_URL" ]]; then
  cat <<'EOF'
[!] MOSA_ZENODO_URL is not set.

    The MOSA dataset URL changes per release, so this script does not hard-code
    it. Steps:

      1. Open https://zenodo.org and search:  MOSA Music mOtion Semantic Annotation
         (or follow the dataset link from the MOSA paper's GitHub page).
      2. Copy the record's API URL, e.g.  https://zenodo.org/api/records/1234567
      3. Re-run:
           MOSA_ZENODO_URL="https://zenodo.org/api/records/1234567" \
             backend/training/download_mosa.sh

    If you already have the archives, drop them in:
           datasets/MOSA/raw/
    and re-run - the script will skip the download and just unpack.
EOF
  # Continue to the unpack step in case archives are already present.
fi

# ── 1. Download (if a URL was provided) ────────────────────────────────────
if [[ -n "$MOSA_ZENODO_URL" ]]; then
  echo ">> Querying Zenodo record metadata..."
  META="$RAW/_record.json"
  curl -sSL "$MOSA_ZENODO_URL" -o "$META"
  # Pull every file download link from the record JSON
  python3 - "$META" <<'PY' > "$RAW/_files.txt"
import json, sys
rec = json.load(open(sys.argv[1]))
for f in rec.get("files", []):
    link = f.get("links", {}).get("self") or f.get("links", {}).get("download")
    if link:
        print(f["key"], link)
PY
  echo ">> Files in record:"; cat "$RAW/_files.txt"
  while read -r name url; do
    [[ -f "$RAW/$name" ]] && { echo "   (have) $name"; continue; }
    echo ">> Downloading $name ..."
    curl -L --fail -o "$RAW/$name" "$url"
  done < "$RAW/_files.txt"
fi

# ── 2. Unpack archives in raw/ ─────────────────────────────────────────────
echo ">> Unpacking archives in $RAW ..."
shopt -s nullglob
for a in "$RAW"/*.zip;     do echo "   unzip $a";    unzip -n -q "$a"     -d "$DEST/_unpacked";        done
for a in "$RAW"/*.tar.gz;  do echo "   tar   $a";    tar  -xzf  "$a"      -C "$DEST/_unpacked";        done
for a in "$RAW"/*.tar;     do echo "   tar   $a";    tar  -xf   "$a"      -C "$DEST/_unpacked";        done

cat <<EOF

>> Done. Now run the preprocessing step to build the training set:

     backend/venv/bin/python backend/training/dataset.py \\
         --mosa-root datasets/MOSA \\
         --out datasets/MOSA/violin

   That walks the unpacked tree, keeps the violin recordings, resamples audio
   to 16 kHz mono into  datasets/MOSA/violin/audio/, and writes per-recording
   note CSVs (onset_sec, offset_sec, midi) into  datasets/MOSA/violin/notes/.
EOF
