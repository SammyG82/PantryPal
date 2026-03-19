import { useState, useRef } from 'react'
import IngredientChip from './IngredientChip'

const API = import.meta.env.VITE_API_URL ?? ''

interface Upload {
  id: string
  url: string
  ingredient: string | null
  detecting: boolean
}

interface UploadZoneProps {
  onDetectedChange: (ingredients: string[]) => void
}

function UploadZone({ onDetectedChange }: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [uploads, setUploads] = useState<Upload[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const notify = (updated: Upload[]) => {
    const ingredients = updated
      .map((u) => u.ingredient)
      .filter((ing): ing is string => ing !== null)
    onDetectedChange(ingredients)
  }

  const processFile = async (file: File) => {
    if (!file.type.startsWith('image/')) return

    const id = crypto.randomUUID()
    const url = URL.createObjectURL(file)
    const entry: Upload = { id, url, ingredient: null, detecting: true }

    setUploads((prev) => [...prev, entry])

    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API}/api/detect`, { method: 'POST', body: formData })
      if (res.ok) {
        const data = await res.json() as { ingredients: string[] }
        const ingredient = data.ingredients?.[0] ?? null
        setUploads((prev) => {
          const updated = prev.map((u) =>
            u.id === id ? { ...u, ingredient, detecting: false } : u
          )
          notify(updated)
          return updated
        })
      } else {
        setUploads((prev) => prev.map((u) => u.id === id ? { ...u, detecting: false } : u))
      }
    } catch (err) {
      console.error('Detection failed:', err)
      setUploads((prev) => prev.map((u) => u.id === id ? { ...u, detecting: false } : u))
    }
  }

  const removeById = (id: string) => {
    setUploads((prev) => {
      const updated = prev.filter((u) => u.id !== id)
      notify(updated)
      return updated
    })
  }

  const removeByIngredient = (ingredient: string) => {
    setUploads((prev) => {
      const updated = prev.filter(
        (u) => u.ingredient?.toLowerCase() !== ingredient.toLowerCase()
      )
      notify(updated)
      return updated
    })
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)

    if (e.dataTransfer.files.length > 0) {
      Array.from(e.dataTransfer.files).forEach(processFile)
      return
    }

    const uri = e.dataTransfer.getData('text/uri-list') || e.dataTransfer.getData('text/plain')
    if (uri) {
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
    if (e.target.files) Array.from(e.target.files).forEach(processFile)
    e.target.value = ''
  }

  const anyDetecting = uploads.some((u) => u.detecting)
  const detectedUploads = uploads.filter((u) => u.ingredient !== null)

  return (
    <div>
      <div
        className={`upload-zone${dragOver ? ' drag-over' : ''}`}
        onClick={() => inputRef.current?.click()}
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
              <img src={u.url} alt="upload preview" />
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

export default UploadZone
