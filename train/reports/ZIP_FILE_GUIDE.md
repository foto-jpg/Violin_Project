# คู่มืออธิบายไฟล์ใน `violin_pitch_detection_starter.zip`

> สำหรับผู้รับไฟล์ที่ต้อง extract แล้ว plug ใน dataset paths ของตัวเองและรันใหม่
> เขียนเป็นภาษาไทย + เก็บศัพท์เทคนิคต้นฉบับเป็นภาษาอังกฤษ
> Date: 2026-05-26

---

## โครงสร้างทั้งหมด (33 ไฟล์)

```
violin_pitch_detection_starter/
├── README.md                         (43 KB)   Section 1
├── QUICKSTART.md                     (3.6 KB)  Section 2
├── NOTICE.md                         (1.9 KB)  Section 3
├── requirements.txt                  (580 B)   Section 4
├── .gitignore                        (507 B)   Section 5
├── configs/
│   └── finetune_default.yaml         (2.0 KB)  Section 6
├── scripts/                                    Section 7 (8 ไฟล์)
│   ├── download_mosa_zenodo.py       (6.1 KB)
│   ├── prepare_violin.py             (1.1 KB)
│   ├── prepare_musicnet_violin.py    (3.4 KB)
│   ├── build_composition_matrix.py   (13 KB)
│   ├── build_train_prepared.py       (2.4 KB)
│   ├── finetune_crepe.py             (13 KB)
│   ├── evaluate_model.py             (13 KB)
│   └── load_example.py               (3.3 KB)
├── backend/
│   └── training/                               Section 8 (3 ไฟล์)
│       ├── __init__.py               (0 B)
│       ├── dataset.py                (6.7 KB)
│       └── metrics.py                (1.1 KB)
├── checkpoints/
│   └── best.pt                       (85 MB)   Section 9
├── docs/                                       Section 10 (6 ไฟล์)
│   ├── PROJECT_COMPLETE_SUMMARY.md   (43 KB)
│   ├── training_results_report.md    (16 KB)
│   ├── results_baseline.json         (755 B)
│   ├── results_finetuned.json        (759 B)
│   ├── training_summary.json         (1.3 KB)
│   └── training_log_epoch.csv        (313 B)
└── examples/
    └── infer_single_wav.py           (2.4 KB)  Section 11
```

---

## 1. `README.md` - เอกสารหลักของโปรเจ็กต์

**ใช้ทำอะไร**: เป็นสำเนาเต็มของ `PROJECT_COMPLETE_SUMMARY.md` (43 KB, 14 sections, 639 บรรทัด) เพื่อให้คนที่ extract zip มาแล้วเปิดอ่านจากรากของโฟลเดอร์ได้ทันที โดยไม่ต้องเดินเข้า `docs/`

**เนื้อหา 14 sections**:

| Section | หัวเรื่อง | สรุปสั้น ๆ |
|---|---|---|
| 1 | Project Overview | เป็นโปรเจ็กต์อะไร / ทำไมเลือก CREPE / pipeline diagram (OMR  CREPE  scoring) / สถานะปัจจุบัน |
| 2 | Dataset Inventory | ตาราง MOSA / MusicNet / Bach10 / URMP - license, ขนาดหลังกรอง, วิธีได้มา, เหตุผลที่ใช้ |
| 3 | Data Preparation Pipeline | 10 ขั้นย่อย (3.1-3.10): scan  filter violin  annotation check  noteframe  group-id  split  Option B  manifest  stats  matrix |
| 4 | Model Architecture | CREPE-full ≈22 M params / 6 conv blocks  360-bin / input 1024 samples @ 16 kHz / pitch decoder (weighted-mean vs argmax) |
| 5 | Training Configuration | ตารางทุก hyperparameter พร้อมเหตุผล (loss, optimizer, LR, schedule, batch, epochs, seed, voicing threshold, hop, sample rate) |
| 6 | Training Execution & Results | hardware, wall-clock, epochs, best step, peak VRAM, ตาราง per-epoch log |
| 7 | Evaluation Methodology | mir_eval-equivalent metrics / 4 test sets / voicing handling / n_frames variance |
| 8 | Results: Before vs After | ตารางค่าจริงจาก JSON + Δ row + interpretation paragraph |
| 9 | SOTA Comparison | เทียบกับ Tamer 2022 + lars76/pitch-benchmark + discussion เรื่อง real vs synth |
| 10 | Open Issues & Known Limitations | 8 ประเด็นค้าง (val-metric mismatch, MusicNet polyphony, URMP, second-pass, ฯลฯ) |
| 11 | Repository Layout | tree-style listing ของ zip |
| 12 | Reproducibility Recipe | 7 ขั้นรันใหม่ พร้อม command lines |
| 13 | Glossary | นิยาม 18 คำ (CREPE, RPA, RCA, MAE, F0, voicing, vibrato, BCE, AdamW, cosine LR, …) |
| 14 | Citations / References | 10 papers + dataset URLs |

**เมื่อไหร่ต้องอ่าน**: เป็นแหล่งความจริงเดียวสำหรับเข้าใจโปรเจ็กต์ทั้งหมด - อ่านครั้งเดียวก่อนจะรัน

---

## 2. `QUICKSTART.md` - สูตรลัด 7 ขั้น

**ใช้ทำอะไร**: คู่มือคำสั่งล้วน ๆ ไม่มีคำอธิบาย - ใช้เมื่ออ่าน README แล้วและต้องการรันจริง

**7 ขั้น**:

