'use client'

export type AlignedNote = {
  index: number
  expected_midi: number
  expected_name: string
  start_sec: number
  end_sec: number
  played_midi: number
  played_name: string
  pitch_diff_cents: number
  voiced_fraction: number
  status?: 'correct' | 'wrong_pitch' | 'missed'
}

export type MatchResult = {
  audio_duration_sec: number
  tempo_bpm: number
  expected_count: number
  aligned_count: number
  summary: { correct: number; wrong_pitch: number; missed: number }
  notes: AlignedNote[]
}

const STEP_COLOR: Record<string, string> = {
  C: 'bg-rose-100 text-rose-700 border-rose-200',
  D: 'bg-orange-100 text-orange-700 border-orange-200',
  E: 'bg-amber-100 text-amber-700 border-amber-200',
  F: 'bg-lime-100 text-lime-700 border-lime-200',
  G: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  A: 'bg-sky-100 text-sky-700 border-sky-200',
  B: 'bg-violet-100 text-violet-700 border-violet-200',
}

const stepOf = (name: string) => (name.match(/^[A-G]/)?.[0] ?? 'C')

function classify(n: AlignedNote): { label: string; cls: string } {
  if (n.voiced_fraction < 0.3) return { label: 'missed', cls: 'bg-gray-100 text-gray-500' }
  if (Math.abs(n.pitch_diff_cents) > 50) return { label: 'wrong', cls: 'bg-red-100 text-red-700' }
  return { label: 'ok', cls: 'bg-emerald-100 text-emerald-700' }
}

function fmtTime(s: number) {
  const mm = Math.floor(s / 60)
  const ss = (s - mm * 60).toFixed(2).padStart(5, '0')
  return `${mm}:${ss}`
}

export default function MatchView({ data }: { data: MatchResult }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex flex-wrap items-center gap-4 text-sm">
        <span className="font-semibold text-gray-700">
          {data.aligned_count}/{data.expected_count} notes aligned
        </span>
        <span className="px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-700">
           {data.summary.correct} correct
        </span>
        <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-700">
           {data.summary.wrong_pitch} wrong pitch
        </span>
        <span className="px-2 py-0.5 rounded-md bg-gray-100 text-gray-500">
          - {data.summary.missed} missed
        </span>
        <span className="ml-auto text-xs text-gray-400">tempo {data.tempo_bpm} BPM</span>
      </div>
      <div className="max-h-[480px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide sticky top-0">
            <tr>
              <th className="px-3 py-2 text-left">#</th>
              <th className="px-3 py-2 text-left">Expected</th>
              <th className="px-3 py-2 text-left">Played</th>
              <th className="px-3 py-2 text-left">Time</th>
              <th className="px-3 py-2 text-right">Δ cents</th>
              <th className="px-3 py-2 text-right">Voiced</th>
              <th className="px-3 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.notes.map((n) => {
              const cls = classify(n)
              const ec = STEP_COLOR[stepOf(n.expected_name)] || 'bg-gray-100'
              const pc = STEP_COLOR[stepOf(n.played_name)] || 'bg-gray-100'
              return (
                <tr key={n.index}>
                  <td className="px-3 py-2 font-mono text-xs text-gray-400">{n.index + 1}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex items-baseline gap-0.5 px-2 py-0.5 rounded-md border text-sm font-mono ${ec}`}>
                      <span className="font-semibold">{n.expected_name.replace(/\d+$/, '')}</span>
                      <sub className="text-[10px] opacity-70">{n.expected_name.match(/\d+$/)?.[0]}</sub>
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex items-baseline gap-0.5 px-2 py-0.5 rounded-md border text-sm font-mono ${pc}`}>
                      <span className="font-semibold">{n.played_name.replace(/\d+$/, '')}</span>
                      <sub className="text-[10px] opacity-70">{n.played_name.match(/\d+$/)?.[0]}</sub>
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">
                    {fmtTime(n.start_sec)}-{fmtTime(n.end_sec)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-gray-600">
                    {n.pitch_diff_cents > 0 ? '+' : ''}{n.pitch_diff_cents.toFixed(0)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-gray-400">
                    {(n.voiced_fraction * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${cls.cls}`}>
                      {cls.label}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
