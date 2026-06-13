'use client'
import { useEffect, useRef, useState } from 'react'

import { API_BASE } from '@/lib/api'
import type { MatchResult } from './MatchView'

const COLOR_DEFAULT = '#1f2937' // gray-800
const COLOR_CORRECT = '#10b981' // emerald-500
const COLOR_WRONG = '#ef4444'   // red-500
const COLOR_MISSED = '#f97316'  // orange-500
const COLOR_ACTIVE = '#3b82f6'  // blue-500 - current note (custom playhead)

const colorFor = (status?: string) =>
  status === 'correct' ? COLOR_CORRECT
  : status === 'wrong_pitch' ? COLOR_WRONG
  : status === 'missed' ? COLOR_MISSED
  : COLOR_DEFAULT

// Paint a graphical note's SVG notehead without a full re-render.
function paint(gNote: any, color: string) {
  try {
    const el = gNote?.getSVGGElement?.()
    if (!el) return
    el.setAttribute('fill', color)
    el.querySelectorAll('path, ellipse, rect').forEach((p: Element) => p.setAttribute('fill', color))
  } catch {}
}

interface Props {
  omrJobId: string
  audioJobId: string
  matchResult: MatchResult
}

export default function SyncedScorePlayer({ omrJobId, audioJobId, matchResult }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const osmdRef = useRef<any>(null)
  const gNotesRef = useRef<any[]>([])      // ordered non-rest graphical notes
  const paintedRef = useRef<number>(-1)    // highest match-index currently painted

  const [isReady, setIsReady] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  // ── 1. Load + render MusicXML, build ordered graphical-note list ────────
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { OpenSheetMusicDisplay } = await import('opensheetmusicdisplay')
        if (cancelled || !containerRef.current) return

        // `any` - we reach into OSMD internals (GraphicalMusicSheet) not in its .d.ts.
        // No OSMD cursor - its async update throws on Audiveris XML
        // (parentMeasure.TempoExpressions). We do our own playhead via coloring.
        const osmd: any = new OpenSheetMusicDisplay(containerRef.current, {
          autoResize: true,
          backend: 'svg',
          drawTitle: true,
          drawComposer: false,
        } as any)
        osmdRef.current = osmd

        // Plain (decompressed) MusicXML - the /download route serves raw .mxl zip.
        const res = await fetch(`${API_BASE}/omr/musicxml/${omrJobId}`)
        if (!res.ok) throw new Error('โหลด MusicXML ไม่ได้')
        const xml = await res.text()

        await osmd.load(xml)
        if (cancelled) return
        osmd.render()

        // Walk the graphical sheet to collect non-rest noteheads in order.
        const gNotes: any[] = []
        const gms = osmd.GraphicalMusicSheet ?? osmd.graphic
        const measureList: any[][] = gms?.MeasureList ?? gms?.measureList ?? []
        for (const staves of measureList) {
          for (const measure of staves) {
            for (const se of measure?.staffEntries ?? []) {
              for (const gve of se?.graphicalVoiceEntries ?? []) {
                for (const gn of gve?.notes ?? []) {
                  if (!gn?.sourceNote?.isRest?.()) gNotes.push(gn)
                }
              }
            }
          }
        }
        gNotesRef.current = gNotes
        gNotes.forEach((gn) => paint(gn, COLOR_DEFAULT))
        setIsReady(true)
      } catch (err: any) {
        if (!cancelled) setLoadError(err?.message ?? 'OSMD load failed')
      }
    })()

    return () => { cancelled = true }
  }, [omrJobId])

  // ── 2. Audio element wiring ─────────────────────────────────────────────
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    const onTime = () => setCurrentTime(audio.currentTime)
    const onMeta = () => setDuration(audio.duration || 0)
    const onPlay = () => setIsPlaying(true)
    const onPause = () => setIsPlaying(false)
    audio.addEventListener('timeupdate', onTime)
    audio.addEventListener('loadedmetadata', onMeta)
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('ended', onPause)
    return () => {
      audio.removeEventListener('timeupdate', onTime)
      audio.removeEventListener('loadedmetadata', onMeta)
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('ended', onPause)
    }
  }, [isReady])

  // ── 3. Sync colors + cursor to current audio time ───────────────────────
  useEffect(() => {
    if (!isReady) return
    const notes = matchResult.notes
    const gNotes = gNotesRef.current

    // Last note whose start has passed.
    let activeIdx = -1
    for (let i = 0; i < notes.length; i++) {
      if (currentTime >= notes[i].start_sec) activeIdx = i
      else break
    }

    if (activeIdx === paintedRef.current) return
    paintedRef.current = activeIdx

    // Repaint: passed notes by status, the active note blue, the rest default.
    // (O(n) only when the active note changes - cheap for melodies.)
    for (let i = 0; i < notes.length; i++) {
      const gn = gNotes[notes[i].index]
      if (!gn) continue
      paint(gn, i < activeIdx ? colorFor(notes[i].status)
              : i === activeIdx ? COLOR_ACTIVE
              : COLOR_DEFAULT)
    }

    // Auto-scroll the active note into view.
    if (activeIdx >= 0) {
      const el = gNotes[notes[activeIdx].index]?.getSVGGElement?.()
      el?.scrollIntoView?.({ block: 'nearest', inline: 'center', behavior: 'smooth' })
    }
  }, [currentTime, isReady, matchResult.notes])

  const togglePlay = () => {
    const a = audioRef.current
    if (!a) return
    a.paused ? a.play() : a.pause()
  }
  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (audioRef.current) audioRef.current.currentTime = Number(e.target.value)
  }

  const s = matchResult.summary
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
        <span>คาดหวัง <strong>{matchResult.expected_count}</strong></span>
        <span>เทียบได้ <strong>{matchResult.aligned_count}</strong></span>
        <span className="text-emerald-600"> ถูก {s?.correct ?? 0}</span>
        <span className="text-red-600"> เพี้ยน {s?.wrong_pitch ?? 0}</span>
        <span className="text-orange-600"> ตก {s?.missed ?? 0}</span>
      </div>

      <div className="border border-gray-200 rounded-xl bg-white overflow-auto max-h-[560px]">
        {loadError ? (
          <div className="p-6 text-center text-red-600 text-sm">{loadError}</div>
        ) : (
          <>
            {!isReady && <div className="p-6 text-center text-gray-400 text-sm">กำลังเรนเดอร์โน้ต…</div>}
            <div ref={containerRef} className="p-4" />
          </>
        )}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 space-y-2">
        <audio ref={audioRef} src={`${API_BASE}/audio/file/${audioJobId}`} preload="metadata" />
        <div className="flex items-center gap-3">
          <button onClick={togglePlay} disabled={!isReady}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium disabled:bg-gray-300">
            {isPlaying ? ' หยุด' : '▶ เล่น'}
          </button>
          <span className="text-sm font-mono tabular-nums text-gray-600">
            {fmt(currentTime)} / {fmt(duration)}
          </span>
        </div>
        <input type="range" min={0} max={duration || 0} step={0.05} value={currentTime}
          onChange={seek} className="w-full accent-blue-600" />
        <div className="flex gap-4 text-xs text-gray-400">
          <span> ถูก</span><span> เพี้ยน</span><span> ตก</span><span> ยังไม่ถึง</span>
        </div>
      </div>
    </div>
  )
}

function fmt(s: number): string {
  if (!isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const r = Math.floor(s % 60)
  return `${m}:${r.toString().padStart(2, '0')}`
}
