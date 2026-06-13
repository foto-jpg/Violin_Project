# รายงานข้อมูลสำหรับสร้าง Excel

ไฟล์ต้นทาง: `manifest.csv` (591 แถว), `set_statistics.md`, `exclusions.csv`, `baseline_metrics.json`, `finetuned_metrics.json`, `training_summary.json`, `training_results_report.md`

ตรวจสถานะ:
- [x] manifest สะท้อน MOSA เต็ม (465 ไฟล์ - เกิน threshold 100 ไฟล์; สถานะ sample 15 ไฟล์หายแล้ว)
- [ ] manifest สะท้อนการกรอง Option B ของ MusicNet (**ไม่ผ่าน**: manifest ยังมี MusicNet train 114 แถว เพราะ Option B ทำตอน training-prep ผ่าน `build_train_prepared.py` ไม่ได้กรองที่ manifest ดูส่วนที่ 7)
- [x] baseline/finetuned_metrics.json มีอยู่และ parse เป็น JSON ได้

หมายเหตุ: ตามที่เจ้าของโปรเจกต์ตัดสินใจ รายงานนี้ใช้ manifest ที่ยังไม่กรอง และบันทึกความไม่ตรงไว้ในส่วนที่ 7

---

## ส่วนที่ 1: ตัวเลของค์ประกอบราย cell (re-aggregate จาก manifest.csv)

### MOSA
| set_id | role | n_files | duration_sec | duration_min |
|--------|-------|---------|--------------------|--------------------|
| 1 | train | 43 | 6836.83 | 113.95 |
| 2 | train | 44 | 6877.62 | 114.63 |
| 3 | train | 47 | 6828.72 | 113.81 |
| 4 | train | 45 | 6878.22 | 114.64 |
| 5 | train | 46 | 6899.20 | 114.99 |
| 6 | train | 48 | 6833.39 | 113.89 |
| 7 | train | 48 | 6838.77 | 113.98 |
| 8 | train | 48 | 6889.23 | 114.82 |
| 9 | train | 44 | 6829.03 | 113.82 |
| 10 | test | 52 | 6945.17 | 115.75 |
| **รวม** | - | **465** | **68656.18** | **1144.27** |

### MusicNet (ตาม manifest - ดู Option B ในส่วนที่ 7)
| set_id | role | n_files | duration_sec | duration_min |
|--------|-------|---------|--------------------|--------------------|
| 1 | train | 14 | 5301.70 | 88.36 |
| 2 | train | 12 | 5241.21 | 87.35 |
| 3 | train | 14 | 5315.17 | 88.59 |
| 4 | train | 12 | 5305.40 | 88.42 |
| 5 | train | 13 | 5016.08 | 83.60 |
| 6 | train | 12 | 5319.66 | 88.66 |
| 7 | train | 8 | 5056.58 | 84.28 |
| 8 | train | 15 | 5239.15 | 87.32 |
| 9 | train | 14 | 5316.52 | 88.61 |
| 10 | test | 12 | 5390.22 | 89.84 |
| **รวม** | - | **126** | **52501.69** | **875.03** |

ยอด MusicNet train 114 แถวข้างบนรวม 9 ไฟล์ solo violin (เข้าเกณฑ์ Option B) **และ** 105 ไฟล์ polyphonic (Option B ตัดออกจากการเทรน) trainer ใช้แค่ 9 ไฟล์ solo violin ถ้า Excel ต้องการจำนวน "ไฟล์ที่ใช้เทรนจริง" ของ MusicNet ควรเป็น **9** ไม่ใช่ 114 (ดูส่วนที่ 7)

---

## ส่วนที่ 2: ตรวจสอบยอดรวม

| Metric | MOSA | MusicNet |
|---|---|---|
| ไฟล์ที่เก็บ (หลังกรองทั้งหมด) | 465 | 126 |
| ไฟล์ที่ตัด | 0 | 204 |
| ความยาวรวม (นาที) | 1144.27 | 875.03 |
| ไฟล์ train (set 1-9) | 413 | 114 |
| ไฟล์ test (set 10) | 52 | 12 |
| set ที่ไม่ว่าง | 10/10 | 10/10 |
| ช่วงความยาวต่อ set (นาที) | 113.81 - 115.75 | 83.60 - 89.84 |
| ความยาวเฉลี่ยต่อ set (นาที) | 114.43 | 87.50 |

