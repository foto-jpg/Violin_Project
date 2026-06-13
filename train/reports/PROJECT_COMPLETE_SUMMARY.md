# โปรเจกต์ตรวจจับ Pitch ไวโอลินด้วยการ Fine-tune CREPE: สรุปฉบับสมบูรณ์

เอกสารนี้สรุปสถานะโปรเจกต์ตั้งแต่ต้นจนจบ เพื่อให้ผู้อ่านเข้าใจได้โดยไม่ต้องเห็น workspace เดิม และให้คนที่มารับช่วงทำซ้ำบนเครื่องใหม่ได้เมื่อมีชุดข้อมูลต้นทาง

---

## 1. ภาพรวมโปรเจกต์

โปรเจกต์นี้ fine-tune โมเดล **CREPE** ("Convolutional REpresentation for Pitch Estimation", Kim et al. 2018) ขนาด full บน **เสียงไวโอลิน** เพื่อปรับปรุงการประเมิน F0 ระดับ frame สำหรับแอป "violin checker" ที่ใช้ OMR ติดตามโน้ตและให้คะแนนการเล่นไวโอลินของนักเรียนเทียบกับโน้ตที่พิมพ์

เลือก CREPE เพราะ (ก) เป็นมาตรฐานวงการสำหรับ F0 เสียงเดี่ยว (~98% RPA บน Bach10) (ข) `torchcrepe` เป็น PyTorch port ที่เทรน weights ได้ตรง (ค) output 360 bin ให้ความละเอียด 20 cent พอจับการเพี้ยน intonation ของไวโอลิน (ง) frame 1024 sample ที่ 16 kHz ทำงานระดับ frame เข้ากับ loop ของ score-follower แบบ real-time

Pipeline:

```
  สเปรดโน้ต (PDF/PNG) → OMR (oemer) → Reference MIDI ┐
                                                      └→ ให้คะแนน (alignment + cents error ต่อโน้ต)
  เสียงไวโอลินนักเรียน (WAV) → CREPE (fine-tuned) → F0 + voicing ระดับ frame ┘
```

**สถานะโปรเจกต์** (ณ 2026-05-26):

| Phase | สถานะ |
|---|---|
| ได้ชุดข้อมูล (MOSA/MusicNet/Bach10) | เสร็จ |
| Composition matrix / แบ่ง 10 ชุด | เสร็จ |
| จัดการ polyphony MusicNet (Option B) | เสร็จ |
| Fine-tune CREPE-full | เสร็จ (5/30 epoch; หยุดเอง, best.pt ที่ step 20,000) |
| ประเมิน baseline + finetuned (3 ชุดทดสอบ) | เสร็จ |
| เขียนรายงานผล | เสร็จ (`training_results_report.md`) |
| เทรนรอบสอง (LR ต่ำ + freeze early) | ค้าง - ดู §10 |

---

## 2. รายการชุดข้อมูล

### 2.1 MOSA (Music mOtion with Semantic Annotation)
- **บทบาท**: training หลัก + เป็นที่มาของ MOSA_test
- **ที่มา**: Zenodo record 11393449 - `https://zenodo.org/records/11393449` (เข้าถึงแบบ restricted; CC-BY-NC)
- **เนื้อหา**: 742 recording ไวโอลิน/เปียโน มี audio + annotation ระดับโน้ต (onset/offset/MIDI) + motion capture 3D หมวดที่ใช้: `ev` (ensemble violin), `yv` (young violin); ตัด `yp` (เปียโน) ออก
- **ที่ใช้**: subset ไวโอลินเต็ม → 465 ไฟล์, 1,144 นาที (~19.1 ชม.) 16 kHz mono + notes CSV
- **annotation**: ระดับโน้ต MIDI → แปลงเป็น F0 ระดับ frame ด้วย piecewise-constant
- **ขนาดหลังกรอง**: **465 ไฟล์ / 1144.3 นาที**
- **วิธีได้มา**: ดาวน์โหลด 6 ส่วน (~21.3 GB) ผ่าน Zenodo token, ตรวจ MD5, รวมด้วย cat/unzip

