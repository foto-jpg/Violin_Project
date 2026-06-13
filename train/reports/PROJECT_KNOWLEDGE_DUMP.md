# คู่มืออ้างอิงโปรเจกต์ - Violin Checker (OMR + Fine-tune CREPE)

เอกสารนี้เป็นการอ้างอิงข้อเท็จจริงทั้งหมดของโปรเจกต์ แต่ละส่วนอ่านแยกได้อิสระ ทุกตัวเลขอ้างอิงถึงไฟล์ที่มา (สำหรับผลตัวเลขเต็มดู `PROJECT_COMPLETE_SUMMARY.md`)

**ข้อควรระวัง 3 ข้อที่ต้องจำไว้:**

1. **มีการเทรน 2 รอบ ไม่ใช่รอบเดียว** รอบแรก (~2026-05-12) ใช้ `backend/training/finetune_crepe.py` (Adam, lr=1e-4, Viterbi, MOSA sample 15 ไฟล์) ได้ `backend/checkpoints/crepe_violin.pt` ส่วน **รอบที่บันทึกไว้** (2026-05-23/24) ใช้ `finetune_crepe_v2.py` (AdamW, lr=5e-5, weighted_argmax, MOSA เต็ม 465 ไฟล์ + MusicNet) ได้ `outputs/finetune_2026-05-23/checkpoints/best.pt` เอกสารนี้ถือว่า **รอบ v2** คือ "โปรเจกต์"
2. **`cell_numbers_and_provenance.md` ล้าสมัย** มันรายงาน manifest 141 แถว / MOSA 15 ไฟล์ (สถานะ subset เก่า) ส่วน manifest ปัจจุบันมี **591 แถว (465 MOSA + 126 MusicNet)** ให้ยึด `manifest.csv`, `set_statistics.md`, `PROJECT_COMPLETE_SUMMARY.md` เป็นจริง
3. **OMR engine default ในโค้ดคือ `audiveris` ไม่ใช่ `oemer`** แม้ pipeline diagram จะเขียน "oemer" แต่ `omr.py:56` ตั้ง default เป็น `Engine.audiveris` ทั้งสอง engine ถูกต่อไว้

---

## ส่วนที่ 0: ก่อนเริ่ม

### 0.1 สำรวจ workspace
ขนาดรวม ~123 GB ส่วนใหญ่เป็น raw dataset: MOSA_full 48G, MOSA_full_downloads 43G, MusicNet 31G, Bach10 144M ส่วนโค้ด/artifact เล็ก: `outputs/` 408M, `backend/` 86M, `scripts/` 84K, `train_prepared/` 3.4M (symlink farm), `MusicNet_solo_violin_prepared/` 55M

### 0.2 Input ที่ขาด/หมายเหตุ
- **ไม่ใช่ git repository** (`git rev-parse` ล้มเหลว) มีแค่ `datasets/Bach10/.git` (จากการ clone) ไม่มี git log
- สคริปต์บางตัวถูกเปลี่ยนชื่อ: `finetune_crepe.py``finetune_crepe_v2.py`, `evaluate_model.py``evaluate_crepe_v2.py`
- ไฟล์ที่มีครบ: manifest.csv (591 แถว), set_statistics.md, baseline/finetuned_metrics.json, training_summary.json, training_log_epoch.csv (4 แถว), รายงานต่างๆ, checkpoint (best.pt/last.pt/crepe_violin.pt)
- ไฟล์ config YAML/INI มีเฉพาะใน zip ที่ ship (`violin_pitch_detection_starter/configs/`)

---

## ส่วนที่ 1: เฟส OMR

