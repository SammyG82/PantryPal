interface IngredientChipProps {
  label: string
  onRemove?: () => void
}

function IngredientChip({ label, onRemove }: IngredientChipProps) {
  return (
    <span className="chip">
      {label}
      {onRemove && (
        <button className="chip-x" onClick={onRemove} aria-label={`Remove ${label}`}>
          ×
        </button>
      )}
    </span>
  )
}

export default IngredientChip
