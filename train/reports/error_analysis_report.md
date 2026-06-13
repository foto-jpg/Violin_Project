# รายงานวิเคราะห์ Error - CREPE หลัง Fine-tune สำหรับตรวจจับ Pitch ไวโอลิน

ไฟล์ต้นทาง:
- finetuned_metrics_detail.csv: `violin-checker/outputs/finetune_2026-05-23/finetuned_metrics_detail.csv`
- baseline_metrics_detail.csv:  `violin-checker/outputs/finetune_2026-05-23/baseline_metrics_detail.csv`
- manifest.csv:                 `violin-checker/datasets/composition/manifest.csv`

เป้าหมาย: หา 10 ไฟล์แย่สุด (bottom-10) ของแต่ละชุดทดสอบ (52/12/10 ไฟล์) แล้วระบุว่าเป็นข้อมูลลักษณะใด

---

## ส่วนที่ 1: 10 ไฟล์แย่สุดของแต่ละชุดทดสอบ

### 1.1 MOSA_test (52 ไฟล์  bottom 10)

| Rank | filename | RPA_ft | RCA_ft | MAE_ft | RPA_bl | Δ_RPA | n_frames | dur_sec | piece_id | performer_id |
|------|----------|-------:|-------:|-------:|-------:|------:|---------:|--------:|----------|--------------|
| 1 | `ba3_yv02_t1.wav` | 0.6189 | 0.6336 | 183.61 | 0.5666 | +0.0523 | 13981 | 170.97 | ba3_yv02 | ba3 |
| 2 | `ba4_yv08_t1.wav` | 0.7969 | 0.8080 | 84.88 | 0.7148 | +0.0821 | 7490 | 101.37 | ba4_yv08 | ba4 |
| 3 | `ba3_yv02_t2.wav` | 0.7989 | 0.8061 | 89.37 | 0.7328 | +0.0661 | 13315 | 167.46 | ba3_yv02 | ba3 |
| 4 | `ba3_yv02_t3.wav` | 0.8026 | 0.8132 | 88.95 | 0.7271 | +0.0755 | 12552 | 156.46 | ba3_yv02 | ba3 |
| 5 | `ba3_ev04_t1.wav` | 0.8029 | 0.8093 | 88.83 | 0.7416 | +0.0612 | 13940 | 175.13 | ba3_ev04 | ba3 |
| 6 | `ba4_yv08_t2.wav` | 0.8056 | 0.8149 | 84.90 | 0.7430 | +0.0627 | 7877 | 103.75 | ba4_yv08 | ba4 |
| 7 | `ba3_ev03_t1.wav` | 0.8104 | 0.8256 | 91.67 | 0.7320 | +0.0784 | 10989 | 143.06 | ba3_ev03 | ba3 |
| 8 | `ba4_yv08_t3.wav` | 0.8115 | 0.8185 | 75.38 | 0.7358 | +0.0757 | 7641 | 106.32 | ba4_yv08 | ba4 |
| 9 | `ba3_ev03_t2.wav` | 0.8158 | 0.8309 | 93.61 | 0.7236 | +0.0922 | 10527 | 141.13 | ba3_ev03 | ba3 |
| 10 | `me4_yv05_t1.wav` | 0.8163 | 0.8509 | 103.50 | 0.7318 | +0.0845 | 11927 | 164.69 | me4_yv05 | me4 |

### 1.2 MusicNet_test (12 ไฟล์ เรียงทั้งหมด; bottom-10 อยู่เหนือเส้นแบ่ง)

