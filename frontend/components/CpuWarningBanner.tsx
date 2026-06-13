'use client'

// Shown only on the HF Free-CPU deployment (NEXT_PUBLIC_HF=1).
export default function CpuWarningBanner() {
  if (process.env.NEXT_PUBLIC_HF !== '1') return null
  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg px-4 py-3 text-sm text-yellow-800">
       <strong>กำลังรันบน Free CPU</strong> - ไม่มี GPU ประมวลผลช้ากว่าปกติ
      (โน้ต 1 หน้า ~10-20 วินาที, เสียง ~1.5 เท่าของความยาวคลิป) โปรดรอสักครู่
      และอัปโหลดทีละงาน เวอร์ชัน GPU เต็มรูปแบบดูได้ที่ repo ต้นทาง
    </div>
  )
}
