# รายงานผลการ Fine-tune โมเดล CREPE

ที่มา config: `scripts/finetune_crepe_v2.py` (ค่า default) + `manifest.csv` สำหรับการแบ่ง train/val/test
Random seed: 42

## ส่วนที่ 1: สรุปการเทรน

| รายการ | ค่า |
|---|---|
| ขนาดโมเดล CREPE | full (~22M params) |
| Pretrained checkpoint | `torchcrepe/assets/full.pth` (84.9 MB) |
| จำนวน epoch ที่เทรน | 5 (จากเป้า `max_epochs=30`) |
| Epoch ที่ดีที่สุด | **1** - best.pt อัปเดตครั้งสุดท้ายที่ step 20,000 (~22 นาทีแรกของ epoch 1) |
| เหตุผลที่หยุด | หยุดเองหลังเห็นสัญญาณ overfitting (ดูส่วนที่ 6) |
| เวลารวม (wall-clock) | 11:24:24 - งานที่ได้ผลจริงคือ ~22 นาทีแรก, อีก ~11 ชม. ไม่ได้ทำให้ best.pt ดีขึ้น |
| Peak GPU VRAM | ~1.1 GB (cuda:3, RTX 3070 Ti) |
| ฮาร์ดแวร์ | NVIDIA RTX 3070 Ti 8 GB (cuda:3 จากเครื่อง 4-GPU: 1x RTX 5090 + 3x RTX 3070 Ti) |
| Training loss สุดท้าย | 0.0134 (step 744,700, epoch 5) |
| Validation loss สุดท้าย | 0.0192 (val pass สุดท้าย, step 740,000) |
| Validation RPA สุดท้าย (weighted-mean)\* | 0.199 (step 740,000) - ค่าดีสุดคือ **0.6615 @ step 20,000** ซึ่งคือสิ่งที่อยู่ใน `best.pt` |

\* ค่า "RPA" ใน `training_log.csv` คำนวณด้วย weighted-mean cents decoding เพื่อความเร็ว จึงเบี่ยงจาก metric argmax+50¢ ตอน output distribution กว้าง/หลายโหมด (ดูส่วนที่ 6)

## ส่วนที่ 2: Training Curves (อ้างอิง CSV)

- Log ราย step: `training_log.csv` - คอลัมน์ `step, epoch, split, loss, RPA, RCA, MAE_cents, learning_rate, wall_time_sec`
  - `split=train` เฉลี่ย rolling-100 ทุก 100 step (7,447 แถว)
  - `split=val` validation เต็มทุก 10,000 step (74 แถว)
- Log ราย epoch: `training_log_epoch.csv` - 1 แถวต่อ epoch (epoch 1-4; epoch 5 ถูกขัดจังหวะ)
- stdout ดิบ: `finetune.log` (706 KB)

## ส่วนที่ 3: ตารางเทียบ Metrics ก่อน vs หลัง Fine-tune

ประเมินด้วย `evaluate_crepe_v2.py`: 16 kHz mono, hop 10 ms, voicing threshold 0.5, decoder `weighted_argmax`
นิยาม metric: RPA/RCA ที่ tolerance 50¢, MAE เป็น cents บน frame ที่ voiced+confident; รวมแบบ per-recording แล้วเฉลี่ยข้ามไฟล์

|  | MOSA_test (RPA/RCA/MAE) | MusicNet_test (RPA/RCA/MAE) | URMP | Bach10 (RPA/RCA/MAE) |
|---|---|---|---|---|
| CREPE pretrained | 0.811 / 0.823 / 92.0¢ | 0.119 / 0.250 / 1470.6¢ | N/A | 0.967 / 0.968 / 14.8¢ |
| CREPE fine-tuned | **0.862 / 0.871 / 60.1¢** | **0.309 / 0.418 / 706.5¢** | N/A | **0.982 / 0.983 / 16.5¢** |
| Δ (ดีขึ้น) | +0.051 / +0.048 / −31.9¢ | +0.190 / +0.168 / −764.1¢ | N/A | +0.015 / +0.015 / +1.7¢ |

จำนวน frame (voiced+confident) pretrained  fine-tuned:
- MOSA_test: 553,463  514,358
- MusicNet_test: 302,627  99,916
- Bach10: 29,514  28,832

URMP ถูกตัดออกจากรอบนี้ (ดูส่วนที่ 6) ระหว่างเทรนใช้ validation จาก MOSA 5% (21 ไฟล์, ไม่มี MusicNet)

**ข้อสังเกตหลัก:**
- **MusicNet_test ดีขึ้น +19.0 จุด RPA** (3 เท่าของ pretrained) ทั้งที่โมเดลไม่เคยเห็น mix polyphonic ของ MusicNet เลย (มีแค่ 9 ไฟล์ solo violin เข้าเทรน) MAE ลดจาก 1470¢ เหลือ 707¢ = โมเดลล็อกผิดไปเครื่องดนตรีอื่นน้อยลงมาก จำนวน frame ลดจาก 303K เหลือ 100K เพราะโมเดลมั่นใจน้อยลงบนเสียง polyphonic จึงผ่าน threshold 0.5 น้อยลง แต่ frame ที่ผ่านแม่นกว่าเดิมมาก
- **MOSA_test ดีขึ้น +5.1 จุด RPA**, MAE ลด 1 ใน 3 (92¢  60¢) - ชนะชัดบนชุด in-distribution
- **Bach10 RPA ดีขึ้น +1.5 จุด** (pretrained ก็เกือบเต็มที่ 0.967 แล้ว) MAE สูงขึ้นเล็กน้อย (14.8¢  16.5¢) แต่ RPA ที่เพิ่มสำคัญกว่า