### 1.1 ภาพรวม pipeline
แปลงภาพ/สแกนโน้ตเป็น note list + MIDI ตามที่ทำใน `backend/`:
1. **Input** - user POST ภาพ (`POST /api/omr/process`, `omr.py:52`) รับ JPG/PNG/PDF, ทำทีละ job (429 ถ้าไม่ว่าง)
2. **OMR engine** - `_run_job` (`omr.py:19`) เลือก `Engine.oemer``run_oemer` หรือ default `run_audiveris` แต่ละตัวได้ **MusicXML**
3. **Post-process** - `read_musicxml` (จัดการ .mxl zip + ซ่อม namespace) → `parse_notes` (music21) → JSON note list; MIDI สร้างตามต้องการ
4. **Downstream** - note list ป้อนเข้า `audio_align.py::align_audio_to_score` (chroma + banded DTW) เทียบกับ pitch จาก CREPE ที่ `POST /api/match`

### 1.2 ระบุ OMR model
ต่อไว้ 2 engine ทั้งคู่ได้ MusicXML:

| รายการ | oemer | Audiveris |
|---|---|---|
| เวอร์ชัน | **0.1.8** (requirements pin `oemer>=0.1.6`) | 5.x (Docker; SYSTEM_OVERVIEW ระบุ 5.3) |
| Repo | github.com/BreezeWhite/oemer | github.com/Audiveris/audiveris |
| License | MIT (upstream) | **AGPL v3 (copyleft)** |
| วิธีได้มา | `pip install oemer` | Docker image build local |
| Weights | โหลด ONNX ตอนรันครั้งแรก (ไม่ bundle) | อยู่ใน Docker image |
| สถาปัตยกรรม | U-Net segmentation (ONNX) + ประกอบโน้ตด้วย rule | classical CV pipeline (Java) |

oemer เรียกผ่าน wrapper `python -m app.services._ort_patch` ซึ่งฉีด CUDA options/จำกัด 5 GB และลด batch เป็น 2 แล้วรัน `oemer.ete` เลือก GPU ด้วย `gpu_selector.get_freest_gpu`

### 1.3 ทำไมเลือก OMR นี้
จากสเปกโปรเจกต์ระบุว่า Audiveris "ดีที่สุดในกลุ่ม open source, output MusicXML" ส่วนเหตุผลที่เพิ่ม oemer เป็น engine ที่สอง (น่าจะเป็น path ที่ใช้ GPU) **ไม่มีบันทึกในโปรเจกต์** และ **ไม่มี benchmark เทียบ oemer vs Audiveris บนดิสก์**

### 1.4 กลไกการตรวจจับ
- **Audiveris**: เรียก `Audiveris -batch -export -output <dir> -- <input>` รับภาพหน้าหรือ PDF → (1) ลบเส้นบรรทัด (2) จำแนก glyph ด้วย classifier (3) ประกอบโครงสร้างดนตรี (4) export MusicXML (.mxl) หมายเหตุ: emit pickup measure เป็น `<measure number="0">` และอาจแยก multi-movement
- **oemer**: OMR end-to-end สำหรับภาพพิมพ์ - 2 U-Net ทำนายเส้นบรรทัด+สัญลักษณ์ → สกัดโน้ต/clef/accidental → เรียงเป็น measure → MusicXML รันบน ONNXRuntime (GPU ถ้ามี)

### 1.5-1.7 สคริปต์ OMR / preprocessing / post-processing
- ไฟล์หลัก: `omr.py` (endpoints), `oemer_engine.py`, `audiveris.py`, `_ort_patch.py`, `musicxml.py` + test 2 ไฟล์
- **ไม่มี raster preprocessing** (deskew/binarize/crop) ในโค้ดนี้ - ส่งภาพเข้า engine ตรงๆ มีแค่ validate upload + ปรับ ORT runtime
- Post-process: `read_musicxml` ซ่อม xmlns → `parse_notes` (music21) ได้ dict ราย pitch (measure, step, accidental, octave, MIDI, duration, seconds); `musicxml_to_midi` ผ่าน music21

### 1.8 OMR ถูก fine-tune ไหม
**ไม่** ทั้งสอง engine ใช้ pretrained ตามเดิม ไม่มีสคริปต์เทรน/dataset/checkpoint ของ OMR ในโปรเจกต์ การ fine-tune ทั้งหมดอยู่ฝั่ง audio/CREPE (ส่วนที่ 2)