| Rank | filename | RPA_ft | RCA_ft | MAE_ft | RPA_bl | Δ_RPA | n_frames | dur_sec | piece_id | performer_id |
|------|----------|-------:|-------:|-------:|-------:|------:|---------:|--------:|----------|--------------|
| 1 | `2147.wav` | 0.0067 | 0.0199 | 1092.02 | 0.0100 | -0.0033 | 11549 | 501.81 | Brahms::String Sextet No 2 in G major | String Sextet |
| 2 | `2466.wav` | 0.1113 | 0.1299 | 410.47 | 0.0575 | +0.0537 | 5141 | 305.74 | Beethoven::Violin Sonata No 4 in A minor | Accompanied Violin |
| 3 | `2621.wav` | 0.2400 | 0.4193 | 1035.08 | 0.0908 | +0.1492 | 12899 | 648.67 | Beethoven::String Quartet No 7 in F major | String Quartet |
| 4 | `1788.wav` | 0.2568 | 0.3795 | 930.73 | 0.0816 | +0.1752 | 10075 | 513.19 | Mozart::String Quartet No 19 in C major | String Quartet |
| 5 | `2622.wav` | 0.3048 | 0.5624 | 975.12 | 0.1249 | +0.1799 | 9615 | 507.25 | Beethoven::String Quartet No 7 in F major | String Quartet |
| 6 | `1791.wav` | 0.3066 | 0.4466 | 829.43 | 0.0788 | +0.2278 | 6148 | 351.53 | Mozart::String Quartet No 19 in C major | String Quartet |
| 7 | `1793.wav` | 0.3194 | 0.3449 | 322.97 | 0.1030 | +0.2164 | 3685 | 504.89 | Mozart::String Quartet No 19 in C major | String Quartet |
| 8 | `1792.wav` | 0.3968 | 0.4787 | 450.41 | 0.1103 | +0.2865 | 4826 | 472.79 | Mozart::String Quartet No 19 in C major | String Quartet |
| 9 | `1789.wav` | 0.4017 | 0.4490 | 642.13 | 0.0964 | +0.3053 | 7648 | 461.33 | Mozart::String Quartet No 19 in C major | String Quartet |
| 10 | `1790.wav` | 0.4155 | 0.5503 | 630.04 | 0.1388 | +0.2767 | 7134 | 323.86 | Mozart::String Quartet No 19 in C major | String Quartet |
|---|---|---|---|---|---|---|---|---|---|---|
| 11 | `2463.wav` | 0.4394 | 0.5089 | 625.71 | 0.2316 | +0.2078 | 8967 | 309.73 | Beethoven::Violin Sonata No 4 in A minor | Accompanied Violin |
| 12 | `2462.wav` | 0.5130 | 0.7285 | 534.37 | 0.2994 | +0.2137 | 12229 | 489.43 | Beethoven::Violin Sonata No 4 in A minor | Accompanied Violin |

### 1.3 Bach10 (10 ไฟล์ เรียงทั้งหมด)

| Rank | filename | RPA_ft | RCA_ft | MAE_ft | RPA_bl | Δ_RPA | n_frames | dur_sec | piece_id | performer_id |
|------|----------|-------:|-------:|-------:|-------:|------:|---------:|--------:|----------|--------------|
| 1 | `02-AchLiebenChristen-violin.wav` | 0.9773 | 0.9790 | 16.83 | 0.9541 | +0.0232 | 3521 | 40.49 | 02-AchLiebenChristen |  |
| 2 | `06-DieSonne-violin.wav` | 0.9775 | 0.9789 | 19.48 | 0.9642 | +0.0133 | 2887 | 33.25 | 06-DieSonne |  |
| 3 | `09-Jesus-violin.wav` | 0.9797 | 0.9805 | 17.71 | 0.9661 | +0.0136 | 2514 | 29.31 | 09-Jesus |  |
| 4 | `08-FuerDeinenThron-violin.wav` | 0.9801 | 0.9852 | 21.96 | 0.9717 | +0.0083 | 2914 | 33.20 | 08-FuerDeinenThron |  |
| 5 | `01-AchGottundHerr-violin.wav` | 0.9824 | 0.9842 | 15.66 | 0.9645 | +0.0179 | 2155 | 25.19 | 01-AchGottundHerr |  |
| 6 | `04-ChristeDuBeistand-violin.wav` | 0.9827 | 0.9827 | 14.25 | 0.9752 | +0.0075 | 3585 | 41.62 | 04-ChristeDuBeistand |  |
| 7 | `03-ChristederdubistTagundLicht-violin.wav` | 0.9833 | 0.9843 | 13.50 | 0.9695 | +0.0139 | 2159 | 25.32 | 03-ChristederdubistTagundLicht |  |
| 8 | `10-NunBitten-violin.wav` | 0.9833 | 0.9833 | 13.62 | 0.9627 | +0.0206 | 3240 | 37.35 | 10-NunBitten |  |
| 9 | `05-DieNacht-violin.wav` | 0.9853 | 0.9859 | 16.78 | 0.9778 | +0.0075 | 3055 | 35.77 | 05-DieNacht |  |
| 10 | `07-HerrGott-violin.wav` | 0.9854 | 0.9868 | 15.61 | 0.9608 | +0.0246 | 2802 | 32.52 | 07-HerrGott |  |