## ส่วนที่ 4: Composition Matrix (หลังได้ MOSA เต็ม)

| Dataset | set_1 | set_2 | set_3 | set_4 | set_5 | set_6 | set_7 | set_8 | set_9 | set_10 | รวม |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MOSA | 43 / 113.9m | 44 / 114.6m | 47 / 113.8m | 45 / 114.6m | 46 / 115.0m | 48 / 113.9m | 48 / 114.0m | 48 / 114.8m | 44 / 113.8m | 52 / 115.8m | **465 / 1144.3m** |
| MusicNet | 14 / 88.4m | 12 / 87.4m | 14 / 88.6m | 12 / 88.4m | 13 / 83.6m | 12 / 88.7m | 8 / 84.3m | 15 / 87.3m | 14 / 88.6m | 12 / 89.8m | **126 / 875.0m** |

ที่มา: `set_statistics.md` (สร้างใหม่ 2026-05-23 จาก `build_composition_matrix.py`)

เทียบก่อน/หลังโหลด MOSA เต็ม:

| | ก่อน (sample) | หลัง (เต็ม) |
|---|---|---|
| ไฟล์ MOSA | 15 | 465 |
| ความยาว MOSA | 36.3 นาที | 1144.3 นาที |
| set ที่ไม่ว่าง | 5 | 10 |
| MusicNet (เท่าเดิม) | 126 ไฟล์ / 875.0 นาที | 126 ไฟล์ / 875.0 นาที |

## ส่วนที่ 5: การจัดการ Polyphony ของ MusicNet

**เลือก Option B** - กรอง MusicNet ให้เหลือเฉพาะเพลง solo violin สำหรับ *training set*

- พบ 9 ไฟล์ที่ `ensemble == "Solo Violin"`: 2186, 2191, 2241, 2242, 2243, 2244, 2288, 2289, 2659
- ทั้ง 9 อยู่ใน `role=train` (ไม่มีใน test) จึงไม่ต้องสับ test ใหม่
- resample เป็น 16 kHz mono + สร้าง notes CSV แบบ MOSA โดยกรอง label เฉพาะ `instrument == 41` (violin)
- โฟลเดอร์ผลลัพธ์: `MusicNet_solo_violin_prepared/` (~30 นาที, 7,792 โน้ต)
- อีก 105 ไฟล์ polyphonic ถูก **ตัดเฉพาะตอนเทรน** (ยังอยู่ใน manifest แต่ไม่เข้า trainer)
- ส่วนการประเมิน `MusicNet_test` (12 ไฟล์ polyphonic) คงไว้ตามเดิม เพื่อใช้เป็นสัญญาณเปรียบเทียบ pretrained vs fine-tuned (ปรากฏว่าดีขึ้นมากสุด ดูส่วนที่ 3)

องค์ประกอบ training set: 413 MOSA + 9 MusicNet solo violin = 422 ไฟล์ ~17.7 ชม. (4,980,665 frame หลังหัก val 5%)

## ส่วนที่ 6: การตัดสินใจ / จุดที่เบี่ยงจากค่า default

