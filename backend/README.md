# backend/ - FastAPI (API + serving)

API หลังบ้าน + business logic ของ OMR / audio / match และ image preprocessing

## โครงสร้าง
```
app/
├─ main.py            entry: รวม router + (HF) เสิร์ฟ frontend static
├─ config.py          settings (data_dir, timeout)
├─ routes/            HTTP endpoints
│  ├─ omr.py          /api/omr/*   (process, result, download, musicxml)
│  ├─ audio.py        /api/audio/* (process, result, file)
│  ├─ match.py        /api/match   (async + /match/result)
│  └─ system.py       /api/health, /api/gpu-status
├─ services/          oemer_engine, _ort_patch, audiveris, audio_engine,
│                     audio_align (DTW), gpu_selector, *_jobs (in-memory stores)
├─ schemas/           pydantic models
└─ utils/             files.py (orient/trim/upscale), musicxml.py (parse/แตก .mxl)
tests/                pytest (oemer, audiveris, gpu_selector)
checkpoints/          crepe_violin.pt (โมเดลเสียง fine-tuned)
```

## รัน (local, มี GPU)
```bash
python3.11 -m venv venv && venv/bin/pip install -r requirements.txt
# จาก root ของรีโป:
bash ../scripts/run_backend.sh      # uvicorn :8300 (ใช้ venv + GPU)
```

## Environment สำคัญ (env-gated - โค้ดชุดเดียวรันได้ทั้ง local/HF)
| var | ผล |
|-----|-----|
| `DISABLE_GPU=1` | บังคับ CPU (ปิด pynvml/CUDA) |
| `DISABLE_OEMER=1` | ปิด engine oemer (HF) |
| `AUDIVERIS_BIN` | เรียก Audiveris ผ่าน Java binary แทน docker |
| `STATIC_DIR` | เสิร์ฟ frontend static (HF) |
| `CREPE_CHECKPOINT` | path โมเดลเสียง fine-tuned |
| `MAX_AUDIO_SECONDS` | จำกัดความยาวคลิป |

## หมายเหตุ
- งานหนักทุกอย่างเป็น **BackgroundTask + polling** (`/result/{job_id}`) และรันทีละงาน (`is_any_running`  429)
- `venv/`, `data/` (uploads/results) ไม่อยู่ในรีโป
- ก๊อปปี้ `.env.example`  `.env` แล้วเติมค่า (DB/MinIO) ถ้าจะใช้ docker-compose เต็มสแตก
