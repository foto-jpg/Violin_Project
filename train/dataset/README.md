# train/dataset/ - เตรียมชุดข้อมูลฝึก

สคริปต์เตรียม/แปลงข้อมูลก่อนเทรน CREPE - **ไม่มีไฟล์ data จริง** (≈123 GB อยู่นอกรีโป)

| ไฟล์ | หน้าที่ |
|------|---------|
| `prepare_musicnet_violin.py` | ดึงเฉพาะ track ไวโอลินจาก MusicNet + ทำ pitch label |
| `build_train_prepared.py` | ประกอบชุด train ที่พร้อมป้อนโมเดล (clip + f0) |
| `build_composition_matrix.py` | สร้างเมทริกซ์องค์ประกอบชุดข้อมูล (สัดส่วนแต่ละแหล่ง) |

## ขั้นตอนทั่วไป
```bash
python prepare_musicnet_violin.py --src /path/to/musicnet --out /path/to/prepared
python build_train_prepared.py    --in  /path/to/prepared --out /path/to/train_ready
```

## แหล่งข้อมูลที่ใช้
- **MusicNet** (เฉพาะไวโอลิน), **MOSA**, **Bach10** (สำหรับ test)
- ผลลัพธ์เก็บนอกรีโป (gitignore) เพราะมีขนาดใหญ่มาก