1. **Install** - `pip install -r requirements.txt`
2. **Get datasets** - ตารางลิงก์ MOSA/MusicNet/Bach10/URMP
3. (2a) **Download MOSA** - `download_mosa_zenodo.py` (ต้องตั้ง `$ZENODO_TOKEN`)
4. (2b) **Prepare MOSA violin** - แก้ paths แล้วรัน `prepare_violin.py`
5. **Build composition matrix** - `build_composition_matrix.py`  `manifest.csv`
6. **Filter MusicNet solo-violin** - `prepare_musicnet_violin.py` + `build_train_prepared.py`
7. **Fine-tune** - `finetune_crepe.py`
8. **Evaluate** - `evaluate_model.py --mode pretrained` + `--mode finetuned`
9. **Inference** - `examples/infer_single_wav.py`

**เมื่อไหร่ต้องอ่าน**: ทุกครั้งที่ลืม command line - เปิดไว้ข้าง terminal

---

## 3. `NOTICE.md` - เอกสาร licensing

**ใช้ทำอะไร**: เนื่องจากต้นฉบับไม่มี `LICENSE` ไฟล์ จึงเขียน notice อธิบายข้อจำกัด

**ระบุว่า**:
- โปรเจ็กต์นี้แจกจ่ายแบบ research/educational เท่านั้น (ไม่ใช่ open-source)
- License ของ component แต่ละตัว: torchcrepe (MIT), MOSA (restricted Zenodo), MusicNet (CC BY 4.0), Bach10 (research-only), URMP (research-only)
- `best.pt` เป็น derivative work ของ MOSA  inherit ข้อจำกัดของ MOSA  **ห้ามแจกจ่ายเชิงพาณิชย์**

**เมื่อไหร่ต้องอ่าน**: ก่อนตัดสินใจ redistribute หรือใช้เชิงพาณิชย์

---

## 4. `requirements.txt` - Pinned dependencies

**ใช้ทำอะไร**: รายการ Python packages ที่ต้องลง พร้อม version ที่ทดสอบแล้วว่าเข้ากันได้ (ดึงจาก venv ที่รัน fine-tune จริง)

**Pinned versions**:

| Package | Version | ใช้ทำอะไร |
|---|---|---|
| `torch` | 2.11.0 | Deep learning framework |
| `torchaudio` | 2.11.0 | Audio ops ที่บางสคริปต์อาจ import |
| `torchcrepe` | 0.0.24 | CREPE PyTorch wrapper + bundled weights |
| `librosa` | 0.11.0 | Audio I/O, resampling, MIDIHz conversions |
| `soundfile` | 0.13.1 | WAV reading (faster than librosa.load) |
| `numba` | 0.65.1 | Transitive via librosa (JIT compilation) |
| `numpy` | 2.4.4 | Array math |
| `scipy` | 1.17.1 | อ่าน `Bach10 *.mat` ไฟล์ ใน `evaluate_model.py` |
| `scikit-learn` | 1.8.0 | Transitive via librosa |
| `PyYAML` | 6.0.3 | อ่าน `configs/finetune_default.yaml` |
| `tqdm` | 4.67.3 | Progress bars |

**เมื่อไหร่ต้องแตะ**: ปกติแค่ `pip install -r requirements.txt` แล้วใช้ได้ ถ้าจะเปลี่ยน torch version ให้ระวัง `torchcrepe` compatibility

---

## 5. `.gitignore`

**ใช้ทำอะไร**: ถ้าผู้รับนำโปรเจ็กต์ไปสร้าง git repo ใหม่ ไฟล์นี้จะกัน:
- `__pycache__/`, `*.pyc`
- `.venv/`, `venv/`
- `datasets/`, `*.wav`, `*.mp3`, `*.flac`, `*.mat`, `musicnet*.tar.gz`, `MOSA*.zip*` - กันไฟล์ dataset เด็ดขาด
- `checkpoints/*.pt` **ยกเว้น** `checkpoints/best.pt` (ไฟล์เดียวที่เก็บใน repo)
- `outputs/runs/`, `*.log`, `*.pid`
- `.vscode/`, `.idea/`, `.DS_Store`
- `.env*` (กัน secrets) **ยกเว้น** `.env.example`
- `*token*`, `*TOKEN*` - กัน Zenodo token หลุด

**เมื่อไหร่ต้องแตะ**: ปกติไม่ต้อง - แต่ถ้าจะเปลี่ยนชื่อ `checkpoints/best.pt` อย่าลืมอัพเดต whitelist

---

## 6. `configs/finetune_default.yaml` - Hyperparameter config

**ใช้ทำอะไร**: เก็บค่าทุกตัวจาก Section 5 ของ README ไว้ใน YAML ที่อ่านได้ทั้งคนและเครื่อง

**โครงสร้างหลัก** (7 sections):

```yaml
model:        size, pretrained_checkpoint
optimizer:    AdamW + lr=5e-5 + weight_decay=1e-5
scheduler:    cosine + warmup_steps=1000
training:     batch_size=32, max_epochs=30, patience=5, seed=42,
              validate_every_n_steps=500, checkpoint_every_n_steps=2000,
              time_budget_hours=12
loss:         bce_per_bin + gaussian_smoothed + sigma=25¢
audio:        sample_rate=16000, hop_ms=10, voicing_threshold=0.5
data:         dataset paths (แก้ตรงนี้ได้ถ้า layout ต่างจาก default)
validation:   source=mosa_recording_level, val_frac=0.05
output:       checkpoints_dir, logs_dir
```

**ข้อสังเกตสำคัญ**:
- `validate_every_n_steps: 500` เป็น **spec value** - รอบรันจริงบน RTX 3070 Ti ใช้ 10,000 เพราะ GPU ช้าเกินจะ validate ทุก 500 step
- ผู้ใช้บน GPU ที่แรงกว่า (≥ 1 val pass/min) ควรเก็บ 500 ตามนี้

