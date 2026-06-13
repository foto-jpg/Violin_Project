'use client'
import { useCallback, useState } from 'react'

import UploadZone from '@/components/UploadZone'
import ProcessingStatus from '@/components/ProcessingStatus'
import NotesView, { type Note } from '@/components/NotesView'
import DownloadButtons from '@/components/DownloadButtons'
import { submitJob, getResult } from '@/lib/api'

type Engine = 'oemer' | 'audiveris'

type OmrJob = {
  job_id: string
  status: string
  engine: Engine
  notes?: Note[] | null
  duration_sec?: number | null
  gpu_used?: number | null
  error?: string | null
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

// Submit one OMR job, then poll until it finishes. Calls onUpdate on every
// status change so the UI can show progress. The backend only runs one job at
// a time (HTTP 429 otherwise), so callers must await each engine in turn.
async function runOmrAndWait(
  file: File,
  engine: Engine,
  tempo: number,
  onUpdate: (j: OmrJob) => void,
): Promise<OmrJob> {
  const { job_id } = await submitJob(file, engine, tempo)
  let job: OmrJob = { job_id, status: 'queued', engine }
  onUpdate(job)
  while (!['done', 'error'].includes(job.status)) {
    await sleep(1500)
    const r = await getResult(job_id)
    job = { ...r, engine }
    onUpdate(job)
  }
  return job
}

// Longest-common-subsequence length over two MIDI sequences - order-aware
// agreement that tolerates insertions/deletions (a dropped note shifts the
// rest, which position-wise comparison would wrongly count as all-wrong).
function lcsLength(a: number[], b: number[]): number {
  const dp = Array(b.length + 1).fill(0)
  for (let i = 1; i <= a.length; i++) {
    let prev = 0
    for (let j = 1; j <= b.length; j++) {
      const tmp = dp[j]
      dp[j] = a[i - 1] === b[j - 1] ? prev + 1 : Math.max(dp[j], dp[j - 1])
      prev = tmp
    }
  }
  return dp[b.length]
}

function midiSeq(notes?: Note[] | null): number[] {
  return (notes ?? []).map((n) => n.midi)
}

function measureCount(notes?: Note[] | null): number {
  return new Set((notes ?? []).map((n) => n.measure ?? 0)).size
}

interface Props {
  tempo: number
}

export default function ImageCompare({ tempo }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [oemer, setOemer] = useState<OmrJob | null>(null)
  const [audiveris, setAudiveris] = useState<OmrJob | null>(null)

  const handleFile = useCallback((f: File) => {
    setFile(f)
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return URL.createObjectURL(f)
    })
    setOemer(null)
    setAudiveris(null)
    setError(null)
  }, [])

  const handleCompare = async () => {
    if (!file) return
    setRunning(true)
    setError(null)
    setOemer(null)
    setAudiveris(null)
    try {
      // Sequential - the backend rejects a second job while one is running.
      await runOmrAndWait(file, 'oemer', tempo, setOemer)
      await runOmrAndWait(file, 'audiveris', tempo, setAudiveris)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const bothDone = oemer?.status === 'done' && audiveris?.status === 'done'
  const seqA = midiSeq(oemer?.notes)
  const seqB = midiSeq(audiveris?.notes)
  const lcs = bothDone ? lcsLength(seqA, seqB) : 0
  const agreement =
    bothDone && seqA.length + seqB.length > 0
      ? (2 * lcs) / (seqA.length + seqB.length)
      : 0

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <UploadZone onFile={handleFile} disabled={running} preview={preview} />
        <button
          onClick={handleCompare}
          disabled={!file || running}
          className="w-full py-3 bg-teal-600 text-white rounded-xl font-semibold hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {running ? 'กำลังรันทั้งสองโมเดล…' : 'เปรียบเทียบ oemer  Audiveris'}
        </button>
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </div>
        )}
      </section>

      {/* ── Comparison summary (research metrics) ─────────────────────── */}
      {bothDone && (
        <section className="bg-white border border-gray-200 rounded-2xl p-5 space-y-4">
          <h3 className="font-semibold text-gray-700"> สรุปการเปรียบเทียบ</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200">
                  <th className="py-2 pr-4 font-medium">เมตริก</th>
                  <th className="py-2 px-4 font-medium text-teal-700">oemer</th>
                  <th className="py-2 px-4 font-medium text-violet-700">Audiveris</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                <tr className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-sans text-gray-600">จำนวนโน้ตที่ตรวจพบ</td>
                  <td className="py-2 px-4">{seqA.length}</td>
                  <td className="py-2 px-4">{seqB.length}</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-sans text-gray-600">จำนวนห้อง (measures)</td>
                  <td className="py-2 px-4">{measureCount(oemer?.notes)}</td>
                  <td className="py-2 px-4">{measureCount(audiveris?.notes)}</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-sans text-gray-600">เวลาที่ใช้ (วินาที)</td>
                  <td className="py-2 px-4">{oemer?.duration_sec?.toFixed(1) ?? '-'}</td>
                  <td className="py-2 px-4">{audiveris?.duration_sec?.toFixed(1) ?? '-'}</td>
                </tr>
                <tr>
                  <td className="py-2 pr-4 font-sans text-gray-600">ใช้ GPU</td>
                  <td className="py-2 px-4">{oemer?.gpu_used != null ? `#${oemer.gpu_used}` : 'ไม่ใช้'}</td>
                  <td className="py-2 px-4">{audiveris?.gpu_used != null ? `#${audiveris.gpu_used}` : 'ไม่ใช้'}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="flex items-center gap-3 pt-1">
            <span className="text-sm text-gray-600">โน้ตที่ทั้งสองโมเดลตรงกัน (LCS):</span>
            <span className="text-lg font-bold text-gray-800">{(agreement * 100).toFixed(1)}%</span>
            <span className="text-xs text-gray-400">({lcs} โน้ตเรียงตรงกัน)</span>
          </div>
        </section>
      )}

      {/* ── Side-by-side engine results ───────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EnginePanel title=" oemer" accent="teal" job={oemer} running={running} />
        <EnginePanel title=" Audiveris" accent="violet" job={audiveris} running={running} />
      </div>
    </div>
  )
}

function EnginePanel({
  title,
  accent,
  job,
  running,
}: {
  title: string
  accent: 'teal' | 'violet'
  job: OmrJob | null
  running: boolean
}) {
  const ring = accent === 'teal' ? 'border-teal-200' : 'border-violet-200'
  return (
    <section className={`space-y-3 bg-gray-50 rounded-2xl p-4 border ${ring}`}>
      <h2 className="font-semibold text-gray-700">{title}</h2>
      {!job && (
        <div className="bg-white border border-dashed border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm">
          {running ? 'กำลังรอคิว…' : 'อัปโหลดภาพแล้วกด “เปรียบเทียบ” เพื่อเริ่ม'}
        </div>
      )}
      {job && (
        <div className="space-y-3">
          <ProcessingStatus
            status={job.status}
            engine={job.engine}
            duration={job.duration_sec}
            error={job.error}
          />
          {job.status === 'done' && (
            <>
              <NotesView notes={job.notes ?? []} />
              <DownloadButtons jobId={job.job_id} />
            </>
          )}
        </div>
      )}
    </section>
  )
}
