interface IngredientChipProps {
  label: string
  onRemove?: () => void
  unsupported?: boolean
}

function IngredientChip({ label, onRemove, unsupported }: IngredientChipProps) {
  return (
    <span
      className={`chip${unsupported ? ' chip-unsupported' : ''}`}
    >
      {label}
      {unsupported && (
        <span className="chip-warn-icon" aria-label="Ingredient not recognised">
          ⚠
          <span className="chip-tooltip" aria-hidden="true">Ingredient not recognised</span>
        </span>
      )}
      {onRemove && (
        <button className="chip-x" onClick={onRemove} aria-label={`Remove ${label}`}>
          ×
        </button>
      )}
    </span>
  )
}

export default IngredientChip
