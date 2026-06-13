'use client'

type Engine = 'oemer' | 'audiveris'

const engines: { id: Engine; label: string; description: string }[] = [
  {
    id: 'oemer',
    label: 'oemer',
    description: 'Deep-learning based, GPU-accelerated. Best for clean printed scores.',
  },
  {
    id: 'audiveris',
    label: 'Audiveris',
    description: 'Rule-based Java engine. Robust for complex layouts, no GPU required.',
  },
]

interface Props {
  value: Engine
  onChange: (e: Engine) => void
  disabled?: boolean
}

export default function EngineSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="flex gap-3 flex-wrap">
      {engines.map((e) => (
        <label
          key={e.id}
          className={`flex-1 min-w-[200px] border-2 rounded-xl p-4 cursor-pointer transition-colors ${
            value === e.id
              ? 'border-teal-500 bg-teal-50'
              : 'border-gray-200 bg-white hover:border-gray-300'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input
            type="radio"
            name="engine"
            value={e.id}
            checked={value === e.id}
            onChange={() => !disabled && onChange(e.id)}
            className="sr-only"
            disabled={disabled}
          />
          <div className="font-semibold">{e.label}</div>
          <div className="text-sm text-gray-500 mt-1">{e.description}</div>
        </label>
      ))}
    </div>
  )
}
