import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import { toTitleCase, API } from '../utils'
import IngredientChip from './IngredientChip'
import type { Upload } from '../types'

export interface UploadZoneHandle {
  removeByIngredient: (ingredient: string) => void
}

interface UploadZoneProps {
  initialUploads?: Upload[]
  onUploadsChange?: (uploads: Upload[]) => void
}

const UploadZone = forwardRef<UploadZoneHandle, UploadZoneProps>(
  ({ initialUploads, onUploadsChange }, ref) => {
    const [dragOver, setDragOver] = useState(false)
    const [uploads, setUploads] = useState<Upload[]>(initialUploads ?? [])
    const inputRef = useRef<HTMLInputElement>(null)

    const onUploadsChangeRef = useRef(onUploadsChange)
    useEffect(() => { onUploadsChangeRef.current = onUploadsChange })
    useEffect(() => {
      onUploadsChangeRef.current?.(uploads.filter(u => !u.detecting))
    }, [uploads])

    const allUrlsRef = useRef<Set<string>>(new Set(initialUploads?.map(u => u.url)))
    const abortControllersRef = useRef<Map<string, AbortController>>(new Map())
    useEffect(() => () => {
      abortControllersRef.current.forEach(c => c.abort())
    }, [])

    const processFile = async (file: File) => {
      if (!file.type.startsWith('image/')) return

      const id = crypto.randomUUID()
      const url = URL.createObjectURL(file)
      allUrlsRef.current.add(url)

      const controller = new AbortController()
      abortControllersRef.current.set(id, controller)

      const entry: Upload = { id, url, ingredient: null, detecting: true }
      setUploads((prev) => [...prev, entry])

      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await fetch(`${API}/api/detect`, { method: 'POST', body: formData, signal: controller.signal })
        if (res.ok) {
          const data = await res.json() as { ingredients: string[] }
          const raw = (data.ingredients?.[0] ?? '').trim()
          const ingredient = raw ? toTitleCase(raw) : null
          setUploads((prev) => prev.map((u) => u.id === id ? { ...u, ingredient, detecting: false } : u))
        } else {
          setUploads((prev) => prev.map((u) => u.id === id ? { ...u, detecting: false } : u))
        }
      } catch (err) {
        if ((err as { name?: string }).name === 'AbortError') return
        console.error('Detection failed:', err)
        setUploads((prev) => prev.map((u) => u.id === id ? { ...u, detecting: false } : u))
      } finally {
        abortControllersRef.current.delete(id)
      }
    }

    const removeById = (id: string) => {
      abortControllersRef.current.get(id)?.abort()
      abortControllersRef.current.delete(id)
      setUploads((prev) => {
        const removed = prev.find(u => u.id === id)
        if (removed) {
          URL.revokeObjectURL(removed.url)
          allUrlsRef.current.delete(removed.url)
        }
        return prev.filter((u) => u.id !== id)
      })
    }

    const removeByIngredient = (ingredient: string) => {
      setUploads((prev) => {
        prev
          .filter(u => u.ingredient?.toLowerCase() === ingredient.toLowerCase())
          .forEach(u => {
            URL.revokeObjectURL(u.url)
            allUrlsRef.current.delete(u.url)
          })
        return prev.filter((u) => u.ingredient?.toLowerCase() !== ingredient.toLowerCase())
      })
    }

    useImperativeHandle(ref, () => ({ removeByIngredient }))

    const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setDragOver(false)

      if (e.dataTransfer.files.length > 0) {
        Array.from(e.dataTransfer.files).forEach(f => void processFile(f))
        return
      }

      const uri = e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/plain')
      if (uri) {
        if (!uri.startsWith('https://') && !uri.startsWith('http://')) return
        try {
          const res = await fetch(uri)
          const blob = await res.blob()
          if (!blob.type.startsWith('image/')) return
          const file = new File([blob], 'dragged-image.jpg', { type: blob.type })
          processFile(file)
        } catch {
          alert('Could not load that image due to browser restrictions. Save it to your device and upload it instead.')
        }
      }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) Array.from(e.target.files).forEach(f => void processFile(f))
      e.target.value = ''
    }

    const anyDetecting = uploads.some((u) => u.detecting)
    const detectedUploads = uploads.filter((u) => u.ingredient !== null)

    return (
      <div>
        <div
          className={`upload-zone${dragOver ? ' drag-over' : ''}`}
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="upload-icon">📷</div>
          <p>
            <strong>Click to browse</strong> or drag &amp; drop<br />
            your fridge / pantry photo here
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={handleChange}
          />
        </div>

        {uploads.length > 0 && (
          <div className="photo-thumbs">
            {uploads.map((u) => (
              <div className="thumb" key={u.id}>
                <img src={u.url} alt={u.ingredient ? `Uploaded: ${u.ingredient}` : u.detecting ? 'Uploaded image (detecting…)' : 'Uploaded image'} />
                <button className="thumb-x" onClick={(e) => { e.stopPropagation(); removeById(u.id) }}>×</button>
              </div>
            ))}
          </div>
        )}

        {anyDetecting && <p className="detecting-msg">Detecting ingredients...</p>}

        {detectedUploads.length > 0 && (
          <div>
            <p className="detected-label">Auto-detected:</p>
            <div className="detected-chips">
              {detectedUploads.map((u) => (
                <IngredientChip
                  key={u.id}
                  label={u.ingredient!}
                  onRemove={() => removeByIngredient(u.ingredient!)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }
)

export default UploadZone