---

## ส่วนที่ 2: วิเคราะห์การกระจายของโน้ต

### 2.1 MOSA

_(bottom-10 มี 10 ไฟล์ที่มีโน้ต; top-10 มี 10 ไฟล์)_

| คุณลักษณะ | Bottom-10 (เฉลี่ย ± std) | Top-10 (เฉลี่ย ± std) | เด่น? |
|---|---|---|:---:|
| MIDI ต่ำสุด | 55.9 ± 0.3 | 58.0 ± 2.4 | **ใช่** |
| MIDI สูงสุด | 89.2 ± 3.6 | 92.1 ± 5.2 | ไม่ |
| ช่วง MIDI (สูง−ต่ำ) | 33.3 ± 3.9 | 34.1 ± 6.7 | ไม่ |
| % โน้ตเหนือ C6 (MIDI ≥ 84) | 3.90 ± 4.05 | 11.29 ± 4.94 | **ใช่** |
| % โน้ตต่ำกว่า G3 (MIDI < 55) | 0.00 ± 0.00 | 0.00 ± 0.00 | ไม่ |
| median ความยาวโน้ต (วินาที) | 0.16 ± 0.04 | 0.34 ± 0.10 | **ใช่** |
| โน้ตต่อวินาที | 6.02 ± 0.71 | 1.93 ± 0.70 | **ใช่** |
| ความหนาแน่น onset สูงสุด (โน้ต/1วิ) | 11.7 ± 4.8 | 6.2 ± 2.5 | **ใช่** |

### 2.2 MusicNet

_(bottom-10 มี 10 ไฟล์ที่มีโน้ต; top-10 มี 10 ไฟล์)_

| คุณลักษณะ | Bottom-10 (เฉลี่ย ± std) | Top-10 (เฉลี่ย ± std) | เด่น? |
|---|---|---|:---:|
| MIDI ต่ำสุด | 54.8 ± 1.0 | 54.9 ± 1.0 | ไม่ |
| MIDI สูงสุด | 92.0 ± 3.0 | 91.1 ± 2.7 | ไม่ |
| ช่วง MIDI (สูง−ต่ำ) | 37.2 ± 2.9 | 36.2 ± 2.7 | ไม่ |
| % โน้ตเหนือ C6 (MIDI ≥ 84) | 6.53 ± 4.29 | 5.51 ± 4.01 | ไม่ |
| % โน้ตต่ำกว่า G3 (MIDI < 55) | 0.00 ± 0.01 | 0.00 ± 0.01 | ไม่ |
| median ความยาวโน้ต (วินาที) | 0.21 ± 0.13 | 0.21 ± 0.13 | ไม่ |
| โน้ตต่อวินาที | 5.27 ± 1.82 | 4.77 ± 1.94 | ไม่ |
| ความหนาแน่น onset สูงสุด (โน้ต/1วิ) | 20.8 ± 6.3 | 19.1 ± 6.7 | ไม่ |

### 2.3 Bach10

