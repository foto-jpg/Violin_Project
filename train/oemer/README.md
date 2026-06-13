# train/oemer/ - OMR engine #1 (oemer, deep learning)

**oemer** = เครื่องยนต์ OMR แบบ deep learning (U-Net + ONNX) ใช้ GPU
เป็น **ไลบรารี pip สำเร็จรูป** (`pip install oemer`) - ไม่ได้เทรนเองในโปรเจกต์นี้
จึงไม่มีโค้ดเทรนที่นี่ มีแต่ "วิธีเรียกใช้"

## โมเดล
- oemer ฝัง ONNX model มาในแพ็กเกจ (seg_net ~37MB + unet_big ~68MB) ดาวน์โหลดอัตโนมัติตอนติดตั้ง

## โค้ดที่เรียกใช้จริง (อยู่ใน backend)
| ไฟล์ | หน้าที่ |
|------|---------|
| `backend/app/services/oemer_engine.py` | เรียก oemer ผ่าน subprocess + เลือก GPU |
| `backend/app/services/_ort_patch.py` | patch onnxruntime ให้ใช้ `CUDAExecutionProvider` + จำกัด VRAM + ลด batch |

## รันเดี่ยว ๆ
```bash
pip install oemer onnxruntime-gpu
oemer sheet.png -o out_dir            # out_dir/sheet.musicxml
```

## หมายเหตุ
- **ช้ามากบน CPU** (หลายนาที/หน้า)  เวอร์ชัน HF (CPU) จึง **ปิด oemer** (`DISABLE_OEMER=1`) ใช้ Audiveris แทน
- ใช้ oemer เฉพาะตอน local ที่มี GPU (เช่น โหมดเปรียบเทียบ oemer  Audiveris)