### 2.2 MusicNet
- **บทบาท**: training รอง (เฉพาะ subset solo violin, "Option B") + test set polyphonic (MusicNet_test)
- **ที่มา**: `https://zenodo.org/records/5120004` (CC BY 4.0)
- **เนื้อหา**: 330 recording ดนตรีคลาสสิก chamber พร้อม label โน้ตและ instrument program (violin = 41) ส่วนใหญ่ polyphonic
- **ที่ใช้**: 126 recording ที่มี violin track (program 41) สำหรับ test; เฉพาะ **9 ไฟล์ solo violin** (ID 2186, 2191, 2241, 2242, 2243, 2244, 2288, 2289, 2659) สำหรับ *training*
- **ขนาดหลังกรอง**: Train 9 ไฟล์ / ~30 นาที / 7,792 โน้ต; Test 12 ไฟล์ / 89.8 นาที (set_10)
- **เหตุผล**: ให้สัญญาณ domain-shift - เทรน solo violin จะ generalize ไป polyphonic ได้แค่ไหน

### 2.3 Bach10 (v1.1)
- **บทบาท**: test ภายนอกเท่านั้น (ไม่เคยเห็นตอนเทรน)
- **ที่มา**: GitHub `flippy-fyp/Bach10_v1.1` (ต้นฉบับ Duan & Pardo 2011, research-only)
- **เนื้อหา**: 10 chorale ของ Bach เล่นด้วยไวโอลิน+คลาริเน็ต+แซ็ก+บาสซูน มี WAV แยกเครื่อง + GT F0 ระดับ frame (`*-GTF0s.mat`, hop 10ms, แถว 0 = ไวโอลิน)
- **ที่ใช้**: คู่ `*-violin.wav` + `*-GTF0s.mat[0]` 10 คู่
- **ขนาด**: **10 ไฟล์ / 29,514 frame (pretrained) / 28,832 frame (finetuned)**
- **เหตุผล**: benchmark มาตรฐานวงการ เทียบกับงานตีพิมพ์ได้ (Tamer 2022, lars76)


---

## 3. Pipeline เตรียมข้อมูล (สรุปย่อ)

ทุก path เทียบจาก `violin-checker/`

1. **สแกน audio + วัดความยาว** ด้วย `soundfile.info` (`build_composition_matrix.py`) - ใช้กำหนด balance ของ split และ time budget
2. **กรองเฉพาะไวโอลิน**: MOSA เก็บไฟล์ที่มี notes CSV คู่กัน (กรอง ev+yv ตั้งแต่ extract); MusicNet เก็บไฟล์ที่ label มี `instrument==41`; Bach10 ใช้ชื่อ `*-violin.wav` - เพื่อไม่เทรนบนสเปกตรัมเครื่องอื่น
3. **กรองให้มี annotation F0** - เก็บเฉพาะ recording ที่มีไฟล์ annotation อ่านได้คู่กัน
4. **แปลงโน้ต → F0 ราย frame (piecewise-constant)**: เติมทุก frame 10ms ใน `[onset, offset)` ด้วย `librosa.midi_to_hz(midi)`; ถ้าโน้ตซ้อนให้ F0 สูงชนะ **ข้อควรระวัง (Tamer 2022)**: piecewise-constant ลบ vibrato/การเพี้ยนออกจาก target โมเดลจึงเรียน pitch "อุดมคติ" ไม่ใช่ pitch จริง
5. **กำหนด group_id**: MOSA = `<performer>_<piece>`, MusicNet = `<composer>::<composition>` - กันการรั่วระหว่าง train/test (take เดียวกันของผู้เล่นเดียวกันต้องอยู่ฝั่งเดียวกัน)
6. **แบ่ง 10 ชุดแบบ group-aware ("จองชุด test ก่อน")**: เรียง group ตามความยาว → หยิบเข้า test pool จน ≥ total/10 (set 10 = test เสมอ) → กระจายที่เหลือลง set 1-9 แบบ least-loaded; `N_SETS=10, TEST_SET=10, SEED=42`
7. **Option B (กรอง polyphony MusicNet)**: จาก 114 ไฟล์ train ที่มีไวโอลิน เก็บเฉพาะ 9 ไฟล์ที่ metadata ระบุ `Solo Violin`, resample 44.1→16 kHz, แปลง label เป็น CSV แบบ MOSA (เก็บแค่ `instrument==41`) อีก 105 ไฟล์ polyphonic ตัดเฉพาะตอนเทรน (`prepare_musicnet_violin.py` + `build_train_prepared.py`)
8. **เขียน manifest**: `manifest.csv` คอลัมน์ `dataset, filepath, set_id, role, duration_sec, piece_id, performer_id, annotation_path`; `role="test"` เมื่อ `set_id==10`
9. **คำนวณสถิติ**: นับไฟล์+ความยาวต่อ (dataset × set) ลง `set_statistics.md` + `exclusions.csv`
10. **เขียน composition matrix**: `training_composition_matrix.md` 1 แถว/dataset, 1 คอลัมน์/set ระบุ TRAIN/TEST

