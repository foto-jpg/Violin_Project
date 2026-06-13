# --- Frontend Builder ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# --- Final Runtime (Python + Audiveris Java) ---
FROM python:3.10-slim AS runtime

# ลง JRE สำหรับให้ Audiveris Binary ฝั่ง Backend เรียกใช้งาน
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ก็อปปี้เฉพาะไฟล์ที่จำเป็นมาใช้งาน (ลดขนาด Image Layer)
COPY backend/requirements-hf.txt ./
RUN pip install --no-cache-dir -r requirements-hf.txt

# ดึงผลลัพธ์ Static Build จาก Stage แรกมาปล่อยให้ FastAPI Mount
COPY --from=frontend-builder /app/frontend/out ./frontend_dist
COPY backend/ .

# ตั้งค่า Env สำหรับรันโหมดเว็บแบบ Headless บน HF Spaces
ENV AUDIVERIS_BIN=/usr/bin/audiveris
ENV DISABLE_GPU=1

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
