'use client'
import { useEffect, useRef, useState } from 'react'

interface Props {
  musicxml: string
}

export default function ResultViewer({ musicxml }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!musicxml || !containerRef.current) return

    let cancelled = false
    setLoading(true)
    setError(null)

    // Clear previous render
    containerRef.current.innerHTML = ''

    import('opensheetmusicdisplay').then(({ OpenSheetMusicDisplay }) => {
      if (cancelled || !containerRef.current) return

      const osmd = new OpenSheetMusicDisplay(containerRef.current, {
        autoResize: true,
        drawTitle: true,
        backend: 'svg',
      })

      osmd
        .load(musicxml)
        .then(() => {
          if (cancelled) return
          osmd.render()
          setLoading(false)
        })
        .catch((e: any) => {
          console.error('OSMD load/render error:', e)
          if (!cancelled) {
            setError(e?.message ?? String(e))
            setLoading(false)
          }
        })
    }).catch((e) => {
      console.error('OSMD import error:', e)
      if (!cancelled) {
        setError('Failed to load OSMD library')
        setLoading(false)
      }
    })

    return () => { cancelled = true }
  }, [musicxml])

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-auto relative min-h-[200px]">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 animate-pulse bg-white/80 z-10">
          Rendering sheet music…
        </div>
      )}
      {error && (
        <div className="p-4 text-sm text-red-600 bg-red-50 border-b border-red-200">
          OSMD render error: {error}. The MusicXML file may still be valid - try the download buttons.
        </div>
      )}
      <div ref={containerRef} className="p-4 min-h-[200px]" />
    </div>
  )
}
