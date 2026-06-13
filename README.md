# Violin Practice Evaluator

เว็บแอปตรวจการเล่นไวโอลินอัตโนมัติ - รับ **ภาพโน้ตเพลง** + **คลิปเสียงที่เล่น** แล้วเทียบกัน
บอกว่าโน้ตไหนเล่นถูก / เพี้ยน / ตก

| Input | เทคโนโลยี |
|-------|-----------|
|  ภาพโน้ต (PNG/JPG/PDF) | OMR - `oemer` (deep learning) และ `Audiveris` (rule-based)  MusicXML |
|  คลิปเสียง (WAV/MP3) | CREPE (fine-tuned ไวโอลิน) ถอด pitch |
|  เทียบ | DTW alignment  คะแนน + ระบายสีบนแผ่นโน้ต (OSMD) |

## โครงสร้างโปรเจกต์

```
.
├─ frontend/          เว็บ Next.js (React) - UI ทั้งหมด
├─ backend/           FastAPI - API, OMR/audio/match services, preprocessing
├─ train/             งานเทรนโมเดล + OMR engines + รายงาน + เอกสาร
│  ├─ crepe/          เทรน/ประเมินโมเดลเสียง CREPE
│  ├─ dataset/        สคริปต์เตรียมชุดข้อมูล (MusicNet/MOSA)
│  ├─ audiveris/      OMR engine #2 (Java) - docker setup
│  ├─ oemer/          OMR engine #1 (deep learning) - หมายเหตุการใช้งาน
│  └─ reports/        ผลการเทรน/ประเมิน (ไฟล์เล็ก)
├─ scripts/           สคริปต์รัน/ตั้งค่า (run_backend, start_dev, setup)
├─ docker/            audiveris image build (ใช้โดย backend ตอนรัน local)
├─ Dockerfile         บิลด์ HF Spaces (container เดียว: frontend+backend+CPU)
├─ docker-compose.yml ออร์เคสเตรชัน dev (frontend + audiveris)
└─ SYSTEM_DOC.html    เอกสารอธิบายระบบแบบละเอียด (เปิดในเบราว์เซอร์)
```

> **3 โฟลเดอร์โค้ดหลัก** = `frontend/` `backend/` `train/` ส่วนไฟล์ที่ root (Dockerfile, compose, scripts/, docker/) เป็น "กาว" สำหรับรัน/deploy ที่อ้างอิงข้ามโฟลเดอร์

## รันแบบเร็ว

**A) Local (มี GPU) - วิจัย/พัฒนา**
```bash
bash scripts/run_backend.sh          # backend :8300 (host venv + GPU)
docker compose up -d frontend        # frontend :3100
```

**B) HF / CPU - เวอร์ชัน deploy (container เดียว)**
```bash
docker build -t violin-hf .
docker run -p 7860:7860 violin-hf    # เว็บ + API รวมที่ :7860
```

รายละเอียดของแต่ละส่วนดูใน `README.md` ของแต่ละโฟลเดอร์ และ `SYSTEM_DOC.html`

## หมายเหตุ
- **datasets ขนาดใหญ่ (123 GB) ไม่อยู่ในรีโป** - ดูวิธีดาวน์โหลด/เตรียมใน `train/dataset/`
- โมเดล `backend/checkpoints/crepe_violin.pt` (~85 MB) รวมมาด้วย - ถ้า push GitHub ให้ใช้ **Git LFS** (`git lfs track "*.pt"`)
- คัดลอกไฟล์ `.env` จาก `backend/.env.example` แล้วเติมค่าเอง (ไฟล์ `.env` จริงไม่อยู่ในรีโป)
