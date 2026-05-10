import React, { useState, useRef, useEffect } from 'react'
import { toTitleCase, API } from '../utils'

interface IngredientInputProps {
  onAdd: (value: string, supported: boolean) => void
}

function IngredientInput({ onAdd }: IngredientInputProps) {
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => { abortRef.current?.abort() }, [])

  const handleSubmit = async () => {
    const trimmed = toTitleCase(value)
    if (!trimmed || submitting) return
    setValue('')
    setSubmitting(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const res = await fetch(`${API}/api/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredient: trimmed }),
        signal: controller.signal,
      })
      if (res.ok) {
        const data = await res.json() as { corrected: string; found: boolean }
        onAdd(data.corrected, data.found)
      } else {
        onAdd(trimmed, false)
      }
    } catch (err) {
      if ((err as { name?: string }).name !== 'AbortError') onAdd(trimmed, false)
    } finally {
      setSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') void handleSubmit()
  }

  return (
    <div className="text-row">
      <input
        type="text"
        aria-label="Add an ingredient"
        placeholder="e.g. chicken, tomatoes..."
        value={value}
        disabled={submitting}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button type="button" className="add-btn" disabled={submitting} onClick={() => void handleSubmit()}>
        Add
      </button>
    </div>
  )
}

export default IngredientInput