**เมื่อไหร่ต้องแตะ**:
- เปลี่ยน `data.mosa_root`, `data.musicnet_root`, etc. ให้ตรง layout ของตัวเอง
- ปรับ `training.validate_every_n_steps` / `checkpoint_every_n_steps` ตามความแรงของ GPU
- ตั้ง `data.urmp_root: null` ถ้ายังไม่ได้ URMP

**หมายเหตุ**: `finetune_crepe.py` ปัจจุบันรับ args ผ่าน argparse ไม่ได้อ่าน YAML นี้โดยตรง - เป็นเอกสารกำหนดค่ามาตรฐานสำหรับมนุษย์ + base สำหรับการเขียน wrapper ในอนาคต

---

## 7. `scripts/` - ตัว pipeline ทั้งหมด (8 ไฟล์)

ลำดับการรันใน production pipeline:
```
download_mosa_zenodo    prepare_violin    prepare_musicnet_violin
build_composition_matrix    build_train_prepared    finetune_crepe
evaluate_model
```

`load_example.py` แยกออกมา - ใช้ทดสอบโหลด checkpoint อย่างเดียว ไม่อยู่ใน pipeline

### 7.1 `scripts/download_mosa_zenodo.py` (NEW - ไม่มีในต้นฉบับ)

**ใช้ทำอะไร**: ดาวน์โหลด MOSA dataset จาก Zenodo (restricted-access record 11393449) แบบ 6 parts พร้อม verify MD5 + resume + reassemble + unzip

**Input**: `$ZENODO_TOKEN` environment variable (Zenodo personal access token), `--record-id`, `--out`

**Output**:
- 6 parts ใน `<out>/MOSA_dataset.zip.001…006`
- รวมเป็น `<out>/MOSA_dataset.zip`
- Unzip ลงใน `<out>/MOSA_dataset/` (ev/, yp/, yv/ categories)

**Key features**:
- ใช้ Zenodo API (`/api/records/{id}`) ดึง metadata + file links + MD5 checksums
- รองรับ **resume**: ถ้าไฟล์ดาวน์โหลดค้างจะอ่าน `Range: bytes=<offset>-` header ต่อจากจุดเดิม
- **MD5 verify** ทุกไฟล์ก่อนใช้ - fail-fast ถ้าไม่ตรง
- Skip ไฟล์ที่มีอยู่แล้วและ MD5 ถูก
- Reassemble parts  `unzip -q -n` (no overwrite)
- ไม่บันทึก token ไว้ใน history (อ่านจาก env)

**Token หาได้ที่**: https://zenodo.org/account/settings/applications/tokens/new/

**ใช้เมื่อไหร่**: เฉพาะตอน setup machine ใหม่ ครั้งเดียวพอ - MOSA ราว 21 GB

### 7.2 `scripts/prepare_violin.py` (VERBATIM + header note)

**ใช้ทำอะไร**: หลังจาก MOSA ถูก unzip แล้ว สคริปต์นี้กรองเฉพาะ category `ev` (ensemble violin) + `yv` (young violin) ทิ้ง `yp` (young piano) แล้วเรียก `prepare_mosa()` จาก `backend/training/dataset.py` เพื่อ:
1. Resample audio  16 kHz mono
2. แปลง note annotation (`*_align_notetime.csv` หรือ `*_note.csv`)  MOSA-style `onset_sec, offset_sec, midi` CSV
3. เขียนผลลัพธ์ลง `<OUT>/audio/*.wav` + `<OUT>/notes/*.csv`

** สำคัญ**: ไฟล์นี้มี **absolute paths hardcoded** อยู่ใน source (`EXTRACT_ROOT` + `OUT`) เพราะเป็น verbatim copy จากต้นฉบับ - **ต้องแก้ paths ก่อนรัน**

**ใช้เมื่อไหร่**: หลัง download MOSA แล้ว ก่อนจะรัน composition matrix

### 7.3 `scripts/prepare_musicnet_violin.py` (VERBATIM)

**ใช้ทำอะไร**: คัด 9 solo-violin recordings จาก MusicNet (Option B จาก Section 3.7 ของ README)

**Input**: 
- arg 1: `<MusicNet root>` - โฟลเดอร์ที่มี `musicnet/train_data/*.wav` + `musicnet/train_labels/*.csv` (และ test split เหมือนกัน)
- arg 2: `<out dir>` - ที่จะเขียน solo-violin prepared

**Output**: `<out>/audio/mn_<ID>.wav` + `<out>/notes/mn_<ID>.csv` ทั้งหมด 9 คู่

**Hardcoded list ของ solo violin IDs** (จาก `musicnet_metadata.csv` ที่ ensemble == "Solo Violin"):
```python
[2186, 2191, 2241, 2242, 2243, 2244, 2288, 2289, 2659]
```

**ขั้นตอนต่อไฟล์**:
1. หาทั้ง wav (`train_data` หรือ `test_data`) และ label CSV ที่คู่กัน
2. กรอง label เฉพาะ row ที่ `instrument == 41` (violin program ตาม MIDI GM)
3. แปลง `start_time` / `end_time` จาก sample-index (44.1 kHz)  seconds
4. Resample WAV  16 kHz mono via `librosa.load(sr=16000, mono=True)`
5. เขียน CSV format เดียวกับ MOSA: `onset_sec, offset_sec, midi`

**Prefix `mn_`**: ใส่ไว้ทุกชื่อไฟล์เพื่อให้ `finetune_crepe.py` แยก MusicNet ออกจาก MOSA ได้ (MusicNet จะไม่ถูกแบ่งเข้า val split - มีน้อยเกินไป)

**ใช้เมื่อไหร่**: หลัง download MusicNet แล้ว ก่อน build train_prepared

### 7.4 `scripts/build_composition_matrix.py` (VERBATIM - สำคัญที่สุดของ data pipeline)

