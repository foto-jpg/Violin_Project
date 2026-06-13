'use client'

export type Note = {
  measure: number | null
  step: string
  accidental: string
  name: string
  octave: number
  name_with_octave: string
  midi: number
  duration: number          // quarter-lengths
  note_value?: string       // 'quarter' / 'eighth' / ...
  seconds?: number | null
}

const VALUE_ABBR: Record<string, string> = {
  whole: '𝅝', 'dotted-half': '𝅗𝅥.', half: '𝅗𝅥',
  'dotted-quarter': '.', quarter: '',
  'dotted-eighth': '.', eighth: '',
  '16th': '𝅘𝅥𝅯', '32nd': '𝅘𝅥𝅰',
}

// Pastel colour per pitch class for quick visual scanning
const STEP_COLOR: Record<string, string> = {
  C: 'bg-rose-100  text-rose-700  border-rose-200',
  D: 'bg-orange-100 text-orange-700 border-orange-200',
  E: 'bg-amber-100  text-amber-700  border-amber-200',
  F: 'bg-lime-100   text-lime-700   border-lime-200',
  G: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  A: 'bg-sky-100    text-sky-700    border-sky-200',
  B: 'bg-violet-100 text-violet-700 border-violet-200',
}

function groupByMeasure(notes: Note[]): Map<number, Note[]> {
  const m = new Map<number, Note[]>()
  for (const n of notes) {
    const key = n.measure ?? 0
    if (!m.has(key)) m.set(key, [])
    m.get(key)!.push(n)
  }
  return m
}

export default function NotesView({ notes }: { notes: Note[] }) {
  if (!notes || notes.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center text-gray-400">
        No notes detected.
      </div>
    )
  }

  const grouped = groupByMeasure(notes)
  const measureNumbers = Array.from(grouped.keys()).sort((a, b) => a - b)

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          {notes.length} note{notes.length === 1 ? '' : 's'} • {measureNumbers.length} measure{measureNumbers.length === 1 ? '' : 's'}
        </span>
        <span className="text-xs text-gray-400">grouped by measure</span>
      </div>

      <div className="max-h-[480px] overflow-auto divide-y divide-gray-100">
        {measureNumbers.map((mNum) => {
          const items = grouped.get(mNum)!
          return (
            <div key={mNum} className="px-4 py-3 flex gap-3 items-start">
              <div className="w-12 flex-shrink-0 text-xs text-gray-400 font-mono pt-1">
                m. {mNum || '?'}
              </div>
              <div className="flex flex-wrap gap-1.5 flex-1">
                {items.map((n, i) => {
                  const colour = STEP_COLOR[n.step] || 'bg-gray-100 text-gray-700 border-gray-200'
                  const valAbbr = n.note_value ? (VALUE_ABBR[n.note_value] ?? '') : ''
                  const secTxt = n.seconds != null ? `, ${n.seconds.toFixed(2)}s` : ''
                  return (
                    <span
                      key={i}
                      title={`${n.name_with_octave} - ${n.note_value || `${n.duration} beats`} (MIDI ${n.midi}${secTxt})`}
                      className={`inline-flex items-baseline gap-0.5 px-2 py-1 rounded-md border text-sm font-mono ${colour}`}
                    >
                      <span className="font-semibold">{n.name}</span>
                      <sub className="text-[10px] opacity-70">{n.octave}</sub>
                      {valAbbr && <span className="ml-0.5 text-[11px] opacity-60">{valAbbr}</span>}
                    </span>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