**ไม่มีความไม่ตรง - การ aggregate จาก manifest ตรงกับ set_statistics.md**

---

## ส่วนที่ 3: Metrics การประเมิน (ตรงจาก JSON)

### CREPE pretrained (baseline_metrics.json)
| ชุดทดสอบ | RPA | RCA | MAE(¢) | n_frames | n_rec | หมายเหตุ |
|---|---|---|---|---|---|---|
| MOSA_test | 0.8109 | 0.8230 | 91.99 | 553,463 | 52 | |
| MusicNet_test | 0.1186 | 0.2500 | 1470.62 | 302,627 | 12 | mix polyphonic; GT กรอง instrument=41 |
| URMP | N/A | N/A | N/A | N/A | N/A | ข้าม (ติด Google Form) |
| Bach10 | 0.9667 | 0.9681 | 14.81 | 29,514 | 10 | violin stem |

### CREPE fine-tuned (finetuned_metrics.json)
| ชุดทดสอบ | RPA | RCA | MAE(¢) | n_frames | n_rec | หมายเหตุ |
|---|---|---|---|---|---|---|
| MOSA_test | 0.8622 | 0.8711 | 60.06 | 514,358 | 52 | |
| MusicNet_test | 0.3093 | 0.4182 | 706.54 | 99,916 | 12 | n_frames ลด ~67% - ดูส่วนที่ 7 |
| URMP | N/A | N/A | N/A | N/A | N/A | ข้าม |
| Bach10 | 0.9817 | 0.9831 | 16.54 | 28,832 | 10 | |

### Delta (Fine-tuned − Pretrained)
| ชุดทดสอบ | ΔRPA | ΔRCA | ΔMAE(¢) | Δn_frames | หมายเหตุ |
|---|---|---|---|---|---|
| MOSA_test | +0.0513 | +0.0481 | −31.93 | −39,105 (−7.1%) | |
| MusicNet_test | +0.1907 | +0.1682 | −764.08 | −202,711 (−67.0%) | frame ลดมาก - ดูส่วนที่ 7 |
| URMP | N/A | N/A | N/A | N/A | ข้าม |
| Bach10 | +0.0150 | +0.0150 | +1.73 | −682 (−2.3%) | MAE แย่ลงเล็กน้อย |

ΔMAE ติดลบ = ดีขึ้น (cent-error ต่ำลง) Bach10 ΔMAE ทำเครื่องหมายว่า regress เพราะ metric แย่ลงเล็กน้อย (+1.73¢) แม้ RPA จะดีขึ้น

### Metadata preprocessing
sample rate 16000 Hz, hop 10 ms, voicing threshold 0.5; baseline ran_at 2026-05-23T21:12:17, finetuned ran_at 2026-05-24T09:13:07, model name `crepe-full finetuned (best.pt)`

---

## ส่วนที่ 4: สรุปการรันเทรน (จาก training_summary.json)

| รายการ | ค่า |
|---|---|
| Base model | crepe-full (~22M params) |
| Seed | 42 |
| ฮาร์ดแวร์ | RTX 3070 Ti 8 GB (cuda:3 จากเครื่อง 4-GPU) |
| Epoch ที่เทรน | 5 (จาก max 30) |
| Best epoch | 1, best step 20,000 |
| เหตุผลหยุด | `user_killed_after_overfitting_observed` |
| เวลารวม | 11:24:24 (41,064.6s) |
| Training loss สุดท้าย | 0.0134 (step 744,700) |
| Validation loss สุดท้าย | 0.0192 (step 740,000) |
| Best val metric | weighted-mean cents RPA = 0.6615 (ไม่ใช่ argmax+50¢ ตามสเปก) |
| Peak VRAM | ~1.1 GB |
| Validation set | MOSA 5% ราย recording (21 ไฟล์) - URMP ไม่มี |
| ข้อมูลเทรน | MOSA set 1-9 (413 ไฟล์ ~17 ชม.) + 9 MusicNet solo (~30 นาที) = 422 ไฟล์ |

Optimizer: AdamW, lr=5e-5, weight_decay=1e-5, cosine + warmup 1000 step; Loss: per-bin BCE บน target 360-bin Gaussian (σ=25¢)