### 1.9 ปัญหา OMR ที่ทราบ (จาก system design notes)
- multi-page: ต่อ PNG แล้วส่งทีเดียวล้มเหลว (Audiveris สับสน layout) → แก้ด้วย PDF-direct + merge movement
- pickup measure เป็น `<measure number="0">` ทำให้โค้ดที่เช็ค `m.number===1` พัง → index ด้วยตำแหน่ง array
- ความมั่นใจ OMR ลดบนโน้ตซับซ้อน (grace note, slur ซ้อน) → ต้องมีขั้นให้ user ยืนยัน/แก้
- ในโค้ด violin-checker นี้ไม่มี movement-merge/PDF-direct จึงเป็นข้อจำกัดแฝงกับ multi-movement

---

## ส่วนที่ 2: เฟส Audio / Fine-tune CREPE

### 2.1 ภาพรวม
raw datasets → สกัดไวโอลินแต่ละชุด → composition matrix (manifest + group-aware 10-way split) → train pool solo violin → fine-tune CREPE → checkpoint → ประเมิน → metrics JSON
- manifest 591 แถว (465 MOSA + 126 MusicNet; test 64 / train 527); test set (set_10) = 52 MOSA + 12 MusicNet
- (รายละเอียด dataset/pipeline เตรียมข้อมูล 10 ขั้น เหมือนใน `PROJECT_COMPLETE_SUMMARY.md` §2-3)

### 2.2-2.3 ชุดข้อมูล & เตรียมข้อมูล
สรุปย่อ (เต็มดู COMPLETE_SUMMARY §2-3):
- **MOSA**: Zenodo 11393449, CC-BY-NC, 465 ไฟล์/1144.3 นาที, training หลัก + MOSA_test, ไม่มี exclusion; group=`<performer>_<piece>`
- **MusicNet**: Zenodo 5120004, CC BY 4.0, 126 ไฟล์มีไวโอลิน (เทรนเฉพาะ 9 solo), ตัด 204 ไฟล์ไม่มีไวโอลิน; group=`<composer>::<composition>`
- **Bach10**: GitHub flippy-fyp, research-only, 10 `*-violin.wav`, test ภายนอกเท่านั้น (เพิ่มตอน eval ไม่อยู่ใน manifest)
- **URMP**: ติด Google Form, **ไม่ได้ใช้** (0 ไฟล์), ใช้ MOSA 5% แทน, hard-null ใน metrics JSON
- 10 ขั้นเตรียมข้อมูลทั้งหมดใน `build_composition_matrix.py` (line ปัจจุบัน: `split_into_sets` ที่ 163-206); Option B ใน `prepare_musicnet_violin.py` + `build_train_prepared.py`

### 2.4 สถาปัตยกรรม CREPE
| รายการ | ค่า |
|---|---|
| Base | `torchcrepe.Crepe("full")`, **torchcrepe 0.0.24**, torch 2.11.0 |
| Params | ~22M |
| Pretrained | `torchcrepe/assets/full.pth` - **88,991,291 bytes (84.87 MiB)** |
| Fine-tuned | `best.pt` - 88,989,129 bytes |
| โครงสร้าง | 6 conv block  flatten  dense  sigmoid 360 หน่วย |
| Input | 1024 sample @ 16 kHz mono, z-score ราย frame |
| Output | 360 bin, bin centre `arange(360)*20 + 1997.379...` cents, ครอบ ~C1-B7 ทีละ 20 cent |
| Decode | weighted-mean cents (ตอน val) vs argmax (`weighted_argmax`, ตอน eval/inference) - **สอง decoder เบนออกจากกัน** (ดู 2.7) |

### 2.5 ทำไม CREPE
(ก) มาตรฐานวงการ F0 เสียงเดี่ยว ~98% RPA Bach10 (ข) torchcrepe เทรน weights ได้ (ค) 360 bin = 20 cent (ง) frame-local เข้ากับ score-follower **ไม่มีการ benchmark เทียบ alternatives จริง** - PESTO/RMVPE/SwiftF0/BasicPitch ถูกพูดถึงเชิงบรรยายเท่านั้น

