// Local dev goes through the Next.js proxy route (/api/backend/*  backend /api/*).
// On HF (static export) the frontend is same-origin with FastAPI, so call /api directly.
const isHF = process.env.NEXT_PUBLIC_HF === '1'
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? (isHF ? '/api' : '/api/backend')

// Exported for components that build their own URLs (e.g. <audio src>, OSMD fetch).
export const API_BASE = BASE

export async function submitJob(file: File, engine: 'audiveris' | 'oemer', tempo = 120): Promise<{ job_id: string; status: string }> {
  const form = new FormData()
  form.append('file', file)
  form.append('engine', engine)
  form.append('tempo', String(tempo))
  const res = await fetch(`${BASE}/omr/process`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function getResult(jobId: string) {
  const res = await fetch(`${BASE}/omr/result/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch result')
  return res.json()
}

export async function getGpuStatus() {
  const res = await fetch(`${BASE}/gpu-status`)
  if (!res.ok) return []
  return res.json()
}

export function downloadUrl(jobId: string, format: 'musicxml' | 'midi') {
  return `${BASE}/omr/download/${jobId}/${format}`
}

export async function submitAudio(file: File, tempo = 120): Promise<{ job_id: string; status: string }> {
  const form = new FormData()
  form.append('file', file)
  form.append('tempo', String(tempo))
  const res = await fetch(`${BASE}/audio/process`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Audio upload failed')
  }
  return res.json()
}

export async function getAudioResult(jobId: string) {
  const res = await fetch(`${BASE}/audio/result/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch audio result')
  return res.json()
}

// Match is async (background job + polling) - start returns a job_id, then poll result.
export async function startMatch(
  omrJobId: string, audioJobId: string, tempo: number,
): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${BASE}/match`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ omr_job_id: omrJobId, audio_job_id: audioJobId, tempo }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Match failed')
  }
  return res.json()
}

export async function getMatchResult(jobId: string) {
  const res = await fetch(`${BASE}/match/result/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch match result')
  return res.json()
}