**ใช้ทำอะไร**: เป็น **manifest builder** + **group-aware 10-way splitter** ที่สร้าง single source of truth สำหรับว่า recording ไหนคือ train ไหนคือ test

**Inputs (CLI args)**:
- `--mosa-root` - folder ของ MOSA prepared (มี `audio/` + `notes/`)
- `--musicnet-root` - folder MusicNet (อาจไม่ต้องระบุก็ได้, จะ skip)
- `--output-dir` - ที่เขียน manifest + stats
- `--seed` (default 42)

**Outputs**:
| File | คืออะไร |
|---|---|
| `manifest.csv` | คอลัมน์: dataset, filepath, set_id, role, duration_sec, piece_id, performer_id, annotation_path |
| `set_statistics.md` | ตาราง files/minutes per (dataset × set_id) |
| `training_composition_matrix.md` | ตาราง TRAIN/TEST per (dataset × set_id) |
| `exclusions.csv` | recordings ที่ถูกตัดทิ้ง + เหตุผล |

**Key algorithms** (ดูรายละเอียดใน Section 3.5-3.6 ของ README):

1. **Group ID derivation**:
   - MOSA: `<performer>_<piece>` จากชื่อไฟล์ (e.g. `S03_AA_audio.wav`  `S03_AA`)
   - MusicNet: `<composer>::<composition>` จาก `musicnet_metadata.csv`
2. **"Reserve test first" split**:
   - Sort groups by duration (largest first, tie-broken by seeded RNG)
   - Greedy: ใส่ groups เข้า test pool จนครบ total/10
   - กระจาย remaining groups เข้า set 1-9 แบบ least-loaded
3. **Sanity checks ที่ท้ายสคริปต์**:
   - `LEAKAGE`: ไม่มี file เดียวกันโผล่ 2 sets
   - `missing annotation_path`: ทุก row มี annotation จริง
   - per-set duration ภายใน ±50% ของค่าเฉลี่ย (warn ถ้าหลุด)

**Constants**:
- `N_SETS = 10`
- `TEST_SET = 10` (set 10 = test เสมอ)
- `SEED = 42`

**ใช้เมื่อไหร่**: หลังจาก prepare MOSA + MusicNet แล้ว - เป็นจุดที่ "ตัดสินใจ" ว่าไฟล์ไหนจะเป็น train/test

### 7.5 `scripts/build_train_prepared.py` (VERBATIM)

**ใช้ทำอะไร**: เอา `manifest.csv` มาคัดเฉพาะ `role=train` แล้วสร้าง **symlink farm** เพียง 1 โฟลเดอร์ ที่ trainer จะอ่านได้ง่าย

**Input (positional args, 3 ตัว)**:
- `<manifest.csv>` - จากขั้น 7.4
- `<musicnet_prepared>` - folder ที่ `prepare_musicnet_violin.py` (7.3) เขียนไว้
- `<out>` - folder ปลายทาง

**Output**: 
- `<out>/audio/*.wav` - 413 MOSA train (symlink) + 9 MusicNet solo-violin (symlink) = **422 symlinks**
- `<out>/notes/*.csv` - เหมือนกัน 422 symlinks

**Logic**:
1. อ่าน manifest, เลือก row ที่ `dataset==MOSA AND role==train`  symlink wav + csv
2. Loop ผ่าน `<musicnet_prepared>/audio/*.wav` ทั้ง 9 ไฟล์  symlink ทั้งหมด (เพราะ MusicNet solo violin ไม่อยู่ใน test set ของ manifest อยู่แล้ว)

**ทำไมต้อง symlink ไม่ copy?**: ประหยัดเนื้อที่ 2-3 GB และให้ trainer มี view เดียวของ training data

**สำคัญ**: ขั้นนี้ **กัน leakage** อย่างเข้มงวด - `role=test` recordings (set 10) ไม่มีทาง entering train pool

**ใช้เมื่อไหร่**: หลัง build_composition_matrix + prepare_musicnet_violin - เป็นขั้นสุดท้ายก่อน fine-tune

### 7.6 `scripts/finetune_crepe.py` (VERBATIM, renamed from `finetune_crepe_v2.py`)

**ใช้ทำอะไร**: เป็น **training entry point** หลัก - load pretrained CREPE-full weights, fine-tune บน `train_prepared`, ผลิต `best.pt` + `last.pt` + per-epoch checkpoints + CSV logs

**CLI args ทั้งหมด**:
| Flag | Default | คืออะไร |
|---|---|---|
| `--data` | (required) | `train_prepared/` folder (จาก 7.5) |
| `--out` | (required) | output folder (จะมี `checkpoints/`, `training_log.csv`, etc.) |
| `--model-size` | full | tiny/small/medium/large/full |
| `--lr` | 5e-5 | base learning rate |
| `--batch-size` | 32 | mini-batch size |
| `--max-epochs` | 30 | ceiling for training |
| `--patience` | 5 | early-stop after N non-improving epochs |
| `--weight-decay` | 1e-5 | AdamW decay |
| `--warmup-steps` | 1000 | linear warmup steps |
| `--val-frac` | 0.15 | fraction of MOSA recordings held for val |
| `--hop-ms` | 10.0 | hop size in ms |
| `--validate-every` | 500 | val pass every N steps |
| `--ckpt-every` | 2000 | save `last.pt` every N steps |
| `--device` | cuda:0 | gpu device |
| `--num-workers` | 2 | DataLoader workers |
| `--seed` | 42 | random seed |
| `--time-budget-hours` | 12 | hard wall-clock cap |

