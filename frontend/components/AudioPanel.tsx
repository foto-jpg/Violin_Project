'use client'
import { useCallback, useEffect, useState } from 'react'
import useSWR from 'swr'

import AudioUpload from '@/components/AudioUpload'
import ProcessingStatus from '@/components/ProcessingStatus'
import AudioNotesView, { type AudioNoteEvent } from '@/components/AudioNotesView'
import { submitAudio, getAudioResult } from '@/lib/api'

type AudioJob = {
  job_id: string
  status: string
  device?: string | null
  model?: string | null
  audio_duration_sec?: number | null
  num_voiced_frames?: number | null
  num_frames?: number | null
  note_events?: AudioNoteEvent[] | null
  process_duration_sec?: number | null
  error?: string | null
}

interface Props {
  tempo: number
}

export default function AudioPanel({ tempo }: Props) {
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [audioJob, setAudioJob] = useState<AudioJob | null>(null)
  const [audioError, setAudioError] = useState<string | null>(null)
  const [audioSubmitting, setAudioSubmitting] = useState(false)

  const audioPollKey = audioJob && !['done', 'error'].includes(audioJob.status) ? audioJob.job_id : null
  const { data: polledAudio } = useSWR(
    audioPollKey ? `audio-${audioPollKey}` : null,
    () => getAudioResult(audioJob!.job_id),
    { refreshInterval: 1500 },
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
    } catch (e: any) {
      setAudioError(e.message)
    } finally {
      setAudioSubmitting(false)
    }
  }

  const audioBusy = audioSubmitting || (!!audioJob && !['done', 'error'].includes(audioJob.status))

  return (
    <section className="space-y-3 bg-gray-50 rounded-2xl p-4 border border-gray-200">
      <h2 className="font-semibold text-gray-700"> จากคลิปเสียง - โมเดล CREPE (fine-tuned สำหรับไวโอลิน)</h2>

      <AudioUpload
        onFile={handleAudioFile}
        disabled={audioBusy}
        selectedName={audioFile?.name ?? null}
      />

      <button
        onClick={handleAudioSubmit}
        disabled={!audioFile || audioBusy}
        className="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {audioBusy ? 'กำลังประมวลผล…' : 'แสดงโน้ต'}
      </button>

      {audioError && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          {audioError}
        </div>
      )}

      {audioJob && (
        <div className="space-y-3">
          <ProcessingStatus
            status={audioJob.status}
            engine={audioJob.model === 'crepe-finetuned' ? 'CREPE (violin fine-tuned)' : 'CREPE'}
            duration={audioJob.process_duration_sec}
            error={audioJob.error}
          />
          {audioJob.status === 'done' && (
            <AudioNotesView events={audioJob.note_events ?? []} />
          )}
        </div>
      )}
    </section>
  )
}