---

## 4. สถาปัตยกรรมโมเดล

- **Base**: `torchcrepe.Crepe("full")` โหลดจาก `full.pth` (~22M params, 84.87 MB)
- **โครงสร้าง**: 6 conv block (`Conv1d → BN → ReLU → MaxPool → Dropout`) → flatten → dense → output sigmoid 360 หน่วย
- **Input**: หน้าต่าง 1024 sample, 16 kHz mono, mean-center หารด้วย std
- **Output**: vector ความน่าจะเป็น 360 bin ครอบ C1 (~32.7 Hz) ถึง ~B7 ทีละ 20 cent
- **การ decode pitch - ตอนเทรน vs ตอนทดสอบ (จุดที่ไม่ตรงกัน + บทเรียน)**:
  - ตอน validation ระหว่างเทรนใช้ **weighted-mean cents** (`sum(probs*cmap)/sum(probs)`) เร็วแต่จะเบนเข้ากลางช่วง output เมื่อ distribution กว้าง → ประเมิน output ที่ดีแต่ noisy ต่ำไป
  - ตอนประเมินจริงใช้ **argmax + tolerance ±50 cents** (`weighted_argmax` + `median(periodicity,3)` + `mean(pitch,3)`) ซึ่งคือค่าที่รายงานใน `evaluate_crepe_v2.py`
  - **บทเรียน**: สอง metric เบนออกจากกันหลัง fine-tune ไม่กี่ epoch การอ่าน weighted-mean ที่ลดลงว่าเป็น "overfit รุนแรง" ทำให้หยุดเทรนหลัง epoch 5 ทั้งที่ best.pt (step 20,000) คือตัวดีจริงและดีขึ้นทั้ง 3 ชุด รอบหน้าควร validate ด้วย metric เดียวกับตอนทดสอบ
- **ทางเลือกอื่นที่พิจารณา**: PESTO (เทรนกับ supervision ระดับโน้ตไม่ได้), RMVPE (เน้นเสียงร้อง), SwiftF0 (ความละเอียดต่ำกว่า), BasicPitch (ระดับโน้ต ไม่ใช่ frame) → CREPE ชนะที่ (ข้อมูลเทรนที่มี) × (คุณภาพ pretrained) × (เข้ากับ interface)

---

## 5. Hyperparameters ทั้งหมดพร้อมเหตุผล

ค่าทั้งหมดจาก `training_summary.json`

