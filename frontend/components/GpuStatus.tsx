'use client'
import useSWR from 'swr'
import { getGpuStatus } from '@/lib/api'

export default function GpuStatus() {
  const { data: gpus = [] } = useSWR('gpu-status', getGpuStatus, { refreshInterval: 5000 })

  if (gpus.length === 0) return null

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">GPU Status</h2>
      <div className="flex gap-4 flex-wrap">
        {gpus.map((g: any) => (
          <div key={g.id} className="flex-1 min-w-[200px] bg-gray-50 rounded-lg p-3">
            <div className="font-medium text-sm truncate">{g.name} (GPU {g.id})</div>
            <div className="mt-2 space-y-1 text-xs text-gray-600">
              <div className="flex justify-between">
                <span>VRAM</span>
                <span>{g.memory_used_mb} / {g.memory_total_mb} MB</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-teal-500 h-1.5 rounded-full"
                  style={{ width: `${(g.memory_used_mb / g.memory_total_mb) * 100}%` }}
                />
              </div>
              <div className="flex justify-between">
                <span>Utilization</span>
                <span>{g.gpu_util_pct}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
