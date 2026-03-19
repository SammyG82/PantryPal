interface SortOption {
  key: string
  label: string
}

const SORT_OPTIONS: SortOption[] = [
  { key: 'match', label: 'Best match' },
  { key: 'health', label: 'Healthiest first' },
]

interface SortBarProps {
  current: string
  onChange: (key: string) => void
  count?: number
}

function SortBar({ current, onChange, count }: SortBarProps) {
  return (
    <div className="sort-bar">
      <span className="sort-label">Sort by</span>
      <div className="sort-tabs">
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            className={`sort-tab${current === opt.key ? ' active' : ''}`}
            onClick={() => onChange(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      {count !== undefined && (
        <span className="results-count">{count} recipe{count !== 1 ? 's' : ''} found</span>
      )}
    </div>
  )
}

export default SortBar
