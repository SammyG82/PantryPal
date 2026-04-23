import { useState } from 'react'
import { toTitleCase } from '../utils'

const API = import.meta.env.VITE_API_URL ?? ''

interface IngredientInputProps {
  onAdd: (value: string) => void
}

function IngredientInput({ onAdd }: IngredientInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = async () => {
    const trimmed = toTitleCase(value)
    if (!trimmed) return
    setValue('')

    try {
      const res = await fetch(`${API}/api/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredient: trimmed }),
      })
      if (res.ok) {
        const data = await res.json() as { corrected: string }
        onAdd(toTitleCase(data.corrected))
      } else {
        onAdd(trimmed)
      }
    } catch {
      onAdd(trimmed)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') void handleSubmit()
  }

  return (
    <div className="text-row">
      <input
        type="text"
        placeholder="e.g. chicken, tomatoes..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button className="add-btn" onClick={() => void handleSubmit()}>
        Add
      </button>
    </div>
  )
}

export default IngredientInput