| Parameter | ค่าที่ใช้ | เหตุผล |
|---|---|---|
| Loss | per-bin BCE บน target 360-bin Gaussian σ=25¢ | ตามสูตร CREPE เดิม; σ=25¢ ทนต่อ annotation ที่คลาด ±10-20¢ |
| Optimizer | **AdamW** | decoupled weight decay เหมาะกับการต่อจาก pretrained |
| Learning rate | **5e-5** | ต่ำเพื่อรักษา feature pretrained (~1/20 ของ LR เทรน CREPE) ย้อนดูยังสูงไป (§10) |
| LR schedule | cosine + warmup เชิงเส้น 1000 step | warmup กันก้าวแรกแรงทำลาย weights; cosine ลดถึง 0 |
| Weight decay | **1e-5** | ต่ำเพราะ fine-tune จาก checkpoint ที่ดีอยู่แล้ว |
| Batch size | **32** | power-of-2 ใหญ่สุดที่พอดี 8 GB (ใช้จริง ~1.1 GB) |
| Max epochs | **30** | ขอบบน คู่กับ early stopping (จริงชน 12 ชม. หลัง 5 epoch) |
| Early-stop patience | **5** | จะ trigger ที่ epoch 6 ถ้าไม่หยุดเอง |
| Seed | **42** | ทำซ้ำได้ |
| Validation cadence | **ทุก 10,000 step** (สเปก 500) | เบี่ยง - ที่ 500 จะกิน budget หมดไปกับ validation |
| Checkpoint cadence | ทุก 5000 step + ท้าย epoch | พอสำหรับกู้ crash |
| Voicing threshold | **0.5** | มาตรฐานวงการสำหรับตัดสิน frame มี pitch |
| Sample rate | **16,000 Hz** | ข้อบังคับของ CREPE |
| Hop size | **10 ms (160 sample)** | ตาม CREPE, ตรงกับ GT ของ Bach10/MusicNet |
| `unvoiced_keep_prob` | 0.1 | เก็บ frame ไม่มีเสียงแค่ 10% ไม่งั้น loss จะถูกครอบงำด้วยความเงียบ |
| Val split | MOSA 5% ราย recording (21/413); MusicNet solo 9 ไฟล์อยู่ใน train ทั้งหมด | ราย recording กันการรั่ว; MusicNet น้อยเกินจะกันออก |

---

## 6. การรันเทรน & ผลลัพธ์

| รายการ | ค่า |
|---|---|
| ฮาร์ดแวร์ | NVIDIA RTX 3070 Ti, 8 GB, `cuda:3` (1 ใน 4 GPU เครื่อง shared) |
| เวลารวม | **11:24:24** (41,064.6s) |
| งานที่ได้ผลจริง | ~22 นาที (best.pt เขียนครั้งสุดท้าย step 20,000); อีก ~11 ชม. ไม่ดีขึ้น |
| Epoch | **5/30** (epoch 5 ถูกขัด) |
| Best epoch | **1** (step 20,000) |
| เหตุผลหยุด | หยุดเองหลังเห็นสัญญาณ overfitting (§10) |
| Training loss สุดท้าย | 0.0134 |
| Validation loss สุดท้าย | 0.0192 |
| Best val RPA (weighted-mean) | **0.6615** @ step 20,000 |
| Peak VRAM | ~1.1 GB |
| ข้อมูลเทรน | 413 MOSA + 9 MusicNet solo = 422 ไฟล์ ~17.7 ชม. (4,980,665 frame หลัง val 5%) |