---

## ส่วนที่ 5: สรุปการตัดข้อมูล

| Dataset | เหตุผล | จำนวน |
|---|---|---|
| MusicNet | ไม่มีแถวไวโอลิน (program 41) | 204 |
| MOSA | (ไม่มี) | 0 |

**ไม่มีการบันทึก Option B exclusion ใน `exclusions.csv`** เพราะ Option B ทำตอน training-prep (`build_train_prepared.py`) ไม่ใช่ตอนสร้าง composition matrix; 105 ไฟล์ MusicNet polyphonic ที่ไม่เข้าเทรนยังอยู่ใน manifest ภายใต้ `role=train` และไม่ปรากฏใน exclusions.csv (ดูส่วนที่ 7)

---

## ส่วนที่ 6: ตรวจซ้ำความถูกต้อง

| รายการตรวจ | ผล | รายละเอียด |
|-------|--------|--------|
| ไม่มีไฟล์อยู่เกิน 1 set | ผ่าน | 0 ซ้ำ จาก 591 แถว |
| ทุก annotation_path มีอยู่จริงบนดิสก์ | ผ่าน | ขาด 0/591 |
| ทุกไฟล์ผ่านการตรวจไวโอลิน | ผ่าน | 204 MusicNet ถูกกรองด้วย program=41; MOSA จาก yv/ev (yp=เปียโนตัดต้นทาง) |
| set ไม่ว่างอยู่ใน 50%-150% ของค่าเฉลี่ย | ผ่าน | MOSA 113.81-115.75 (เฉลี่ย 114.43); MusicNet 83.60-89.84 (เฉลี่ย 87.50) |
| set_10 (TEST) ≥ 10% ของความยาวรวม | ผ่าน | MOSA 10.12%; MusicNet 10.27% |
| baseline_metrics.json schema ถูกต้อง | ผ่าน | มี key ครบ |
| finetuned_metrics.json schema ถูกต้อง | ผ่าน | schema เดียวกัน |
| best.pt มีอยู่และขนาดไม่เป็น 0 | ผ่าน | 84.87 MB |
| training_log.csv มีข้อมูล | ผ่าน | 7,521 แถว (7,447 train + 74 val) |

---

## ส่วนที่ 7: ข้อค้นพบที่น่าแปลกใจ / คำถามค้าง

- **Option B ไม่ได้ apply กับ manifest.csv** ตัวกรอง 9 ไฟล์ solo violin ทำเป็น symlink farm ตอน training-prep (`build_train_prepared.py` - link เฉพาะ 9 solo + 413 MOSA train เข้า `train_prepared/`) manifest ยังบันทึก MusicNet train 114 แถว **แนะนำสำหรับ Excel**: แสดง "ไฟล์ MusicNet ที่ใช้เทรน: 9" พร้อม footnote และ (ก) เก็บเลข 114 สำหรับ cell "MusicNet manifest" หรือ (ข) ระบุการแยก 9 vs 114 ให้ชัด; 12 ไฟล์ test ไม่เปลี่ยน
- **n_frames MusicNet_test ลด ~67%** (302,627 → 99,916) ระหว่าง pretrained → finetuned; n_frames = frame voiced+confident (periodicity ≥ 0.5) โมเดล finetuned อนุรักษ์กว่าบนเสียง polyphonic 2 ใน 3 ของ frame จึงต่ำกว่า threshold; frame ที่ผ่านแม่นกว่ามาก (RPA เพิ่ม 3 เท่า, MAE ลดกว่าครึ่ง) เป็น feature ไม่ใช่ bug - แต่ Excel ควรระบุว่า cell MusicNet_test รายงาน accuracy บน subset ที่เล็กและสะอาดกว่า
- **MAE Bach10 แย่ลงเล็กน้อย** (14.81¢ → 16.54¢, +1.73¢) แม้ RPA ดีขึ้น (+1.5 จุด) โมเดลกู้ frame ก้ำกึ่งได้มากขึ้นแลกกับ cent-error ต่อ frame เพิ่มนิดหน่อย น่าจะไม่คุ้มจะ tune; แจ้งไว้ให้อาจารย์ที่ปรึกษา
- **best.pt มาจาก step 20,000 ใน epoch 1 เท่านั้น** โมเดลดีสุดตั้งแต่ต้น (~22 นาที) อีก ~11 ชม. ไม่ได้ checkpoint ที่ดีกว่าตาม val metric weighted-mean แต่ตัวเลขทดสอบตามสเปกดีขึ้นจริง (ส่วนที่ 3) ตีความ: "weighted-mean val RPA" ที่ใช้เป็น proxy early-stop มี noise และไม่ตรงกับ argmax ตอนทดสอบ รันใหม่ด้วย val metric ที่ถูกอาจ converge เร็วขึ้น
- **ข้าม URMP ทั้งหมด** ทุก entry URMP ใน JSON เป็น `null` แสดง "N/A"; Excel ควรเว้นแถว URMP ว่าง + footnote "URMP ไม่มี - รอสิทธิ์ Google Form"
- **training_log_epoch.csv มีแค่ 4 epoch** (epoch 1-4 จบสมบูรณ์; epoch 5 ถูกขัดกลางคัน) ส่วน per-step log (`training_log.csv`) มีแถว epoch-5 ถึง step 744,700