### 2.6 Hyperparameters
(เต็มดู COMPLETE_SUMMARY §5) ค่าหลัก: BCE σ=25¢, AdamW, lr=5e-5, cosine+warmup 1000, weight_decay=1e-5, batch=32, max_epochs=30, patience=5, seed=42, voicing 0.5, 16kHz, hop 10ms, unvoiced_keep_prob=0.1
**จุดเบี่ยงจากสเปก (จริง vs default)**: validate-every 50010,000, ckpt-every 2,0005,000, val-frac 0.150.05 (config ใน zip รายงานค่าสเปก)

### 2.7 การรันจริง
| รายการ | ค่า |
|---|---|
| ฮาร์ดแวร์ | RTX 3070 Ti 8 GB, cuda:3 |
| เวลารวม | 41,064.6s ≈ 11:24:24 |
| Epoch | 5/30 (epoch 5 ถูกขัด) |
| Best epoch | 1, best_step 20,000 |
| เหตุผลหยุด | `user_killed_after_overfitting_observed` |
| Best val RPA (weighted-mean) | 0.6615 |
| Peak VRAM | 1,118 MB |
| ข้อมูลเทรน | 413 MOSA + 9 MusicNet solo = 422 ไฟล์ (~17.7 ชม.) |

 **ความขัดแย้งภายในที่ต้องแจ้ง**: JSON ระบุ `best_step=20000` แต่ `stop_reason_detail` บอกว่า best จริงอยู่ที่ **step 10000** สองค่านี้ขัดกัน

Log ราย epoch (มีแค่ 4 แถว เพราะ epoch 5 ถูกขัดก่อนเขียนแถว):
```
epoch  train_loss  val_loss  val_RPA(wm)  val_RCA(wm)  val_MAE  lr_end     wall(s)
1      0.015198    0.015578   0.5090       0.5124       136.20   4.99e-05   8538.7
2      0.014367    0.016327   0.3751       0.3776       155.81   4.95e-05   17209.6
3      0.014060    0.017213   0.2843       0.2867       180.17   4.88e-05   25758.1
4      0.013852    0.018282   0.2320       0.2348       204.87   4.78e-05   34421.4
```
คอลัมน์ val_RPA คือ decoder weighted-mean ที่ลดทุก epoch (กับดักหลัก) - RPA จาก argmax บน best.pt สูงกว่ามาก (2.11)

### 2.8 ฟังก์ชันสำคัญ (ย่อ)
- `build_composition_matrix.py`: `scan_mosa` (36-75), `scan_musicnet` (109-160), `split_into_sets` (163-206, reserve-test-first), `write_manifest/write_set_stats/write_matrix/main`
- `prepare_musicnet_violin.py`: `convert_labels` (program-41→วินาที), `main` (resample + เขียน `mn_<id>`)
- `finetune_crepe_v2.py`: `cosine_lr`, `bin_to_cents` (weighted-mean), `evaluate`, `main` (train loop; save best.pt ที่ :221-229)
- `evaluate_crepe_v2.py`: `_piecewise_f0_from_notes`, `gt_f0_*`, `predict_f0` (weighted_argmax + median/mean + OOM fallback), `aggregate_per_dataset` (per-recordingmean), `add_bach10`
- `dataset.py`: `cents_to_bin_target` (Gaussian σ=25¢), `prepare_mosa`, `CrepeFrameDataset`
- `metrics.py`: `raw_pitch_accuracy` (±50¢), `raw_chroma_accuracy` (ยุบ octave) - mir_eval-compatible

### 2.9 เทคนิค/อัลกอริทึม
group-aware split, reserve-test-first (กัน test ว่างเมื่อ group < n_sets), piecewise-constant F0 (มี auto-tuning effect), Gaussian target σ=25¢, BCE per-bin, cosine LR + warmup, voicing gating (train เก็บ unvoiced 10%; eval ≥0.5), per-recording aggregation, Option B (solo-violin filter), MD5-verified resumable Zenodo download

