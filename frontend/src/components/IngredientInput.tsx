import { useState } from 'react'
import { toTitleCase, API } from '../utils'

interface IngredientInputProps {
  onAdd: (value: string, supported: boolean) => void
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
        const data = await res.json() as { corrected: string; found: boolean }
        onAdd(data.corrected, data.found)
      } else {
        onAdd(trimmed, false)
      }
    } catch {
      onAdd(trimmed, false)
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
      <button type="button" className="add-btn" onClick={() => void handleSubmit()}>
        Add
      </button>
    </div>
  )
}

export default IngredientInput