_(bottom-10 มี 10 ไฟล์ที่มีโน้ต; top-10 มี 10 ไฟล์)_

| คุณลักษณะ | Bottom-10 (เฉลี่ย ± std) | Top-10 (เฉลี่ย ± std) | เด่น? |
|---|---|---|:---:|
| MIDI ต่ำสุด | 62.6 ± 2.6 | 62.6 ± 2.6 | ไม่ |
| MIDI สูงสุด | 80.4 ± 3.8 | 80.4 ± 3.8 | ไม่ |
| ช่วง MIDI (สูง−ต่ำ) | 17.8 ± 3.9 | 17.8 ± 3.9 | ไม่ |
| % โน้ตเหนือ C6 (MIDI ≥ 84) | 0.00 ± 0.00 | 0.00 ± 0.00 | ไม่ |
| % โน้ตต่ำกว่า G3 (MIDI < 55) | 0.00 ± 0.00 | 0.00 ± 0.00 | ไม่ |
| median ความยาวโน้ต (วินาที) | 0.39 ± 0.09 | 0.39 ± 0.09 | ไม่ |
| โน้ตต่อวินาที | 1.85 ± 0.32 | 1.85 ± 0.32 | ไม่ |
| ความหนาแน่น onset สูงสุด (โน้ต/1วิ) | 6.9 ± 1.5 | 6.9 ± 1.5 | ไม่ |

---

## ส่วนที่ 3: รูปแบบระดับ Frame

### 3.1 MOSA

| สถิติ | Bottom-10 | Top-10 |
|---|---:|---:|
| frame ที่ประเมินทั้งหมด | 110,239 | 97,233 |
| จำนวน recording ที่ใช้ | 10 | 10 |
| ค่าเฉลี่ย GT F0 (Hz) | 614.3 | 690.0 |
| median GT F0 (Hz, ประมาณจาก hist) | 554.0 | 659.0 |
| mean |error| (cents, voiced) | 100.6 | 30.9 |
| สัดส่วน frame error > 50¢ | 0.2171 | 0.0762 |
| สัดส่วน frame error > 100¢ | 0.1870 | 0.0555 |
| สัดส่วน frame error > 1200¢ | 0.0060 | 0.0029 |

### 3.2 MusicNet

| สถิติ | Bottom-10 | Top-10 |
|---|---:|---:|
| frame ที่ประเมินทั้งหมด | 78,720 | 83,226 |
| จำนวน recording ที่ใช้ | 10 | 10 |
| ค่าเฉลี่ย GT F0 (Hz) | 664.9 | 654.0 |
| median GT F0 (Hz, ประมาณจาก hist) | 587.0 | 587.0 |
| mean |error| (cents, voiced) | 822.2 | 746.5 |
| สัดส่วน frame error > 50¢ | 0.7424 | 0.6414 |
| สัดส่วน frame error > 100¢ | 0.7115 | 0.6178 |
| สัดส่วน frame error > 1200¢ | 0.2704 | 0.2394 |

### 3.3 Bach10

| สถิติ | Bottom-10 | Top-10 |
|---|---:|---:|
| frame ที่ประเมินทั้งหมด | 28,832 | 28,832 |
| จำนวน recording ที่ใช้ | 10 | 10 |
| ค่าเฉลี่ย GT F0 (Hz) | 478.2 | 478.2 |
| median GT F0 (Hz, ประมาณจาก hist) | 465.0 | 465.0 |
| mean |error| (cents, voiced) | 16.2 | 16.2 |
| สัดส่วน frame error > 50¢ | 0.0189 | 0.0189 |
| สัดส่วน frame error > 100¢ | 0.0098 | 0.0098 |
| สัดส่วน frame error > 1200¢ | 0.0006 | 0.0006 |

---

## ส่วนที่ 4: สมมติฐานของ Failure Mode

### สมมติฐาน 1: bottom-10 ของ MOSA ถูกครอบงำด้วยท่อนเร็ว/โน้ตถี่ (โน้ต/วิสูง, โน้ตสั้น)

