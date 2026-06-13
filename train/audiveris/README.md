# train/audiveris/ - OMR engine #2 (Audiveris, Java)

**Audiveris** = เครื่องยนต์ OMR แบบ rule-based (Java) ใช้แปลงภาพโน้ต  MusicXML
ไม่ต้อง "เทรน" (rule-based) - โฟลเดอร์นี้เก็บ **Docker setup** สำหรับบิลด์ image ของเอนจิน

| ไฟล์ | หน้าที่ |
|------|---------|
| `Dockerfile` | บิลด์จาก `toprock/audiveris` (Audiveris 5.x + JRE) |
| `entrypoint.sh` | `Audiveris -batch -export -output <dir> -- <image>` |

## บิลด์ + ใช้งาน
```bash
docker build -t violin-checker-audiveris .
docker run --rm -v "$PWD/data:/data" violin-checker-audiveris /data/in.png /data/out
```

## หมายเหตุ
- ตอนรัน **local** backend เรียกผ่าน `docker run` (สำเนา setup เดียวกันอยู่ที่ `docker/audiveris/`)
- ตอน **HF** backend เรียก Java binary ตรง ๆ ผ่าน env `AUDIVERIS_BIN`
- Audiveris ชอบภาพ ~300 DPI - ระบบมี preprocessing (`backend/app/utils/files.py`) ช่วย orient/trim/upscale ให้ก่อน