---

## ส่วนที่ 8: เทียบกับรายงาน composition ก่อนหน้า

| Dataset | เดิม (MOSA sample) | ปัจจุบัน |
|---|---|---|
| MOSA | 15 ไฟล์ / 36.29 นาที | **465 ไฟล์ / 1144.27 นาที** (+450 ไฟล์ / +1107.98 นาที) |
| MusicNet | 126 ไฟล์ / 875.03 นาที | **126 ไฟล์ / 875.03 นาที** (เท่าเดิมระดับ manifest; trainer ใช้ 9 จาก 114 train ภายใต้ Option B) |

ยืนยัน: MOSA เพิ่มมากตามคาด (extract MOSA-full จาก Zenodo 11393449 หลัง phase ก่อน) manifest MusicNet เหมือนเดิมเป๊ะ; Option B เป็นการเลือกตอนเทรนไม่เปลี่ยน manifest

---

## ส่วนที่ 9: ที่มาของโค้ด

`build_composition_matrix.py` แก้ล่าสุด 2026-05-20 16:37 (หลัง provenance เก่า 2026-05-18) ตาราง 8 ขั้น regenerate จาก source ปัจจุบัน:

| ขั้น | จุดประสงค์ | ฟังก์ชัน | file:line |
|------|---------|-------------|-----------|
| 3.1 | สำรวจ + วัดความยาว WAV ด้วย `soundfile.info` | `scan_mosa`/`scan_musicnet`/`_wav_duration` | `:36`, `:109`, `:31` |
| 3.2 | กรองไวโอลิน - MusicNet ตัดถ้าไม่มี `instrument==41`; MOSA กรอง ev/yv ต้นทาง | `_musicnet_label_uses_violin` | `:91` |
| 3.3 | ตรวจมี annotation F0 - MOSA ต้องมี `notes/<stem>.csv`; MusicNet ต้องมี label CSV | ใน `scan_mosa`/`scan_musicnet` | `:47`, `:128` |
| 3.4 | กำหนด group-id - MOSA `{performer}_{piece}`; MusicNet ตาม recording id | ใน `scan_mosa`/`scan_musicnet` | `:52-58`, `:140-150` |
| 3.5 | แบ่ง 10 set แบบ group-aware (seed 42); set_10 = TEST, 1-9 = TRAIN | `split_into_sets` | `:163` |
| 3.6 | เขียน manifest (8 คอลัมน์) | `write_manifest` | `:209` |
| 3.7 | คำนวณสถิติ → `set_statistics.md` | `write_set_stats` | `:221` |
| 3.8 | เขียน composition matrix | `write_matrix` | `:246` |

เทียบกับ provenance 18 พ.ค.: ไม่เปลี่ยน algorithm (แก้ 20 พ.ค. เป็น refactor/rename) ผลนับไฟล์เท่าเดิมเป๊ะ; สคริปต์นี้**ไม่**ทำ Option B - Option B อยู่ใน `build_train_prepared.py` + `prepare_musicnet_violin.py` (ทั้งคู่ใหม่; ดูส่วนที่ 7)