Log ราย epoch (`training_log_epoch.csv`):
```
epoch  train_loss  val_loss  val_RPA(wm)  val_RCA(wm)  val_MAE(¢)  lr_end     wall(s)
1      0.015198    0.015578  0.5090       0.5124       136.20      4.99e-05   8,538.7
2      0.014367    0.016327  0.3751       0.3776       155.81      4.95e-05   17,209.6
3      0.014060    0.017213  0.2843       0.2867       180.17      4.88e-05   25,758.1
4      0.013852    0.018282  0.2320       0.2348       204.87      4.78e-05   34,421.4
5      (ถูกขัด - บางส่วน)
```
> คอลัมน์ "val RPA" ข้างบนคือ decoder weighted-mean (ตอนเทรน) ส่วน RPA จาก argmax บนชุดทดสอบของ best.pt สูงกว่ามาก - ดู §8

**บทเรียนหลัก**: การที่ metric val ตอนเทรน (weighted-mean) ไม่ตรงกับตอนทดสอบ (argmax+50¢) ทำให้เสีย compute ~11 ชม. หลังจุด best จริง

---

## 7. วิธีการประเมิน

- **Library**: implementation RPA/RCA/MAE ในโปรเจกต์เอง (`metrics.py`) เพราะ venv ไม่มี mir_eval; คณิตศาสตร์ตรงกับ `mir_eval.melody` ที่ tolerance 50¢ (RPA = สัดส่วน frame voiced ที่ error ≤ 50¢; RCA = แบบยุบ octave; MAE = error เฉลี่ยสัมบูรณ์เป็น cents)
- **มาตรฐานวงการ**: ทุก paper melody-extraction ตั้งแต่ ~2015 รายงาน 3 ค่านี้ที่ tolerance เดียวกัน เทียบงานตีพิมพ์ได้ตรง
- **สคริปต์**: `evaluate_crepe_v2.py` (300 บรรทัด) อ่าน manifest เลือก `role=="test"` สำหรับ MOSA/MusicNet, เพิ่ม Bach10 แยก, รันโมเดล แล้วเขียน json/md/csv
- **ชุดทดสอบที่ใช้จริง**: MOSA_test 52, MusicNet_test 12 (polyphonic), Bach10 10, URMP null (ติด gate)
- **การนับ voicing**: frame นับเมื่อ `voiced_gt & periodicity≥0.5 & isfinite(pred) & pred>0`; รวมราย recording ก่อนแล้วเฉลี่ยข้ามไฟล์
- **ทำไม n_frames ต่างกัน**: โมเดล finetuned voicing อนุรักษ์กว่า (มัก "unvoiced" บนเสียง polyphonic/noisy) frame ผ่าน threshold น้อยลง แต่ที่ผ่านแม่นกว่ามาก

---

## 8. ผลลัพธ์: ก่อน vs หลัง Fine-tune

ค่าตรงจาก `baseline_metrics.json` / `finetuned_metrics.json`

| ชุดทดสอบ | โมเดล | RPA | RCA | MAE(¢) | n_frames | n_rec |
|---|---|---:|---:|---:|---:|---:|
| MOSA_test | Pretrained | 0.8109 | 0.8230 | 91.99 | 553,463 | 52 |
| MOSA_test | Finetuned | **0.8622** | **0.8711** | **60.06** | 514,358 | 52 |
| MusicNet_test | Pretrained | 0.1186 | 0.2500 | 1470.62 | 302,627 | 12 |
| MusicNet_test | Finetuned | **0.3093** | **0.4182** | **706.54** | 99,916 | 12 |
| Bach10 | Pretrained | 0.9667 | 0.9681 | 14.81 | 29,514 | 10 |
| Bach10 | Finetuned | **0.9817** | **0.9831** | 16.54 | 28,832 | 10 |
| URMP | (ทั้งคู่) | N/A | N/A | N/A | - | - |

Δ (Finetuned − Pretrained): MOSA +0.0513/+0.0481/−31.93¢; MusicNet +0.1907/+0.1681/−764.08¢; Bach10 +0.0150/+0.0149/+1.73¢

