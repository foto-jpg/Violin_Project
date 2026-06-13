'use client'
import { downloadUrl } from '@/lib/api'

export default function DownloadButtons({ jobId }: { jobId: string }) {
  return (
    <div className="flex gap-3 flex-wrap">
      <a
        href={downloadUrl(jobId, 'musicxml')}
        download
        className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 transition-colors"
      >
        Download MusicXML
      </a>
      <a
        href={downloadUrl(jobId, 'midi')}
        download
        className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
      >
        Download MIDI
      </a>
    </div>
  )
}