### 2.10 วิธีประเมิน
- test sets จาก manifest `role=="test"` + Bach10 แยก + URMP null
- decoder `weighted_argmax` + `median(periodicity,3)` + `mean(pitch,3)`, fmin/fmax=50/2000, OOM fallback 512128328
- frame ใช้เมื่อ `voiced_gt & periodicity≥0.5 & isfinite & pred>0`
- รวม per-recording → เฉลี่ยข้ามไฟล์; output: baseline/finetuned_metrics.json + .md + _detail.csv

### 2.11 ผลลัพธ์ (ตรงจาก JSON)

| ชุดทดสอบ | RPA pre | RPA ft | Δ RPA | RCA ft | MAE pre | MAE ft | Δ MAE | n_frames preft |
|---|---|---|---|---|---|---|---|---|
| MOSA_test | 0.8109 | 0.8622 | +0.0513 | 0.8711 | 91.99 | 60.06 | −31.93 | 553,463  514,358 |
| MusicNet_test | 0.1186 | 0.3093 | +0.1907 | 0.4182 | 1470.62 | 706.54 | −764.08 | 302,627  99,916 |
| Bach10 | 0.9667 | 0.9817 | +0.0150 | 0.9831 | 14.81 | 16.54 | **+1.73** | 29,514  28,832 |
| URMP | N/A | N/A | - | - | - | - | - | - |

baseline รันที่ 2026-05-23T21:12, finetuned 2026-05-24T09:13; preprocessing sr=16000, hop_ms=10, voicing=0.5

### 2.12 ผลดีไหม
- RPA/RCA ดีขึ้นทั้ง 3 ชุด (MOSA +5.1, MusicNet +19.1≈×2.6, Bach10 +1.5); MAE ดีขึ้น MOSA/MusicNet แต่ Bach10 +1.73¢ (noise)
- regress ราย recording: **1 ไฟล์** - MusicNet `2147.wav` Δ_RPA −0.0033
- n_frames MusicNet ลด 67% (voicing อนุรักษ์กว่า; frame ที่เหลือแม่นกว่า)
- SOTA Bach10: เรา 0.982 (real) vs Tamer 2022 0.989-0.992 (synth, ง่ายกว่า) vs lars76 0.985 (real, เทียบตรงสุด); MOSA/MusicNet ไม่มีตัวเลขเทียบตีพิมพ์

---

## ส่วนที่ 3: วิเคราะห์ Error (ทำแล้ว)

(เต็มดู `error_analysis_report.md` / `error_analysis_summary.md`)
- **MOSA** - bottom-10 = ท่อนเร็ว/โน้ตถี่ (โน้ต/วิ 6.02 vs 1.93) พลาดแบบ "ผิดเล็กๆ จำนวนมาก" ย่านกลาง ไม่ใช่สูง (เชื่อมั่นสูง)
- **MusicNet** - ความยากสม่ำเสมอ, polyphony พังทั้งชุด (~25% frame >1200¢ ทั้ง bottom/top) (เชื่อมั่นต่ำ)
- **Bach10** - เพดานโมเดล RPA ∈ [0.977, 0.985] (เชื่อมั่นสูง)
- fine-tune ทำแย่ลง 1 ไฟล์ (MusicNet 2147)
- ขั้นถัดไป: (1) เทรนรอบสอง lr=1e-5 freeze-early (2) source separation ก่อน CREPE สำหรับ MusicNet (3) สืบไฟล์ที่แย่ลง (4) แก้ val-metric ให้ใช้ argmax+50¢

---

## ส่วนที่ 4: ปัญหาที่ค้าง & ข้อจำกัด

