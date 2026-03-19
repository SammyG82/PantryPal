import { useState } from 'react'

interface IngredientInputProps {
  onAdd: (value: string) => void
}

function IngredientInput({ onAdd }: IngredientInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed) return
    onAdd(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
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
      <button className="add-btn" onClick={handleSubmit}>
        Add
      </button>
    </div>
  )
}

export default IngredientInput
