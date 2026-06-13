'use client'
import { useState } from 'react'

import ImageCompare from '@/components/ImageCompare'
import AudioPanel from '@/components/AudioPanel'
import HfApp from '@/components/HfApp'

type Mode = 'image' | 'audio'

export default function HomePage() {
  // HF deployment ships the full pipeline (Audiveris + CREPE + match), Audiveris-only.
  // Local keeps the research UI: oemerAudiveris compare + audio.
  if (process.env.NEXT_PUBLIC_HF === '1') return <HfApp />
  return <LocalApp />
}

function LocalApp() {
  // Shared tempo (BPM) - used to convert durations into written note values
  const [tempo, setTempo] = useState<number>(120)
  const [mode, setMode] = useState<Mode>('image')

  return (
    <main className="max-w-6xl mx-auto px-4 py-10 space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Violin Note Detector</h1>
          <p className="text-gray-500 mt-1">เลือกโหมด - เปรียบเทียบโมเดลภาพ (oemer  Audiveris) หรือถอดโน้ตจากเสียง</p>
        </div>
        <label className="flex items-center gap-2 text-sm bg-white border border-gray-200 rounded-xl px-3 py-2">
          <span className="text-gray-600 font-medium">Tempo</span>
          <input
            type="number"
            min={20}
            max={300}
            value={tempo}
            onChange={(e) => setTempo(Math.max(20, Math.min(300, Number(e.target.value) || 120)))}
            className="w-20 text-right font-mono border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-teal-300"
          />
          <span className="text-gray-400">BPM</span>
        </label>
      </div>

      {/* ── Mode tabs ─────────────────────────────────────────────────── */}
      <div className="flex gap-3">
        <ModeButton active={mode === 'image'} onClick={() => setMode('image')}>
           ภาพ
        </ModeButton>
        <ModeButton active={mode === 'audio'} onClick={() => setMode('audio')}>
           เสียง
        </ModeButton>
      </div>

      {mode === 'image' ? <ImageCompare tempo={tempo} /> : <AudioPanel tempo={tempo} />}
    </main>
  )
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-4 rounded-2xl font-semibold text-lg transition-colors border-2 ${
        active
          ? 'bg-gray-900 text-white border-gray-900'
          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'
      }`}
    >
      {children}
    </button>
  )
}
