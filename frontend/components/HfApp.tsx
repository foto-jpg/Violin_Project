'use client'
import { useCallback, useEffect, useState } from 'react'
import useSWR from 'swr'

import CpuWarningBanner from '@/components/CpuWarningBanner'
import UploadZone from '@/components/UploadZone'
import AudioUpload from '@/components/AudioUpload'
import ProcessingStatus from '@/components/ProcessingStatus'
import NotesView, { type Note } from '@/components/NotesView'
import AudioNotesView, { type AudioNoteEvent } from '@/components/AudioNotesView'
import MatchView, { type MatchResult } from '@/components/MatchView'
import SyncedScorePlayer from '@/components/SyncedScorePlayer'
import DownloadButtons from '@/components/DownloadButtons'
import {
  submitJob, getResult,
  submitAudio, getAudioResult,
  startMatch, getMatchResult,
} from '@/lib/api'

type ImageJob = {
  job_id: string; status: string; engine: string
  notes?: Note[] | null; duration_sec?: number | null; error?: string | null
}
type AudioJob = {
  job_id: string; status: string; model?: string | null
  note_events?: AudioNoteEvent[] | null; process_duration_sec?: number | null; error?: string | null
}
type MatchJob = MatchResult & { job_id: string; status: string; error?: string | null }

const DONE = ['done', 'error']