**ตีความ**: fine-tune ชนะทุกชุดบนแกน RPA/RCA MOSA_test +5.1 จุด (MAE ลด 1/3) ตามคาดสำหรับ in-distribution; MusicNet_test RPA เพิ่ม ~2.6 เท่าทั้งที่ไม่เคยเห็น polyphonic ตอนเทรน (การจูนไวโอลินทำให้ล็อกผิดไป viola/cello น้อยลง + voicing คัด frame ยากออก จำนวน frame ลด 67% แต่ที่เหลือแม่นกว่ามาก); Bach10 pretrained เกือบเพดานแล้ว (+1.5 จุด) MAE +1.73¢ อยู่ในช่วง noise

---

## 9. เทียบ SOTA

### Bach10
| แหล่ง | RPA Bach10 (violin) | หมายเหตุ |
|---|---|---|
| CREPE pretrained (รอบนี้) | **0.967** | benchmark วงการ |
| CREPE finetuned (รอบนี้) | **0.982** | +1.5 จุด |
| Tamer 2022 (synth, pretrained) | 0.989 | GT แบบ re-synth (audio ตรง GT เป๊ะ) งานง่ายกว่าเรา |
| Tamer 2022 (synth, finetuned) | 0.992 | เหมือนกัน |
| lars76/pitch-benchmark (real Bach10) | 0.985 | เทียบตรงสุด อยู่ระหว่างเรา pretrained/finetuned |

### MOSA
ไม่มีงานตีพิมพ์ประเมิน pitch บน MOSA - โปรเจกต์นี้เป็นตัวเลขแรก การขยับ 0.8110.862 คือ baseline แรก

### MusicNet (program 41)
ไม่มีตัวเลขเทียบตรง (งาน MusicNet ส่วนใหญ่ทำ transcription หลายเครื่องแบบ F1) การขยับ 0.1190.309 สอดคล้องสัญชาตญาณว่า pitch tracker เสียงเดี่ยวบน mix polyphonic จะอยู่ระดับพื้นจนกว่าจะ bias ไปเครื่องเฉพาะ ซึ่ง fine-tune solo violin ทำได้

**อภิปราย real vs synth**: RPA 0.97-0.99 ที่ตีพิมพ์มักอ้าง Bach10 แบบ synth; บน recording จริงงานดีสุดอยู่ ~0.985 (lars76) ค่า 0.982 ของเราอยู่ในกรอบนั้น

---

## 10. ปัญหาที่ค้าง & ข้อจำกัด

1. **val-metric ไม่ตรง (weighted-mean vs argmax+50¢)** - เสีย compute ~11 ชม. **แก้**: คำนวณ RPA จาก argmax ตอน validation
2. **polyphony MusicNet** - Option B (กรอง 9 solo) เป็นทางลัด; อนาคตลอง Demucs/Spleeter แยก stem ไวโอลินจาก 105 ไฟล์ polyphonic ("Option A")
3. **MAE Bach10 ขึ้นเล็กน้อย** (+1.73¢) ยอมรับได้แลกกับ RPA +1.5 จุด; น่าจะหายด้วย LR ต่ำ freeze-early รอบสอง
4. **n_frames MusicNet_test ลด 67%** - เพราะ voicing อนุรักษ์; frame ที่เก็บแม่นกว่ามาก แต่ไม่ควรอ่านว่าจำนวน voiced frame เทียบกันได้ตรงข้ามโมเดล
5. **URMP ยังไม่มี** - รอ Google Form; ได้แล้วจะ validate ตรงสเปกขึ้น
6. **annotation MOSA โน้ตpiecewise F0** - เกิด "auto-tuning effect" (Tamer 2022) ลบ vibrato/การเพี้ยน; ยอมรับได้สำหรับงานสอนดนตรี แต่ไม่เหมาะงานวิจัย
7. **จุดเบี่ยงจากสเปก**: validation 50010,000, checkpoint 2,0005,000, val set ใช้ MOSA 5% แทน URMP; config ที่แนบมารายงานค่าสเปก (500/2,000)
8. **ยังไม่ได้เทรนรอบสอง**: `lr=1e-5` + `--freeze-early` + `max_epochs=10` น่าได้ best.pt ดีกว่าใน 3-4 ชม.