**Outputs ใน `--out`**:
- `checkpoints/best.pt` - weights ที่ val_RPA สูงสุด
- `checkpoints/last.pt` - weights ปัจจุบัน (สำหรับ resume)
- `checkpoints/epoch_NN.pt` - ทุก 5 epoch
- `checkpoints/final.pt` - ถ้าหยุดเพราะ time_budget
- `training_log.csv` - per-step rolling logs (step, epoch, split, loss, RPA, RCA, MAE, lr, wall_time)
- `training_log_epoch.csv` - per-epoch summary
- `training_summary.json` - final stop info + config dump

**Pipeline ภายใน**:
1. Set seeds (random, numpy, torch, cuda)
2. Build `CrepeFrameDataset` (จาก `backend/training/dataset.py`) บน `--data`
3. Split val: 5% ของ MOSA recordings (ตาม filename prefix), MusicNet (`mn_*`) ทั้งหมดอยู่ train
4. Load CREPE-full pretrained weights จาก `torchcrepe/assets/full.pth`
5. Optimizer = AdamW, scheduler = cosine with linear warmup
6. Per step:
   - Forward  per-bin BCE loss vs Gaussian-smoothed target (σ=25¢)
   - Backward + step
   - Track rolling RPA/RCA/MAE using **weighted-mean cents** decoder (เร็ว, แต่ดูคำเตือน)
   - Every 100 steps: log row to `training_log.csv`
   - Every `validate-every` steps: full val pass  ถ้า val_RPA สูงขึ้น save `best.pt`
   - Every `ckpt-every` steps: save `last.pt`
   - Check time budget  break ถ้าเกิน
7. End of epoch: full val + log to `training_log_epoch.csv`, early-stop logic

** คำเตือน (จาก Section 10 ของ README)**: val metric ที่ใช้ทำ early-stop เป็น **weighted-mean cents** (เร็ว) ซึ่ง diverge จาก **argmax+50¢** (ที่ใช้ใน eval จริง) หลังจากเทรนไปได้ระยะหนึ่ง - รอบนี้ทำให้เข้าใจผิดว่า overfit แล้วฆ่า training ทิ้ง ทั้งที่ `best.pt` ที่ step 20,000 จริง ๆ ดีกว่า pretrained บนทุก test set

**ใช้เมื่อไหร่**: หลัง build_train_prepared แล้ว เป็นขั้นที่กินเวลาที่สุด

### 7.7 `scripts/evaluate_model.py` (VERBATIM, renamed from `evaluate_crepe_v2.py`)

**ใช้ทำอะไร**: เป็น **evaluation entry point** - รัน CREPE (pretrained หรือ fine-tuned) บน test sets และเขียนตาม spec schema

**CLI args**:
| Flag | คืออะไร |
|---|---|
| `--manifest` | path ไปหา `composition/manifest.csv` |
| `--bach10-root` | folder Bach10 (optional, แต่ถ้าใส่จะ add 10 recordings) |
| `--mode` | `pretrained` หรือ `finetuned` |
| `--checkpoint` | path ไปหา `.pt` (required เมื่อ mode=finetuned) |
| `--output-dir` | ที่เขียน metrics |
| `--device` | gpu device |
| `--limit` | limit recordings per dataset (debug) |

**Outputs**:
- `baseline_metrics.json` หรือ `finetuned_metrics.json` - schema:
  ```json
  {
    "model": "crepe-full pretrained",
    "test_sets": {
      "MOSA_test":     {"RPA": ..., "RCA": ..., "MAE_cents": ..., "n_frames": ..., "n_recordings": ...},
      "MusicNet_test": {...},
      "Bach10":        {...},
      "URMP":          null
    },
    "preprocessing": {"sr": 16000, "hop_ms": 10, "voicing_threshold": 0.5},
    "ran_at": "ISO8601"
  }
  ```
- `*_metrics.md` - ตารางอ่านง่าย
- `*_metrics_detail.csv` - per-recording rows (RPA, RCA, MAE, frames_used)

**Pipeline ภายใน**:
1. โหลด test rows จาก manifest (`role=test`)
2. ถ้ามี `--bach10-root`  walk `<root>/<NN-piece>/<piece>-violin.wav` + `<piece>-GTF0s.mat`
3. Load CREPE (pretrained หรือจาก checkpoint)
4. ต่อ recording:
   - `librosa.load(sr=16000, mono=True)`
   - `torchcrepe.predict(...)` ด้วย `decoder=weighted_argmax` + median(periodicity, 3) + mean(pitch, 3)
   - Auto-retry batch size: 512  128  32  8 (ถ้า OOM)
   - Build GT F0 array ตาม dataset:
     - MOSA: piecewise-constant จาก `onset_sec/offset_sec/midi`
     - MusicNet: filter `instrument==41` แล้ว piecewise-constant
     - Bach10: row 0 ของ `GTF0s.mat` (per-10ms MIDI)
   - คำนวณ RPA / RCA / MAE จาก `backend/training/metrics.py` (50¢ tolerance, mir_eval-equivalent)
5. Aggregate: per-recording  mean across recordings; n_frames = sum

**ใช้เมื่อไหร่**: หลัง fine-tune เสร็จ - รัน 2 ครั้ง (pretrained + finetuned) เพื่อเทียบ

### 7.8 `scripts/load_example.py` (NEW)

**ใช้ทำอะไร**: ตัวอย่าง **minimal** "load best.pt + predict" สำหรับเทสว่า checkpoint โหลดได้และ output มี sense

**Usage**:
```bash
python scripts/load_example.py path/to/violin.wav [path/to/checkpoint.pt]
```
ถ้าไม่ระบุ checkpoint  default `checkpoints/best.pt`

**Output ที่ stdout**:
- file info + duration + frame count
- 10 frames แรก: `(time_sec, pred_hz, periodicity)`
- voiced statistics: count, percent voiced, min/median/max Hz

