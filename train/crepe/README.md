# train/crepe/ - เทรน/ประเมินโมเดลเสียง CREPE

Fine-tune **CREPE** (torchcrepe, capacity "full") ให้แม่นกับเสียงไวโอลิน แล้วประเมิน

## ไฟล์
| ไฟล์ | หน้าที่ |
|------|---------|
| `finetune_crepe.py` | เทรนหลัก (AdamW + cosine LR, BCE per-bin, early stop)  `best.pt` |
| `finetune_crepe_v2.py` | เวอร์ชันปรับปรุง |
| `dataset.py` | โหลด clip + target pitch (Gaussian target รอบ f0) |
| `metrics.py` | RPA / RCA / MAE (cents) |
| `evaluate_crepe.py`, `evaluate_crepe_v2.py` | ประเมินบน test set (Bach10 / MusicNet / MOSA) |
| `infer.py` | รัน inference เดี่ยว ๆ |
| `download_mosa.sh` | ดาวน์โหลดชุด MOSA |

## รัน (ตัวอย่าง)
```bash
# เตรียม data ก่อน (ดู train/dataset/)
python finetune_crepe.py --epochs 30 --batch-size 32 --lr 5e-5 --device cuda:0
python evaluate_crepe_v2.py --ckpt checkpoints/best.pt
```

## ผลล่าสุด (ดู train/reports/)
เทรนจริงหยุดที่ epoch 5 (best = epoch 1, val RPA ~0.66) - best.pt ดีกว่า baseline บนทั้ง 3 test set
จึงนำ `best.pt` ไป deploy เป็น `backend/checkpoints/crepe_violin.pt`

> ต้องมี GPU (CUDA) สำหรับเทรน - inference รันบน CPU ได้
