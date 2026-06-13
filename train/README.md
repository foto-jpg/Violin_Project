# train/ - งานเทรนโมเดล + OMR engines + รายงาน

รวมทุกอย่างที่เกี่ยวกับการ "ทำให้โมเดลฉลาด" และเครื่องยนต์ OMR (แยกจากโค้ดที่รันใน production)

| โฟลเดอร์ | คืออะไร |
|----------|---------|
| `crepe/` | เทรน/ประเมินโมเดลเสียง **CREPE** (fine-tune สำหรับไวโอลิน) - โมเดลที่ deploy มาจากที่นี่ |
| `dataset/` | สคริปต์เตรียมชุดข้อมูล (MusicNet violin / MOSA / composition matrix) - **ไม่รวมไฟล์ data จริง 123GB** |
| `audiveris/` | OMR engine #2 (Java, rule-based) - Docker setup ที่ใช้บิลด์ image |
| `oemer/` | OMR engine #1 (deep learning) - หมายเหตุการใช้งาน (เป็น pip lib, wrapper อยู่ใน backend) |
| `reports/` | ผลการเทรน/ประเมินจริง (CSV/JSON/MD) - log ราย epoch, baseline vs fine-tuned, error analysis |

## ภาพรวม pipeline การเทรน
```
dataset/   เตรียม clip+pitch (จาก MusicNet/MOSA)
crepe/     finetune_crepe.py เทรน CREPE  checkpoints/*.pt
           evaluate_crepe*.py ประเมิน (RPA/RCA/MAE)  reports/
```
โมเดลที่ใช้งานจริงถูกคัดลอกไปไว้ที่ `backend/checkpoints/crepe_violin.pt`

## ข้อมูลดิบ
ชุดข้อมูลฝึก (≈123 GB) **ไม่อยู่ในรีโป** - ใช้สคริปต์ใน `dataset/` ดาวน์โหลด/เตรียมเอง
