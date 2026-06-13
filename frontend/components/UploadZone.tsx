'use client'
import { useRef, useState } from 'react'

const ACCEPT = '.png,.jpg,.jpeg,.pdf'
const MAX_MB = 50

interface Props {
  onFile: (f: File) => void
  disabled?: boolean
  preview?: string | null
}

export default function UploadZone({ onFile, disabled, preview }: Props) {
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
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handle(file)
  }

  return (
    <div
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
        ${dragOver ? 'border-teal-400 bg-teal-50' : 'border-gray-300 bg-white hover:border-gray-400'}
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

      {preview ? (
        <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg object-contain" />
      ) : (
        <div className="space-y-2 text-gray-500">
          <div className="text-4xl"></div>
          <div className="font-medium">Drag & drop or click to select</div>
          <div className="text-sm">PNG, JPG, PDF - max {MAX_MB} MB</div>
        </div>
      )}
    </div>
  )
}
