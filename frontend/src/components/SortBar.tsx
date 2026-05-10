import type { SortMode } from '../types'

interface SortOption {
  key: SortMode
  label: string
}

const SORT_OPTIONS: SortOption[] = [
  { key: 'match', label: 'Best match' },
  { key: 'health', label: 'Healthiest' },
]

const FILTER_OPTIONS = [
  { key: 'vegetarian',  label: '🌿 Vegetarian' },
  { key: 'vegan',       label: '🌱 Vegan'      },
  { key: 'gluten_free', label: 'Gluten-free'   },
]

interface SortBarProps {
  current: SortMode
  onChange: (key: SortMode) => void
  count?: number
  searchQuery: string
  onSearchChange: (q: string) => void
  dietaryFilters: string[]
  onDietaryChange: (filters: string[]) => void
}

function SortBar({ current, onChange, count, searchQuery, onSearchChange, dietaryFilters, onDietaryChange }: SortBarProps) {
  const toggleFilter = (key: string) => {
    onDietaryChange(dietaryFilters.includes(key) ? dietaryFilters.filter((f) => f !== key) : [...dietaryFilters, key])
  }

  return (
    <div className="sort-bar">
      <span className="sort-label">Sort by</span>
      <div className="sort-tabs">
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            className={`sort-tab${current === opt.key ? ' active' : ''}`}
            aria-pressed={current === opt.key}
            onClick={() => onChange(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="sort-bar-divider" />

      <div className="sort-tabs">
        {FILTER_OPTIONS.map((f) => (
          <button
            key={f.key}
            className={`sort-tab${dietaryFilters.includes(f.key) ? ' active' : ''}`}
            aria-pressed={dietaryFilters.includes(f.key)}
            onClick={() => toggleFilter(f.key)}
          >
            {f.label}
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