**หลักฐาน**: โน้ตต่อวินาที bottom=6.02 vs top=1.93 (3.1× higher, 5.8σ). Median note duration bottom=0.16s vs top=0.34s (2.2× longer in top-10). Peak onset density bottom=11.7 vs top=6.2 notes/sec. Fast passages stress CREPE's 1024-sample (64 ms) frame window: note transitions land mid-frame and the model's piecewise-constant target assumption breaks down. This is the strongest signal in the analysis.

**ความเชื่อมั่น**: สูง

### สมมติฐาน 2: bottom-10 ของ MOSA พลาดแบบ 'ผิดเล็กๆ จำนวนมาก' ไม่ใช่กระโดด octave

**หลักฐาน**: frac(err>50¢) bottom=0.217 vs top=0.076 (มากกว่า 2.8x) frac(err>1200¢) bottom=0.0060 vs top=0.0029 (จิ๋วทั้งคู่ <1%) mean|error| bottom=100.6¢ vs top=30.9¢ รูปแบบสอดคล้องกับการเพี้ยน intonation, vibrato หรือขอบโน้ตไม่ตรง (GT คงที่ vs pitch แสดงอารมณ์ต่อเนื่อง) ไม่ใช่ failure mode แบบ harmonic locking

**ความเชื่อมั่น**: สูง

### สมมติฐาน 3: bottom-10 ของ MOSA อยู่ย่านกลาง (ไม่ใช่สูง) - ย่านเสียงไม่ใช่แกนที่ทำพลาด

**หลักฐาน**: % โน้ต ≥ C6: bottom=3.9% vs top=11.3% (bottom มีโน้ตสูง *น้อยกว่า*) MIDI ต่ำ bottom=55.9 vs top=58.0; MIDI สูง bottom=89.2 vs top=92.1; F0 เฉลี่ย bottom=614 vs top=690 Hz  ตัดสมมติฐาน 'CREPE แย่กับโน้ตสูง' ทิ้ง bottom-10 คือท่อนเร็วย่านกลาง ไม่ใช่ย่านสุดขั้ว

**ความเชื่อมั่น**: สูง

### สมมติฐาน 4: ความยากของ MusicNet สม่ำเสมอทั้งชุด - polyphony พังทั้งการประเมิน ไม่ใช่แค่ bottom-10

**หลักฐาน**: frac(err>1200¢): bottom=0.2704 vs top=0.2394 (ต่างแค่ 1.13x เล็ก) mean|error|: bottom=822¢ vs top=747¢ **ทั้งคู่** ถูกครอบงำด้วยการสับสน octave/เครื่องดนตรี (~25% frame >1200¢ ทั้งสองกลุ่ม)  polyphony เป็นปัญหาทั้งชุด การจัดอันดับใน MusicNet แค่เรียงตามปริมาณ polyphony เทียบ Bach10 (polyphonic แต่แยก stem สะอาด): mean|err| = 17¢ ทั้งกระดาน

**ความเชื่อมั่น**: ต่ำ

### สมมติฐาน 5: Bach10 อยู่ที่เพดานโมเดล - การแบ่ง bottom/top ไม่มีความหมายในชุด 10 ไฟล์ที่ RPA ≥ 0.97 ทั้งหมด

**หลักฐาน**: Bach10 ทั้ง 10 ไฟล์ RPA อยู่ [0.977, 0.985] ต่างกัน ~1 จุด อยู่ในช่วง noise สถิติ frame ของ bottom-10/top-10 เหมือนกันโดยโครงสร้าง (ไฟล์เดียวกัน) ไม่มี failure mode ให้สืบ

**ความเชื่อมั่น**: สูง

---

## ส่วนที่ 5: เทียบกับ Pretrained

### 5.1 MOSA