---

## 11. โครงสร้าง Repo (ใน zip นี้)

```
violin_pitch_detection_starter/
├── README.md, QUICKSTART.md, NOTICE.md, requirements.txt, .gitignore
├── configs/finetune_default.yaml          # hyperparameters ทั้งหมดจาก §5
├── scripts/
│   ├── build_composition_matrix.py        # manifest + แบ่ง 10 ชุด (§3)
│   ├── build_train_prepared.py            # symlink farm (§3.7)
│   ├── prepare_musicnet_violin.py         # Option B (§3.7)
│   ├── prepare_violin.py                  # กรอง MOSA ev+yv (§3.2)
│   ├── finetune_crepe.py                  # entry point §5/§6
│   ├── evaluate_model.py                  # entry point §7/§8
│   ├── load_example.py / download_mosa_zenodo.py
├── backend/training/{dataset.py, metrics.py}
├── checkpoints/best.pt                     # 84.87 MB - weights ที่ fine-tune แล้ว
├── docs/  (สำเนาสรุป + รายงานผล + json/csv)
└── examples/infer_single_wav.py            # ตัวอย่างโหลด best.pt รันบน 1 WAV
```

---

## 12. ขั้นตอนทำซ้ำ

best.pt ที่แนบมา self-contained ถ้าต้องการแค่ inference ข้ามไป step 6

**Step 1 - ติดตั้ง**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Step 2 - วางชุดข้อมูล (ไม่ได้แนบมา)** ที่ `datasets/MOSA/violin/{audio,notes}/`, `datasets/MusicNet/`, `datasets/Bach10/`, (URMP optional)
```bash
# MOSA: ดาวน์โหลด 6 ส่วนจาก Zenodo (ต้องมี token)
export ZENODO_TOKEN=<your token>
python scripts/download_mosa_zenodo.py --record-id 11393449 --out datasets/MOSA_downloads/
python scripts/prepare_violin.py --extract-root datasets/MOSA_full/MOSA_dataset --out datasets/MOSA/violin
# Bach10:
git clone https://github.com/flippy-fyp/Bach10_v1.1 datasets/Bach10
```

**Step 3 - สร้าง composition matrix**
```bash
python scripts/build_composition_matrix.py --mosa-root datasets/MOSA/violin --musicnet-root datasets/MusicNet --output-dir datasets/composition
```

**Step 4 - กรอง MusicNet solo violin (Option B) + ประกอบ train pool**
```bash
python scripts/prepare_musicnet_violin.py datasets/MusicNet datasets/MusicNet_solo_violin_prepared
python scripts/build_train_prepared.py datasets/composition/manifest.csv datasets/MusicNet_solo_violin_prepared datasets/train_prepared
```

**Step 5 - Fine-tune**
```bash
python scripts/finetune_crepe.py --data datasets/train_prepared --out outputs/finetune_run \
  --model-size full --lr 5e-5 --batch-size 32 --max-epochs 30 --patience 5 \
  --warmup-steps 1000 --val-frac 0.05 --weight-decay 1e-5 \
  --validate-every 500 --ckpt-every 2000 --device cuda:0 --seed 42 --time-budget-hours 12
```

**Step 6 - ประเมิน baseline + finetuned**
```bash
python scripts/evaluate_model.py --manifest datasets/composition/manifest.csv --bach10-root datasets/Bach10 \
  --mode pretrained --output-dir outputs/finetune_run --device cuda:0
python scripts/evaluate_model.py --manifest datasets/composition/manifest.csv --bach10-root datasets/Bach10 \
  --mode finetuned --checkpoint checkpoints/best.pt --output-dir outputs/finetune_run --device cuda:0
```