| # | ปัญหา | ผลกระทบ | แนวทางแก้ |
|---|---|---|---|
| 1 | val-metric ไม่ตรง (weighted-mean vs argmax+50¢) | เสีย compute ~11 ชม. หยุดผิดสัญญาณ | คำนวณ RPA ตอนเทรนจาก argmax |
| 2 | polyphony MusicNet | RPA ระดับพื้นบน mix; Option B เก็บ 9 solo | Option A: Demucs/Spleeter แยก stem |
| 3 | MAE Bach10 +1.73¢ | เล็กน้อย | LR ต่ำ freeze-early รอบสอง |
| 4 | n_frames MusicNet −67% | จำนวน voiced frame เทียบข้ามโมเดลไม่ได้ | ระบุไว้ ไม่เทียบ frame count |
| 5 | URMP ไม่มี | ไม่มี OOD val จริง; ใช้ MOSA 5% แทน | ขอผ่าน Google Form แล้วรันใหม่ |
| 6 | piecewise F0 auto-tuning effect | โมเดลอาจ over-correct pitch แสดงอารมณ์; โอเคสำหรับสอน ไม่เหมาะวิจัย | ยอมรับสำหรับงานนี้ ระบุตอนตีพิมพ์ |
| 7 | จุดเบี่ยงจากสเปก | validate 50010000, ckpt 20005000, val MOSA 5% | รันบน GPU แรงกว่าเพื่อทำตามสเปก |
| 8 | ยังไม่เทรนรอบสอง | ทิ้ง best.pt ที่อาจดีกว่า | lr=1e-5 freeze-early max_epochs=10 (~3-4 ชม.) |

---

## ส่วนที่ 5: ข้อมูลทำซ้ำ

- **Python** 3.11.14; **OS** Linux 6.8.0; host 4 GPU (รันใช้ cuda:3 RTX 3070 Ti 8 GB)
- **เวอร์ชันแพ็กเกจหลัก**: `torch==2.11.0`, `torchcrepe==0.0.24`, `librosa==0.11.0`, `soundfile==0.13.1`, `scipy==1.17.1`, `numpy==2.4.4`, `music21==9.9.1`, `oemer==0.1.8`, `fastapi==0.115.14`, `pretty_midi==0.2.11` (หมายเหตุ: torchcrepe ไม่อยู่ใน requirements.txt - เป็น dep ตอนเทรนเท่านั้น; mir_eval ไม่ใช้ - reimplement metrics เอง)
- **Seed** 42
- **คำสั่ง** (เต็มดู COMPLETE_SUMMARY §12): install  วาง dataset  `build_composition_matrix.py`  `prepare_musicnet_violin.py` + `build_train_prepared.py`  `finetune_crepe.py` (--lr 5e-5 --batch-size 32 --max-epochs 30 --patience 5 --warmup-steps 1000 --val-frac 0.05 --weight-decay 1e-5 --seed 42 --time-budget-hours 12)  `evaluate_model.py` pretrained แล้ว finetuned

---

## ส่วนที่ 6: รายการไฟล์สำคัญ