| หมวด | จำนวน | คำอธิบาย |
|---|---:|---|
| อยู่ bottom-10 ทั้งคู่ | 9 | ยากเชิงระบบ - pretrained ก็พลาด |
| fine-tune ช่วยแต่ยัง bottom-10 | 1 | fine-tune ช่วย (Δ_RPA ≥ 0) แต่ RPA ยังอยู่ worst-10 |
| fine-tune ทำแย่ลง (Δ_RPA < 0) | 0 | fine-tune สร้าง failure mode ใหม่ |

**ไฟล์ที่อยู่ bottom-10 ทั้ง pretrained และ finetuned (ยากเชิงระบบ):**

| file | RPA_pretrained | RPA_finetuned |
|---|---:|---:|
| `ba3_yv02_t1.wav` | 0.5666 | 0.6189 |
| `ba4_yv08_t1.wav` | 0.7148 | 0.7969 |
| `ba3_yv02_t2.wav` | 0.7328 | 0.7989 |
| `ba3_yv02_t3.wav` | 0.7271 | 0.8026 |
| `ba3_ev04_t1.wav` | 0.7416 | 0.8029 |
| `ba3_ev03_t1.wav` | 0.7320 | 0.8104 |
| `ba4_yv08_t3.wav` | 0.7358 | 0.8115 |
| `ba3_ev03_t2.wav` | 0.7236 | 0.8158 |
| `me4_yv05_t1.wav` | 0.7318 | 0.8163 |

### 5.2 MusicNet

| หมวด | จำนวน | คำอธิบาย |
|---|---:|---|
| อยู่ bottom-10 ทั้งคู่ | 10 | ยากเชิงระบบ - pretrained ก็พลาด |
| fine-tune ช่วยแต่ยัง bottom-10 | 0 | fine-tune ช่วย (Δ_RPA ≥ 0) แต่ RPA ยังอยู่ worst-10 |
| fine-tune ทำแย่ลง (Δ_RPA < 0) | 1 | fine-tune สร้าง failure mode ใหม่ |

**ไฟล์ที่ fine-tune ทำให้แย่ลง:**

| file | Δ_RPA | RPA_pretrained | RPA_finetuned | MAE_finetuned |
|---|---:|---:|---:|---:|
| `2147.wav` | -0.0033 | 0.0100 | 0.0067 | 1092.02 |

**ไฟล์ที่อยู่ bottom-10 ทั้ง pretrained และ finetuned (ยากเชิงระบบ):**

| file | RPA_pretrained | RPA_finetuned |
|---|---:|---:|
| `2147.wav` | 0.0100 | 0.0067 |
| `2466.wav` | 0.0575 | 0.1113 |
| `2621.wav` | 0.0908 | 0.2400 |
| `1788.wav` | 0.0816 | 0.2568 |
| `2622.wav` | 0.1249 | 0.3048 |
| `1791.wav` | 0.0788 | 0.3066 |
| `1793.wav` | 0.1030 | 0.3194 |
| `1792.wav` | 0.1103 | 0.3968 |
| `1789.wav` | 0.0964 | 0.4017 |
| `1790.wav` | 0.1388 | 0.4155 |

### 5.3 Bach10

| หมวด | จำนวน | คำอธิบาย |
|---|---:|---|
| อยู่ bottom-10 ทั้งคู่ | 10 | ยากเชิงระบบ - pretrained ก็พลาด |
| fine-tune ช่วยแต่ยัง bottom-10 | 0 | fine-tune ช่วย (Δ_RPA ≥ 0) แต่ RPA ยังอยู่ worst-10 |
| fine-tune ทำแย่ลง (Δ_RPA < 0) | 0 | fine-tune สร้าง failure mode ใหม่ |

**ไฟล์ที่อยู่ bottom-10 ทั้ง pretrained และ finetuned (ยากเชิงระบบ):**

