'use client'

export type AudioNoteEvent = {
  start_sec: number
  duration_sec: number
  midi: number
  frequency: number
  step: string
  accidental: string
  name: string
  octave: number
  name_with_octave: string
  confidence: number
  beats?: number | null
  note_value?: string
}

const STEP_COLOR: Record<string, string> = {
  C: 'bg-rose-100  text-rose-700  border-rose-200',
  D: 'bg-orange-100 text-orange-700 border-orange-200',
  E: 'bg-amber-100  text-amber-700  border-amber-200',
  F: 'bg-lime-100   text-lime-700   border-lime-200',
  G: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  A: 'bg-sky-100    text-sky-700    border-sky-200',
  B: 'bg-violet-100 text-violet-700 border-violet-200',
}

function fmtTime(s: number): string {
  const mm = Math.floor(s / 60)
  const ss = (s - mm * 60).toFixed(2).padStart(5, '0')
  return `${mm}:${ss}`
}

export default function AudioNotesView({ events }: { events: AudioNoteEvent[] }) {
  if (!events || events.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center text-gray-400">
        No pitch detected (audio might be silent or below confidence threshold).
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          {events.length} note event{events.length === 1 ? '' : 's'} detected
        </span>
        <span className="text-xs text-gray-400">CREPE pitch tracking</span>
      </div>

      <div className="max-h-[480px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-3 py-2 text-left">Time</th>
              <th className="px-3 py-2 text-left">Note</th>
              <th className="px-3 py-2 text-left">Value</th>
              <th className="px-3 py-2 text-right">Hz</th>
              <th className="px-3 py-2 text-right">Dur</th>
              <th className="px-3 py-2 text-right">Conf</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {events.map((e, i) => {
              const colour = STEP_COLOR[e.step] || 'bg-gray-100 text-gray-700 border-gray-200'
              const value = e.note_value
                ? `${e.note_value}${e.beats != null ? ` (${e.beats.toFixed(2)})` : ''}`
                : '-'
              return (
                <tr key={i}>
                  <td className="px-3 py-2 font-mono text-xs text-gray-500">{fmtTime(e.start_sec)}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex items-baseline gap-0.5 px-2 py-0.5 rounded-md border text-sm font-mono ${colour}`}>
                      <span className="font-semibold">{e.name}</span>
                      <sub className="text-[10px] opacity-70">{e.octave}</sub>
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600">{value}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-gray-600">{e.frequency.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-gray-600">{e.duration_sec.toFixed(2)}s</td>
                  <td className="px-3 py-2 text-right font-mono text-xs text-gray-400">{(e.confidence * 100).toFixed(0)}%</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