| Path | ชนิด | ขนาด | หน้าที่ |
|---|---|---|---|
| `datasets/composition/manifest.csv` | data | 125 KB | **แหล่งความจริงเดียว** ของ split (591 แถว) |
| `datasets/composition/set_statistics.md` | data | 715 B | ไฟล์/นาที ต่อ (dataset×set) |
| `datasets/composition/exclusions.csv` | data | 20 KB | 204 MusicNet ที่ตัด (ไม่มีไวโอลิน) |
| `datasets/composition/cell_numbers_and_provenance.md` | doc | - | **ล้าสมัย** (subset 15 ไฟล์) |
| `datasets/train_prepared/{audio,notes}` | data | 3.4 MB | symlink farm: MOSA train + 9 MusicNet solo |
| `datasets/MusicNet_solo_violin_prepared/` | data | 55 MB | 9 ไฟล์ solo violin (Option B) |
| `outputs/finetune_2026-05-23/checkpoints/best.pt` | model | 84.87 MB | **weights ที่ fine-tune (deliverable)** |
| `outputs/finetune_2026-05-23/checkpoints/last.pt` | model | 84.87 MB | checkpoint สุดท้าย |
| `backend/checkpoints/crepe_violin.pt` | model | 84.87 MB | โมเดล**รอบเก่า** (sample-subset, 2026-05-12) |
| `outputs/finetune_2026-05-23/baseline_metrics.json` | result | 755 B | CREPE pretrained 3 ชุด |
| `outputs/finetune_2026-05-23/finetuned_metrics.json` | result | 759 B | best.pt 3 ชุด |
| `outputs/finetune_2026-05-23/training_summary.json` | result | 1.3 KB | config + เหตุผลหยุด |
| `outputs/finetune_2026-05-23/training_log.csv` | log | 466 KB | log ทุก 100 step |
| `outputs/finetune_2026-05-23/PROJECT_COMPLETE_SUMMARY.md` | doc | 43 KB | เอกสารเดี่ยวที่ครบสุด (§1-14) |
| `scripts/build_composition_matrix.py` | code | 13 KB | manifest + แบ่ง 10 ชุด |
| `scripts/finetune_crepe_v2.py` | code | 13 KB | **สคริปต์เทรนจริง** |
| `scripts/evaluate_crepe_v2.py` | code | 13 KB | **สคริปต์ eval จริง** |
| `backend/training/dataset.py` | code | - | CrepeFrameDataset + prepare_mosa |
| `backend/training/metrics.py` | code | 1.1 KB | RPA/RCA/MAE |
| `backend/training/finetune_crepe.py` | code | - | trainer**รอบเก่า** (Adam, lr=1e-4, Viterbi) |
| `backend/app/services/audio_engine.py` | code | 11.5 KB | CREPE inference + แบ่งโน้ต (deployed) |
| `backend/app/services/audio_align.py` | code | 7.1 KB | chroma + banded DTW alignment |
| `backend/app/services/{oemer_engine,audiveris}.py` | code | ~1.3 KB | OMR wrapper |
| `backend/app/utils/musicxml.py` | code | 3.7 KB | MusicXML read/parse/MIDI |

**เอกสารออกแบบที่เกี่ยวข้อง** (ไม่ได้รวมในโปรเจกต์นี้): product spec (เหตุผล OMR §1.3) และ system design (การออกแบบ production, decoder, ปัญหาที่ทราบ)

---

## ส่วนที่ 7: คำถามที่ค้างให้เจ้าของโปรเจกต์

1. **เหตุผลที่ต่อ OMR 2 engine** (§1.3) - มีเหตุผลว่าทำไม Audiveris แต่ไม่มีเหตุผล/benchmark สำหรับการเพิ่ม oemer เขียน 1-2 ประโยคถ้าจำเป็นต่อรายงาน
2. **ไม่มี benchmark CREPE vs alternatives** (§2.5) - PESTO/RMVPE/SwiftF0/BasicPitch พูดถึงเชิงบรรยายเท่านั้น ไม่ได้วัดตัวเลข
3. **best_step 20,000 vs 10,000 ขัดกัน** (§2.7) - JSON บอก 20000, stop_reason บอก 10000 อันไหนถูก (กระทบคำกล่าว "งานจริง ~22 นาที")
4. **ใช้ checkpoint ไหน deploy** - backend โหลดตาม `CREPE_CHECKPOINT` ใช้ best.pt (v2) หรือ crepe_violin.pt (เก่า)? ตัวเลขใน README (MAE 66.723.6¢ บน de2_yv10_t1) มาจากรอบ**เก่า** ไม่ใช่ v2 - ยืนยันว่ารายงานควรอ้างอันไหน
5. **`composition` vs `composition_v2`** - ทั้งคู่มี manifest 591 แถว set_statistics เหมือนกัน อันไหน canonical ลบอีกอันได้ไหม
6. **doc ล้าสมัย** - `cell_numbers_and_provenance.md` (subset 141 แถว) ควร regenerate กับ manifest 591 แถว หรือเก็บเป็นประวัติ
7. **URMP** - ยังติด gate ยืนยันว่าจะเก็บเป็น input อนาคต หรือถอดออกจาก headline