**ความแตกต่างจาก `examples/infer_single_wav.py`**:
- `load_example.py` = quick smoke test, ไม่มี argparse + เผื่อกรณี checkpoint format ห่อ `{"model": state_dict}`
- `infer_single_wav.py` = production-style (argparse, full CLI, error handling)

**ใช้เมื่อไหร่**: ตอนเพิ่ง extract zip มา อยากเช็คว่า best.pt ใช้ได้จริงไหม

---

## 8. `backend/training/` - Library code (3 ไฟล์)

โมดูลที่ scripts ใน `scripts/` import เข้ามาใช้ ผ่าน `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))`

### 8.1 `backend/training/__init__.py` (empty)

**ใช้ทำอะไร**: ให้ Python รู้ว่า `backend/training/` เป็น package - เพื่อให้ `from training.dataset import ...` ทำงานได้

### 8.2 `backend/training/dataset.py` (VERBATIM)

**ใช้ทำอะไร**: หัวใจของ data layer มี 2 ส่วน:

**ส่วน A: `prepare_mosa(mosa_root, out_dir)`** - function ที่ `scripts/prepare_violin.py` เรียก
- เดิน `*.wav` ใน `_unpacked/` หรือ root
- หา annotation `*_align_notetime.csv` หรือ `*_note.csv`
- Resample  16 kHz mono
- เขียน `<out_dir>/audio/<stem>.wav` + `<out_dir>/notes/<stem>.csv` (header: `onset_sec, offset_sec, midi`)

**ส่วน B: `class CrepeFrameDataset`** - PyTorch dataset ที่ `finetune_crepe.py` ใช้

Constructor:
```python
CrepeFrameDataset(prepared_dir, hop_ms=10.0, unvoiced_keep_prob=0.1,
                  sigma_cents=25.0, seed=0)
```

`_build_index()`: 
- เดิน `<prepared_dir>/audio/*.wav` + `<prepared_dir>/notes/<stem>.csv` ทั้งหมด
- สำหรับแต่ละ frame ที่ stride `hop_ms` (=160 samples @ 16 kHz)
  - หา note ที่ครอบ centre time  midi value (หรือ `-1` ถ้า unvoiced)
  - ถ้า unvoiced  keep ด้วย probability 0.1 เท่านั้น (กัน unvoiced ครองชุดข้อมูล)
- จบด้วย shuffle + print count

`__getitem__(i)`:
- โหลด audio (มี cache ในแมตม)
- ตัด frame ขนาด 1024 samples ตำแหน่ง `start`
- normalize: `(x - mean) / std`
- target = Gaussian-smoothed 360-bin vector (จาก `cents_to_bin_target(hz_to_cents(midi_to_hz(midi)), sigma=25)`)
- return `(torch.Tensor(frame), torch.Tensor(target))`

**Constants ที่ export**:
- `CREPE_BINS = 360`
- `_CENTS_MAPPING = (np.arange(360) * 20) + 1997.379...` - centre cents per bin
- `SAMPLE_RATE = 16000`
- `FRAME_LEN = 1024`

### 8.3 `backend/training/metrics.py` (VERBATIM)

**ใช้ทำอะไร**: คำนวณ metrics RPA / RCA / MAE (cents) แบบ mir_eval-compatible - เพราะ `mir_eval` ไม่ได้ install ใน venv โปรเจ็กต์

**3 functions**:

```python
pitch_mae_cents(pred_hz, true_hz, voiced)  float
    # mean(|1200 * log2(pred/true)|) ที่ voiced frames

raw_pitch_accuracy(pred_hz, true_hz, voiced, tol_cents=50)  float
    # fraction of voiced frames ที่ cents error ≤ 50¢

raw_chroma_accuracy(pred_hz, true_hz, voiced, tol_cents=50)  float
    # เหมือน RPA แต่ collapse octave ก่อน: ((d + 600) mod 1200) - 600
```

ทุก function return `nan` ถ้า `voiced.sum() == 0`

---

## 9. `checkpoints/best.pt` - Fine-tuned weights (85 MB)

**คืออะไร**: PyTorch state dict ของ CREPE-full ที่ผ่านการ fine-tune แล้ว - ผลผลิตจริงของโปรเจ็กต์

**Metadata**:
- ขนาดบน disk: 84.87 MB
- สร้างเมื่อ: 2026-05-23 ~22:00 (≈22 min into epoch 1, step 20,000)
- จาก rollback: ใน 11h ของการเทรน, step นี้คือจุดที่ val_RPA peak จึงถูกเก็บเป็น best
- Test-set numbers (จาก `docs/results_finetuned.json`):
  - MOSA_test: RPA 0.862 (vs pretrained 0.811)
  - MusicNet_test: RPA 0.309 (vs 0.119, +160%)
  - Bach10: RPA 0.982 (vs 0.967)

**วิธีโหลด**:
```python
import torch, torchcrepe
model = torchcrepe.Crepe("full")
sd = torch.load("checkpoints/best.pt", map_location="cpu", weights_only=True)
model.load_state_dict(sd)
model.eval()
```

**ทำไมเก็บแค่ `best.pt` ไม่เก็บ `last.pt`?**: 
- `last.pt` มาจากรอบที่ overfit ไปแล้ว - ไม่ดีกว่า best.pt ในทุก test set
- ขนาดเท่ากัน 85 MB จะเป็นการเปลือง

**License**: ตาม `NOTICE.md` - research/educational only, ไม่ใช้เชิงพาณิชย์ (เพราะ derivative จาก MOSA restricted-license)

---

## 10. `docs/` - เอกสารและผลลัพธ์ (6 ไฟล์)

### 10.1 `docs/PROJECT_COMPLETE_SUMMARY.md`

สำเนาเหมือนกับ `README.md` ที่ root ของ zip - มีไว้สำหรับเปิดอ่านขณะอยู่ใน `docs/` folder