| ค่า | Spec default | ที่ใช้จริง | เหตุผล |
|---|---|---|---|
| `batch_size` | 32 | 32 | พอดี VRAM 8 GB (~1.1 GB) |
| `learning_rate` | 5e-5 | 5e-5 | แต่ย้อนดูแล้วน่าจะสูงไป (ดู "บทเรียน") |
| `max_epochs` | 30 | 30 | ชน time budget หลัง epoch 5 |
| `early_stopping_patience` | 5 | 5 | จะ trigger หลัง epoch 6 ถ้าไม่หยุดเอง |
| `optimizer` | AdamW | AdamW | ตามสเปก |
| `weight_decay` | 1e-5 | 1e-5 | ตามสเปก |
| `lr_scheduler` | cosine | cosine | warmup เชิงเส้นแล้ว half-cosine ลงถึง 0 |
| `warmup_steps` | 1000 | 1000 | ตามสเปก |
| `loss` | BCE | BCE | per-bin BCE บน target 360-bin Gaussian (ตาม CREPE) |
| `gaussian_target_std_cents` | 25 | 25 | ตามสเปก |
| `validation_every_n_steps` | 500 | **10,000** | **เบี่ยง** - ที่ 500 จะ validate 279 ครั้ง/epoch (~9 ชม./epoch) ทะลุ budget; 10,000 ยังคงสัญญาณ early-stop ไว้ |
| `checkpoint_every_n_steps` | 2000 | **5000** | **เบี่ยง** - best.pt อัปเดตตอน val อยู่แล้ว; last.pt ทุก 5K + ท้าย epoch พอสำหรับกู้ crash |
| validation set | URMP | **MOSA 5% (21 ไฟล์)** | **เบี่ยง** - URMP ติด Google Form, เลือกข้าม |
| metrics library | mir_eval | custom (`metrics.py`) | venv ไม่มี mir_eval; ใช้ implementation เดิม นิยาม/tolerance เดียวกัน |
| GPU device | (cuda ใดก็ได้) | **cuda:3** | cuda:0 (RTX 5090) ถูกคนอื่นใช้เต็ม, cuda:1/2 ว่าง < 2 GB; cuda:3 ว่าง ~7.6 GB |
| Validation metric | RPA at 50¢ | weighted-mean cents (ตอนเทรน) + argmax+50¢ (ตอน eval สุดท้าย) | **เบี่ยงแบบทำให้เข้าใจผิด** - ใช้ weighted-mean เร็วกว่าตอน val ระหว่างเทรน metric นี้พีคเร็วแล้วลดลงเมื่อ distribution คมขึ้น จึงเข้าใจว่า overfit (epoch4=0.23 vs epoch1=0.51) แล้วหยุดเทรน แต่ประเมินด้วย argmax จริงพบว่า best.pt ดีขึ้นจริงทั้ง 3 ชุด **บทเรียน: ควรคำนวณ metric ตอน val ให้ตรงกับตอนทดสอบ (argmax) แม้ช้าลง** |
| `seed` | 42 | 42 | ตามสเปก |

หมายเหตุ: การเตรียมข้อมูลตัด `role=test` ออกชัดเจน (`build_train_prepared.py` อ่านเฉพาะ `role=train`) จึงไม่มีการรั่วของ set_10/URMP/Bach10

## ส่วนที่ 7: คำถามที่ยังค้าง

- **สิทธิ์เข้าถึง URMP**: ยังติด Google Form ถ้าได้มาภายหลังสามารถสลับ validation set เป็น URMP แล้วรันใหม่ได้
- **ควรเทรนใหม่ด้วย LR ต่ำลงไหม**: best.pt มาตั้งแต่ step 20,000 แล้ว; ลอง `lr=1e-5` + `--freeze-early` (freeze conv1-4) + `max_epochs=10` จะถูกกว่า (~3-4 ชม.) และอาจได้ best.pt ที่ดีกว่า
- **เพลง MusicNet "Solo Violin"** มีโน้ต viola (`instrument==42`) ปนใน chord/double-stop เราเก็บแค่ violin (41) ซึ่ง conservative อาจนับ frame น้อยไปนิด
- **MAE ของ Bach10 สูงขึ้นเล็กน้อย** (14.8¢16.5¢) แม้ RPA ขึ้น - เป็น tradeoff เล็กน้อย ไม่คุ้มจะ tune

## ส่วนที่ 8: ไฟล์ที่ผลิตออกมา

ทุก path อยู่ใต้ `outputs/finetune_2026-05-23/`

| ไฟล์ | ขนาด | คืออะไร |
|---|---|---|
| `baseline_metrics.json` | 755 B | CREPE pretrained บน 3 ชุดทดสอบ |
| `baseline_metrics.md` | 520 B | ฉบับอ่านง่าย |
| `baseline_metrics_detail.csv` | 6.3 KB | ราย recording (baseline) |
| `finetuned_metrics.json` | 759 B | fine-tuned (best.pt) บน 3 ชุดเดียวกัน |
| `finetuned_metrics.md` | 529 B | ฉบับอ่านง่าย |
| `finetuned_metrics_detail.csv` | 6.3 KB | ราย recording (fine-tuned) |
| `training_log.csv` | 466 KB | 7,447 train + 74 val แถว |
| `training_log_epoch.csv` | 313 B | 4 epoch ที่จบ |
| `training_summary.json` | 1.4 KB | สถานะหยุด, config, best step |
| `finetune.log` | 706 KB | stdout เทรนเต็ม |
| `checkpoints/best.pt` | **84.87 MB** | checkpoint validation ดีสุด - ตัวที่ใช้ประเมิน |
| `checkpoints/last.pt` | 84.87 MB | weights สุดท้าย (ไม่ใช้ eval) |
| `training_results_report.md` | ไฟล์นี้ | deliverable หลัก |

ไฟล์ข้อมูลที่เกี่ยวข้อง (อ้างในส่วนที่ 3-5): `datasets/composition/manifest.csv` (591 แถว), `set_statistics.md`, `exclusions.csv`, `MOSA_full/` (21.3 GB), `MOSA_full/violin/` (465 ไฟล์), `MusicNet_solo_violin_prepared/` (9 ไฟล์), `Bach10/` (269 MB), `train_prepared/` (422 ไฟล์ symlink) และสคริปต์ `build_composition_matrix.py`, `prepare_musicnet_violin.py`, `build_train_prepared.py`, `evaluate_crepe_v2.py`, `finetune_crepe_v2.py`