// Full pipeline UI for the HF deployment: Audiveris OMR + CREPE audio + DTW match.
export default function HfApp() {
  const [tempo, setTempo] = useState<number>(120)

  // ── Image / Audiveris ──────────────────────────────────────────────────
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageJob, setImageJob] = useState<ImageJob | null>(null)
  const [imageError, setImageError] = useState<string | null>(null)
  const [imageSubmitting, setImageSubmitting] = useState(false)

  const imagePollKey = imageJob && !DONE.includes(imageJob.status) ? imageJob.job_id : null
  const { data: polledImage } = useSWR(
    imagePollKey ? `omr-${imagePollKey}` : null,
    () => getResult(imageJob!.job_id), { refreshInterval: 1500 },
  )
  useEffect(() => { if (polledImage) setImageJob(polledImage) }, [polledImage])

  const handleImageFile = useCallback((f: File) => {
    setImageFile(f)
    setImagePreview((p) => { if (p) URL.revokeObjectURL(p); return URL.createObjectURL(f) })
    setImageJob(null); setImageError(null)
  }, [])

  const handleImageSubmit = async () => {
    if (!imageFile) return
    setImageSubmitting(true); setImageError(null); setImageJob(null)
    try {
      const j = await submitJob(imageFile, 'audiveris', tempo)
      setImageJob({ ...j, engine: 'audiveris' })
    } catch (e: any) { setImageError(e.message) } finally { setImageSubmitting(false) }
  }
  const imageBusy = imageSubmitting || (!!imageJob && !DONE.includes(imageJob.status))

  // ── Audio / CREPE ──────────────────────────────────────────────────────
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [audioJob, setAudioJob] = useState<AudioJob | null>(null)
  const [audioError, setAudioError] = useState<string | null>(null)
  const [audioSubmitting, setAudioSubmitting] = useState(false)

  const audioPollKey = audioJob && !DONE.includes(audioJob.status) ? audioJob.job_id : null
  const { data: polledAudio } = useSWR(
    audioPollKey ? `audio-${audioPollKey}` : null,
    () => getAudioResult(audioJob!.job_id), { refreshInterval: 1500 },
  )
  useEffect(() => { if (polledAudio) setAudioJob(polledAudio) }, [polledAudio])

  const handleAudioFile = useCallback((f: File) => {
    setAudioFile(f); setAudioJob(null); setAudioError(null)
  }, [])
  const handleAudioSubmit = async () => {
    if (!audioFile) return
    setAudioSubmitting(true); setAudioError(null); setAudioJob(null)
    try {
      const j = await submitAudio(audioFile, tempo)
      setAudioJob({ job_id: j.job_id, status: j.status })
    } catch (e: any) { setAudioError(e.message) } finally { setAudioSubmitting(false) }
  }
  const audioBusy = audioSubmitting || (!!audioJob && !DONE.includes(audioJob.status))

  // ── Match (async background job) ───────────────────────────────────────
  const [matchJob, setMatchJob] = useState<MatchJob | null>(null)
  const [matchError, setMatchError] = useState<string | null>(null)
  const [matchStarting, setMatchStarting] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  const matchPollKey = matchJob && !DONE.includes(matchJob.status) ? matchJob.job_id : null
  const { data: polledMatch } = useSWR(
    matchPollKey ? `match-${matchPollKey}` : null,
    () => getMatchResult(matchJob!.job_id), { refreshInterval: 1500 },
  )
  useEffect(() => { if (polledMatch) setMatchJob(polledMatch) }, [polledMatch])

  const canMatch =
    imageJob?.status === 'done' && audioJob?.status === 'done' &&
    !matchStarting && !(matchJob && !DONE.includes(matchJob.status))

  const handleMatch = async () => {
    if (!imageJob || !audioJob) return
    setMatchStarting(true); setMatchError(null); setMatchJob(null)
    try {
      const j = await startMatch(imageJob.job_id, audioJob.job_id, tempo)
      setMatchJob({ job_id: j.job_id, status: j.status } as MatchJob)
    } catch (e: any) { setMatchError(e.message) } finally { setMatchStarting(false) }
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-10 space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight"> Violin Practice Evaluator</h1>
          <p className="text-gray-500 mt-1">อัปโหลดโน้ตเพลง + คลิปเสียงที่เล่น - ระบบบอกว่าเล่นถูก/เพี้ยน/ตกตรงไหน</p>
        </div>
        <label className="flex items-center gap-2 text-sm bg-white border border-gray-200 rounded-xl px-3 py-2">
          <span className="text-gray-600 font-medium">Tempo</span>
          <input type="number" min={20} max={300} value={tempo}
            onChange={(e) => setTempo(Math.max(20, Math.min(300, Number(e.target.value) || 120)))}
            className="w-20 text-right font-mono border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-teal-300" />
          <span className="text-gray-400">BPM</span>
        </label>
      </div>

      <CpuWarningBanner />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sheet music  Audiveris */}
        <section className="space-y-3 bg-gray-50 rounded-2xl p-4 border border-gray-200">
          <h2 className="font-semibold text-gray-700"> จากภาพโน้ตเพลง (Audiveris)</h2>
          <UploadZone onFile={handleImageFile} disabled={imageBusy} preview={imagePreview} />
          <button onClick={handleImageSubmit} disabled={!imageFile || imageBusy}
            className="w-full py-3 bg-teal-600 text-white rounded-xl font-semibold hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {imageBusy ? 'กำลังประมวลผล…' : 'แสดงโน้ต'}
          </button>
          {imageError && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{imageError}</div>}
          {imageJob && (
            <div className="space-y-3">
              <ProcessingStatus status={imageJob.status} engine={imageJob.engine} duration={imageJob.duration_sec} error={imageJob.error} />
              {imageJob.status === 'done' && (<><NotesView notes={imageJob.notes ?? []} /><DownloadButtons jobId={imageJob.job_id} /></>)}
            </div>
          )}
        </section>

        {/* Audio  CREPE */}
        <section className="space-y-3 bg-gray-50 rounded-2xl p-4 border border-gray-200">
          <h2 className="font-semibold text-gray-700"> จากคลิปเสียง (CREPE)</h2>
          <AudioUpload onFile={handleAudioFile} disabled={audioBusy} selectedName={audioFile?.name ?? null} />
          <button onClick={handleAudioSubmit} disabled={!audioFile || audioBusy}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {audioBusy ? 'กำลังประมวลผล…' : 'แสดงโน้ต'}
          </button>
          {audioError && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{audioError}</div>}
          {audioJob && (
            <div className="space-y-3">
              <ProcessingStatus status={audioJob.status}
                engine={audioJob.model === 'crepe-finetuned' ? 'CREPE (violin fine-tuned)' : 'CREPE'}
                duration={audioJob.process_duration_sec} error={audioJob.error} />
              {audioJob.status === 'done' && <AudioNotesView events={audioJob.note_events ?? []} />}
            </div>
          )}
        </section>
      </div>

      {/* Match */}
      {(imageJob?.status === 'done' || audioJob?.status === 'done') && (
        <section className="space-y-3 pt-6 border-t border-gray-200">
          <h2 className="font-semibold text-gray-700"> เทียบเสียงกับโน้ต (DTW)</h2>
          <button onClick={handleMatch} disabled={!canMatch}
            className="w-full py-3 bg-fuchsia-600 text-white rounded-xl font-semibold hover:bg-fuchsia-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {matchJob && !DONE.includes(matchJob.status) ? 'กำลังเทียบ…'
              : !canMatch ? 'ต้องประมวลผลทั้งโน้ตและเสียงให้เสร็จก่อน' : 'เทียบเสียงกับโน้ต'}
          </button>
          {matchError && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{matchError}</div>}
          {matchJob?.status === 'error' && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{matchJob.error}</div>}
          {matchJob?.status === 'done' && imageJob?.status === 'done' && audioJob?.status === 'done' && (
            <div className="space-y-3">
              <SyncedScorePlayer
                omrJobId={imageJob.job_id}
                audioJobId={audioJob.job_id}
                matchResult={matchJob}
              />
              <button
                onClick={() => setShowDetails((v) => !v)}
                className="text-sm text-gray-500 underline hover:text-gray-700"
              >
                {showDetails ? 'ซ่อนรายละเอียดราย note' : 'ดูรายละเอียดราย note'}
              </button>
              {showDetails && <MatchView data={matchJob} />}
            </div>
          )}
        </section>
      )}
    </main>
  )
}