### 10.2 `docs/training_results_report.md` (16 KB)

**คืออะไร**: รายงานเต็มของรอบ training 2026-05-23 ที่เขียนระหว่างทำโปรเจ็กต์ (เก่ากว่า `PROJECT_COMPLETE_SUMMARY.md` แต่ลึกกว่าในรายละเอียดรอบ training)

**8 sections**:
1. Training Summary - hardware, epochs, wall-clock, peak VRAM
2. Training Curves - references ไปหา `training_log.csv` + `training_log_epoch.csv`
3. Metrics Table - Before vs After + Δ
4. Updated Composition Matrix - ตาราง 10 sets × 2 datasets
5. MusicNet Polyphony Resolution - รายละเอียด Option B
6. Decisions / Departures from Defaults - ตารางเปรียบเทียบ spec vs actual + เหตุผล
7. Open Questions for User
8. Files Produced

**ใช้เมื่อไหร่**: ถ้าอยากเข้าใจ "ทำไมรอบนั้นถึงตัดสินใจแบบนั้น" หรือเตรียม second-pass training

### 10.3 `docs/results_baseline.json` (= `baseline_metrics.json`)

**คืออะไร**: ผลของ CREPE-full pretrained บน 4 test sets (URMP=null)

**ค่าหลัก**:
```
MOSA_test:      RPA 0.8109, RCA 0.8230, MAE 91.99¢, 553,463 frames, 52 recordings
MusicNet_test:  RPA 0.1186, RCA 0.2500, MAE 1470.62¢, 302,627 frames, 12 recordings
Bach10:         RPA 0.9667, RCA 0.9681, MAE 14.81¢, 29,514 frames, 10 recordings
URMP:           null
```

**ใช้เมื่อไหร่**: เป็น reference point สำหรับ "improvement vs baseline"

### 10.4 `docs/results_finetuned.json` (= `finetuned_metrics.json`)

**คืออะไร**: ผลของ `best.pt` บน test sets เดียวกัน

**ค่าหลัก**:
```
MOSA_test:      RPA 0.8622, RCA 0.8711, MAE 60.06¢, 514,358 frames, 52 recordings
MusicNet_test:  RPA 0.3093, RCA 0.4182, MAE 706.54¢, 99,916 frames, 12 recordings
Bach10:         RPA 0.9817, RCA 0.9831, MAE 16.54¢, 28,832 frames, 10 recordings
URMP:           null
```

**ข้อสังเกต**: 
- `n_frames` ของ MusicNet_test drop จาก 302K  100K (-67%) เพราะ fine-tuned model voicing-conservative ขึ้น
- Frames ที่เหลือมีความถูกต้องสูงกว่ามาก (RPA 0.31 vs 0.12)

### 10.5 `docs/training_summary.json` (1.3 KB)

**คืออะไร**: snapshot ของ state ตอนจบ training - ผลิตอัตโนมัติโดย `finetune_crepe.py`

**Fields**:
```json
{
  "total_epochs": 5,
  "best_epoch": 1,
  "best_val_rpa_weighted_mean": 0.6615,
  "best_step": 20000,
  "stop_reason": "user_killed_after_overfitting_observed",
  "stop_reason_detail": "...อธิบาย val-metric mismatch โดยละเอียด...",
  "wall_clock_sec": 41064.6,
  "peak_vram_mb": 1118,
  "best_pt_size_mb": 84.87,
  "config": {... full hyperparam dump ...}
}
```

**ใช้เมื่อไหร่**: ถ้าอยากเทียบกับรอบ training ของตัวเอง

### 10.6 `docs/training_log_epoch.csv` (313 B, 4 rows + header)

**คืออะไร**: per-epoch summary log

**Columns**: `epoch, train_loss, val_loss, val_RPA, val_RCA, val_MAE_cents, lr_end, wall_time_sec`

**Content** (4 completed epochs):
```
1: train 0.0152, val 0.0156, RPA 0.509, MAE 136¢, wall 8538s
2: train 0.0144, val 0.0163, RPA 0.375, MAE 156¢, wall 17209s
3: train 0.0141, val 0.0172, RPA 0.284, MAE 180¢, wall 25758s
4: train 0.0139, val 0.0183, RPA 0.232, MAE 205¢, wall 34421s
```

** ค่า `val_RPA` นี้คือ weighted-mean decoder** (ไม่ใช่ argmax+50¢ ของ test eval) - ดูคำเตือนใน 7.6

**Per-step log ที่ละเอียดกว่า** (`training_log.csv` 466 KB, 7,447 rows) **ไม่ได้รวมใน zip** เพื่อกันขนาด - ถ้าต้องการ plot training curves ละเอียด ๆ ขอจาก source workspace

---

## 11. `examples/infer_single_wav.py` (NEW, 2.4 KB)

**ใช้ทำอะไร**: ตัวอย่าง **production-style** สำหรับ inference บนไฟล์ WAV เดียว - เป็นจุดเริ่มต้นที่ผู้ใช้ปลายทาง copy-paste ไปเขียน application ของตัวเองได้

**Usage**:
```bash
python examples/infer_single_wav.py path/to/violin.wav \
  --checkpoint checkpoints/best.pt
```

**Optional flags**:
- `--sr 16000` - sample rate ที่ต้องการ (default 16000, hard requirement ของ CREPE)
- `--device cuda` - GPU device (auto-detect ถ้าไม่ใส่)

**Output ที่ stdout**:
```
frames total: <N>
frames voiced (periodicity >= 0.5): <M> (<P>%)
voiced pitch (Hz): min <min>, median <median>, max <max>
voiced cents (re A440): min <min>, median <median>, max <max>
```