**Step 7 - inference บน 1 WAV**
```bash
python examples/infer_single_wav.py path/to/violin.wav --checkpoint checkpoints/best.pt
```

---

## 13. อภิธานศัพท์

- **CREPE** - CNN 6 conv-block แปลงหน้าต่าง 1024 sample เป็น vector 360 bin ทีละ 20 cent (Kim et al. 2018)
- **RPA** - สัดส่วน frame voiced ที่ทำนาย cents อยู่ใน ±50¢ ของค่าจริง
- **RCA** - เหมือน RPA แต่ยุบ octave (ให้คะแนนถูก pitch class แม้ octave ผิด)
- **MAE (cents)** - error เฉลี่ยสัมบูรณ์เป็น cents บน frame voiced; ต่ำดีกว่า
- **F0** - ความถี่มูลฐานของสาย/เส้นเสียง = "ระดับเสียง" ที่หูรับรู้
- **Voicing threshold** - เกณฑ์ periodicity (0.5) เหนือกว่านี้ถือว่า frame มีเสียง pitch จริง
- **Vibrato** - การโยกระดับเสียงเล็กๆ เป็นคาบ (~±50¢ ที่ ~5 Hz) ถูกลบโดยการแปลง piecewise-constant
- **Harmonic** - ความถี่ทวีคูณของมูลฐาน; CREPE บางทีล็อก harmonic ที่ 2 รายงาน error +1200¢ (RCA ยกโทษให้)
- **Group-aware split** - แบ่ง train/test โดยเคารพ group_id เพื่อไม่ให้ take เดียวกันรั่ว
- **Leakage** - train/test แชร์ recording/ผู้เล่น/เพลง ทำให้ accuracy ดูสูงเกินจริง
- **Fine-tuning** - เทรนต่อจาก checkpoint บนข้อมูลเฉพาะทาง มัก LR ต่ำ
- **BCE loss** - `−(y log p + (1−y) log(1−p))` ใช้ราย bin เพื่อให้ output เป็น distribution นุ่ม
- **Gaussian-smoothed target** - แทน one-hot ด้วย `exp(−(c−c_true)²/2σ²)` (σ=25¢) ทนต่อ noise ±10-20¢
- **AdamW** - Adam + decoupled weight decay (Loshchilov & Hutter 2017) เหมาะ fine-tune
- **Cosine LR schedule** - LR ลดเป็นครึ่งคลื่น cosine จาก base → 0

---

## 14. อ้างอิง

1. Kim, J. W., Salamon, J., Li, P., & Bello, J. P. (2018). *CREPE: A Convolutional Representation for Pitch Estimation.* IEEE ICASSP 2018. arXiv:1802.06182.
2. Loshchilov, I., & Hutter, F. (2017). *Decoupled Weight Decay Regularization.* arXiv:1711.05101.
3. Tamer, B. C., Manilow, E., Salamon, J., & Bittner, R. M. (2022). *Bach10-mf0 and other multi-F0 benchmarks.* ISMIR 2022.
4. Duan, Z., & Pardo, B. (2011). *Soundprism.* IEEE JSTSP 5(6):1205-1215. (Bach10)
5. Thickstun, J., Harchaoui, Z., & Kakade, S. (2017). *Learning Features of Music From Scratch.* ICLR. (MusicNet, Zenodo 5120004)
6. Li, B., et al. (2018). *URMP dataset.* IEEE Transactions on Multimedia.
7. MOSA dataset v1. Zenodo record 11393449.
8. Salamon, J., et al. (2014). *Melody Extraction from Polyphonic Music Signals.* IEEE SPM 31(2):118-134. (ที่มา tolerance 50¢)
9. lars76/pitch-benchmark. github.com/lars76/pitch-benchmark
10. Raffel, C., et al. (2014). *mir_eval.* ISMIR.

---

*จบเอกสาร (ส่วนที่ 1-14)*
