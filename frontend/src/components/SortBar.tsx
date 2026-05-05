import type { SortMode } from '../types'

interface SortOption {
  key: SortMode
  label: string
}

const SORT_OPTIONS: SortOption[] = [
  { key: 'match', label: 'Best match' },
  { key: 'health', label: 'Healthiest' },
]

interface SortBarProps {
  current: SortMode
  onChange: (key: SortMode) => void
  count?: number
  searchQuery: string
  onSearchChange: (q: string) => void
}

function SortBar({ current, onChange, count, searchQuery, onSearchChange }: SortBarProps) {
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
      <input
        className="recipe-search"
        type="text"
        placeholder="Search all recipes…"
        aria-label="Search recipes by name"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      {count !== undefined && (
        <span className="results-count">{count} recipe{count !== 1 ? 's' : ''} found</span>
      )}
    </div>
  )
}

export default SortBar
