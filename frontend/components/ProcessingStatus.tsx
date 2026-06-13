'use client'

interface Props {
  status: string
  engine: string
  duration?: number | null
  error?: string | null
}

const labels: Record<string, string> = {
  queued: 'Queued - waiting to start…',
  running: 'Running OMR engine…',
  done: 'Done',
  error: 'Failed',
}

export default function ProcessingStatus({ status, engine, duration, error }: Props) {
  return (
    <div className={`rounded-xl border p-4 ${
      status === 'error' ? 'border-red-300 bg-red-50' :
      status === 'done'  ? 'border-green-300 bg-green-50' :
                           'border-yellow-300 bg-yellow-50'
    }`}>
      <div className="flex items-center gap-3">
        {status === 'running' && (
          <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
        )}
        <div>
          <span className="font-medium">{labels[status] ?? status}</span>
          {' '}
          <span className="text-sm text-gray-500">({engine})</span>
        </div>
        {duration != null && (
          <span className="ml-auto text-sm text-gray-500">{duration.toFixed(1)}s</span>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  )
}
