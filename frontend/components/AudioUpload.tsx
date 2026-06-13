'use client'
import { useRef, useState } from 'react'

const ACCEPT = 'audio/*,.wav,.mp3,.m4a,.flac,.ogg'
const MAX_MB = 50

interface Props {
  onFile: (f: File) => void
  disabled?: boolean
  selectedName?: string | null
}

export default function AudioUpload({ onFile, disabled, selectedName }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const handle = (file: File) => {
    if (file.size > MAX_MB * 1024 * 1024) {
      alert(`File exceeds ${MAX_MB} MB limit`)
      return
    }
    onFile(file)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handle(file)
  }

  return (
    <div
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer
        ${dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 bg-white hover:border-gray-400'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        disabled={disabled}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handle(f) }}
      />
      {selectedName ? (
        <div className="text-sm">
          <div className="text-2xl mb-1"></div>
          <div className="font-medium text-gray-700 truncate">{selectedName}</div>
          <div className="text-xs text-gray-400 mt-1">click to choose another</div>
        </div>
      ) : (
        <div className="space-y-1 text-gray-500">
          <div className="text-3xl"></div>
          <div className="font-medium">Drop or click to select audio</div>
          <div className="text-xs">WAV / MP3 / M4A / FLAC - max {MAX_MB} MB</div>
        </div>
      )}
    </div>
  )
}