| file | RPA_pretrained | RPA_finetuned |
|---|---:|---:|
| `02-AchLiebenChristen-violin.wav` | 0.9541 | 0.9773 |
| `06-DieSonne-violin.wav` | 0.9642 | 0.9775 |
| `09-Jesus-violin.wav` | 0.9661 | 0.9797 |
| `08-FuerDeinenThron-violin.wav` | 0.9717 | 0.9801 |
| `01-AchGottundHerr-violin.wav` | 0.9645 | 0.9824 |
| `04-ChristeDuBeistand-violin.wav` | 0.9752 | 0.9827 |
| `03-ChristederdubistTagundLicht-violin.wav` | 0.9695 | 0.9833 |
| `10-NunBitten-violin.wav` | 0.9627 | 0.9833 |
| `05-DieNacht-violin.wav` | 0.9778 | 0.9853 |
| `07-HerrGott-violin.wav` | 0.9608 | 0.9854 |

---

## ส่วนที่ 6: ขั้นตอนถัดไปที่แนะนำ

1. **เทรนรอบสอง** ด้วย `--lr 1e-5`, `--freeze-early` (freeze conv1-conv4), `max_epochs=10` best.pt มาตั้งแต่ 22 นาทีแรก แปลว่า 5e-5 แรงไป LR ต่ำกว่าจะขยับผลทีละนิดโดยไม่รื้อ feature ที่ pretrained ไว้

2. **เพิ่ม source separation** (Demucs/Spleeter) ก่อน CREPE สำหรับ MusicNet polyphonic - ส่วนที่ 3 ชี้ว่า bottom-10 พลาดเพราะสับสน octave/เครื่องดนตรี (frac>1200¢=0.270) แยก stem ไวโอลินก่อนอาจปลดล็อก RPA +5-10 จุด

3. **สืบไฟล์ที่ fine-tune ทำแย่ลง** (ดูส่วนที่ 5) ฟัง หาคุณลักษณะร่วม แล้วพิจารณาตัดไฟล์คล้ายกันออกจาก training set ในรอบสาม

4. **แก้ val-metric ที่ไม่ตรง** ใน `finetune_crepe.py::evaluate`: เปลี่ยน val RPA ตอนเทรนจาก weighted-mean cents เป็น argmax+50¢ (ตรงกับตอน eval) นี่คือการเสีย compute มากสุดในรอบก่อน (เกินจุด best จริง 11 ชม.)

---

## ส่วนที่ 7: รายการสำหรับฟัง (ขั้นตอนที่คนทำเอง)

_การวิเคราะห์นี้อิงตัวเลข ไม่ได้ฟังจริง คอลัมน์ 'ฟังหาอะไร' มาจากส่วนที่ 2-4 ให้เติมข้อสังเกตหลังฟังเอง_

_ข้าม Bach10: ทั้ง 10 ไฟล์ RPA ≥ 0.97 (เพดาน)_

| # | ไฟล์ | ชุด | ฟังหาอะไร |
|---|---|---|---|
| 1 | `ba3_yv02_t1.wav` | MOSA | ยืนยันสมมติฐานท่อนเร็ว: โน้ตถี่ 5+/วิไหม จุดพลาดโน้ตสั้นกว่า 200ms ไหม เช็ค vibrato หนัก (>30¢) และ legato |
| 2 | `ba4_yv08_t1.wav` | MOSA | ยืนยันสมมติฐานท่อนเร็ว: โน้ตถี่ 5+/วิไหม จุดพลาดโน้ตสั้นกว่า 200ms ไหม เช็ค vibrato หนัก (>30¢) และ legato |
| 3 | `2147.wav` | MusicNet | ไวโอลินดังแค่ไหนเทียบเครื่องอื่น คนแยกเสียงไวโอลินออกไหม ถ้าได้  Demucs น่าช่วย ถ้าคนยังยาก  GT ของไฟล์นี้น่าสงสัย |
| 4 | `2466.wav` | MusicNet | ไวโอลินดังแค่ไหนเทียบเครื่องอื่น คนแยกเสียงไวโอลินออกไหม ถ้าได้  Demucs น่าช่วย ถ้าคนยังยาก  GT ของไฟล์นี้น่าสงสัย |