**ความแตกต่างจาก `scripts/load_example.py`**:
- ใช้ argparse แบบเต็ม
- ตรวจ stereo  mean(axis=1)
- บังคับ sample rate ต้องตรง (raise error ถ้าไม่ตรง)
- ตรวจ format ของ checkpoint (รองรับทั้ง raw state_dict และ `{"model": state_dict}`)
- เพิ่ม cents (re A440) นอกจาก Hz

**ใช้เมื่อไหร่**: เมื่อต้องการ run model จริงบน audio ที่ไม่ใช่ test set

---

## ภาพรวมความสัมพันธ์ระหว่างไฟล์

```
                  ┌──────────────────────┐
                  │  configs/            │
                  │  finetune_default    │   human-readable config
                  │  .yaml               │
                  └──────────────────────┘
                            │ (อ่านโดยมนุษย์, ปัจจุบันไม่ได้ load
                            │  เข้า code โดยอัตโนมัติ)
                            ▼
  ┌─────────────────┐   ┌────────────────────┐   ┌───────────────────┐
  │ download_mosa   │  │ prepare_violin     │  │ MOSA prepared:    │
  │ _zenodo.py      │   │ (MOSA)             │   │ audio/ + notes/   │
  └─────────────────┘   └────────────────────┘   └─────────┬─────────┘
                                                            │
                        ┌────────────────────┐   ┌──────────▼────────┐
                        │ prepare_musicnet   │  │ MN solo-violin    │
                        │ _violin.py         │   │ prepared          │
                        └────────────────────┘   └──────────┬────────┘
                                                            │
                        ┌────────────────────┐              │
                        │ build_composition  │ ─┐           │
                        │ _matrix.py         │  │           │
                        └────────────────────┘  │           │
                                       │        │           │
                                       ▼        │           │
                              ┌──────────────┐  │           │
                              │ manifest.csv │ ─┼──┐        │
                              └──────────────┘  │  │        │
                                                │  ▼        ▼
                                                │ ┌─────────────────┐
                                                │ │ build_train     │
                                                │ │ _prepared.py    │
                                                │ └────────┬────────┘
                                                │          │
                                                │          ▼
                                                │ ┌─────────────────┐
                                                │ │ train_prepared/ │
                                                │ │ (symlink farm)  │
                                                │ └────────┬────────┘
                                                │          │
                                                │          ▼
                                                │ ┌─────────────────┐    ┌──────────────────┐
                                                │ │ finetune_crepe  │   │ backend/training/│
                                                │ │ .py             │    │   dataset.py     │
                                                │ └────────┬────────┘    │   metrics.py     │
                                                │          │             └──────────────────┘
                                                │          ▼
                                                │ ┌─────────────────┐
                                                │ │ checkpoints/    │
                                                │ │   best.pt       │
                                                │ │   last.pt       │
                                                │ │ training_log*   │
                                                │ │ training_summary│
                                                │ └────────┬────────┘
                                                │          │
                                                └──────────┤
                                                           ▼
                                              ┌──────────────────────┐    ┌──────────────────┐
                                              │ evaluate_model.py    │   │ Bach10 root      │
                                              │ (mode=pretrained,    │    │ (optional)       │
                                              │  mode=finetuned)     │    └──────────────────┘
                                              └──────────┬───────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │ baseline_metrics.json│
                                              │ finetuned_metrics    │
                                              │   .json/.md          │
                                              │ *_detail.csv         │
                                              └──────────────────────┘

   เส้นทางลัด สำหรับใช้ checkpoint อย่างเดียว:
   ┌────────────────────┐    ┌──────────────────────┐
   │ checkpoints/       │   │ examples/infer       │
   │ best.pt (มีในzip)  │    │ _single_wav.py       │
   └────────────────────┘    │  หรือ                │
                             │ scripts/load_example │
                             │ .py                  │
                             └──────────────────────┘
```

---

## 4 เส้นทางการใช้งานหลัก

### เส้นทาง A - แค่ inference (ไม่ต้องโหลด dataset)
1. ติดตั้ง `requirements.txt`
2. รัน `examples/infer_single_wav.py <wav> --checkpoint checkpoints/best.pt`
3. **เวลา**: < 5 นาที

### เส้นทาง B - Reproduce evaluation (ต้องโหลด test datasets)
1. ติดตั้ง dependencies
2. โหลด MOSA + MusicNet + Bach10
3. รัน `build_composition_matrix.py` เพื่อสร้าง manifest
4. รัน `evaluate_model.py --mode finetuned --checkpoint checkpoints/best.pt`
5. **เวลา**: 1-2 ชม. (ส่วนใหญ่หมดไปกับการโหลดข้อมูล)

### เส้นทาง C - Re-train จาก pretrained (ต้องโหลด train data)
1. ทุกอย่างใน B + เพิ่ม
2. `prepare_violin.py` + `prepare_musicnet_violin.py` + `build_train_prepared.py`
3. `finetune_crepe.py`
4. **เวลา**: 4-12 ชม. ขึ้นอยู่กับ GPU

### เส้นทาง D - Second-pass training (ตามคำแนะนำใน Section 10 ของ README)
1. ทุกอย่างใน C ด้วย flags ใหม่:
   ```
   --lr 1e-5 --freeze-early --max-epochs 10
   ```
2. ค่าใหม่ที่คาดว่าจะดีกว่า `best.pt` ปัจจุบัน
3. **เวลา**: 3-4 ชม.
4. **หมายเหตุ**: `--freeze-early` ยังไม่ได้ implement ใน `finetune_crepe_v2.py` (มีใน `backend/training/finetune_crepe.py` ตัวเก่าแต่ไม่ได้รวมใน zip) - ต้อง porting logic ก่อน

---

*จบเอกสาร - รายละเอียดเต็มอยู่ใน [README.md](README.md) sections 1-14*
