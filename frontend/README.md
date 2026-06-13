# frontend/ - เว็บ Next.js (React)

UI ของระบบทั้งหมด เขียนด้วย **Next.js 14 (App Router) + TypeScript + Tailwind**

## มีอะไรบ้าง
| ส่วน | ไฟล์ |
|------|------|
| Entry / routing | `app/page.tsx` (เลือก `HfApp` หรือ `LocalApp` ตาม `NEXT_PUBLIC_HF`) |
| เรียก API | `lib/api.ts` (จุดเดียวที่คุยกับ backend) |
| Proxy  backend | `app/api/backend/[...path]/route.ts` (เฉพาะ local) |
| คอมโพเนนต์ | `components/` - UploadZone, NotesView, ImageCompare, AudioPanel, MatchView, **SyncedScorePlayer** (OSMD), ฯลฯ |

## รัน (dev)
```bash
npm install
npm run dev            # http://localhost:3000 (หรือ 3100 ผ่าน docker)
```

## Build
```bash
npm run build          # local = standalone server
NEXT_PUBLIC_HF=1 NEXT_PUBLIC_API_BASE=/api npm run build   # HF = static export (out/)
```

## Environment (build-time)
| var | ผล |
|-----|-----|
| `NEXT_PUBLIC_HF=1` | static export + UI แบบ HF (Audiveris-only + เครื่องเล่นโน้ต) |
| `NEXT_PUBLIC_API_BASE` | base ของ API (`/api/backend` local, `/api` บน HF) |

> `node_modules/`, `.next/`, `out/` ไม่อยู่ในรีโป - สร้างใหม่ด้วย `npm install` + build
