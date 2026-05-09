import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import SortBar from '../components/SortBar'
import RecipeCard from '../components/RecipeCard'
import { useFavourites } from '../hooks/useFavourites'
import { API } from '../utils'
import type { Recipe, SortMode } from '../types'

const RECIPES_PER_PAGE = 9

function Results() {
  const location = useLocation()
  const navigate = useNavigate()

  const ingredients: string[] | null = location.state?.ingredients ?? null

  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortMode, setSortMode] = useState<SortMode>('match')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Recipe[] | null>(null)
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [showInfo, setShowInfo] = useState(false)
  const [visibleCount, setVisibleCount] = useState(RECIPES_PER_PAGE)
  const handleSortChange = (mode: SortMode) => { setSortMode(mode); setVisibleCount(RECIPES_PER_PAGE) }
  const { toggleFavourite, isFavourited } = useFavourites()

  useEffect(() => {
    if (!ingredients) return

    const controller = new AbortController()

    const fetchRecipes = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API}/api/recipes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ingredients }),
          signal: controller.signal,
        })
        if (!res.ok) {
          const body = await res.json().catch(() => null) as { detail?: string } | null
          throw new Error(body?.detail ?? `Server error: ${res.status}`)
        }
        const data = await res.json() as Recipe[]
        setRecipes(data)
      } catch (err) {
        if ((err as { name?: string }).name === 'AbortError') return
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    fetchRecipes()
    return () => controller.abort()
  }, [ingredients])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      setSearchError(null)
      setSearching(false)
      setVisibleCount(RECIPES_PER_PAGE)
      return
    }
    const controller = new AbortController()
    setSearchError(null)
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/api/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q: searchQuery, ingredients: ingredients ?? [] }),
          signal: controller.signal,
        })
        if (res.ok) {
          setSearchResults(await res.json() as Recipe[])
        } else {
          const body = await res.json().catch(() => null) as { detail?: string } | null
          setSearchError(body?.detail ?? 'Search failed')
          setSearchResults(null)
        }
      } catch (err) {
        if ((err as { name?: string }).name !== 'AbortError') {
          setSearchResults(null)
          setSearchError('Search failed')
        }
      } finally {
        if (!controller.signal.aborted) setSearching(false)
      }
    }, 300)
    return () => { clearTimeout(timer); controller.abort() }
  }, [searchQuery, ingredients])

  if (!ingredients) return (
    <div>
      <NavBar ingredients={[]} />
      <div className="empty-state empty-state--full">
        <div style={{ fontSize: '2.5rem', marginBottom: '1.25rem' }}>🥗</div>
        <h3>No ingredients yet</h3>
        <p style={{ marginTop: '0.5rem' }}>Head back and upload a photo or type in what you have — we'll find recipes you can make right now.</p>
        <button
          className="btn-terra"
          style={{ marginTop: '1.75rem', padding: '12px 32px', fontSize: '0.95rem' }}
          onClick={() => navigate('/')}
        >
          Add ingredients →
        </button>
      </div>
    </div>
  )

  const isSearching = searchQuery.trim().length > 0
  const displayRecipes = (isSearching && searchResults !== null)
    ? searchResults.filter((r) => r.match_score > 0)
    : recipes
  const sorted = [...displayRecipes]
    .sort((a, b) => sortMode === 'health' ? b.health_score - a.health_score : b.match_score - a.match_score)
  const visible = isSearching ? sorted : sorted.slice(0, visibleCount)
  const hasMore = !isSearching && visibleCount < sorted.length

  return (
    <div>
      <NavBar ingredients={ingredients} />

      <div className="results-header">
        <h1 className="results-title">Your recipe matches</h1>
        <p className="results-sub">
          Based on <strong>{ingredients.join(', ')}</strong>
        </p>
      </div>

      <SortBar
        current={sortMode}
        onChange={handleSortChange}
        count={(loading || searching) ? undefined : visible.length}
        searchQuery={searchQuery}
        onSearchChange={(q) => { setSearchQuery(q); setSearching(q.trim().length > 0) }}
      />

      {searchError && <div className="error-state" style={{ padding: '0.75rem 1.5rem', fontSize: '0.9rem' }}>{searchError}</div>}

      {loading && <div className="loading-state">Finding recipes for you…</div>}

      {error && (
        <div className="error-state">
          Could not load recipes: {error}
          <br />
          <button
            style={{ marginTop: '1rem', padding: '8px 20px', cursor: 'pointer', fontFamily: 'DM Sans, sans-serif' }}
            onClick={() => navigate('/')}
          >
            Go back
          </button>
        </div>
      )}

      {!loading && !error && !searching && visible.length === 0 && (!isSearching || searchResults !== null) && (
        <div className="empty-state">
          {isSearching ? (
            <>
              <div style={{ fontSize: '2.5rem', marginBottom: '1.25rem' }}>🔍</div>
              <h3>No matching recipes</h3>
              <p style={{ marginTop: '0.5rem' }}>None of your ingredients match any <em>"{searchQuery}"</em> recipes. Try a different search or add more ingredients.</p>
            </>
          ) : (
            <>
              <h3>No matches found</h3>
              <p>Try adding more ingredients or different ones.</p>
              <button
                style={{ marginTop: '1.5rem', padding: '10px 28px', cursor: 'pointer', fontFamily: 'DM Sans, sans-serif', background: 'var(--terra)', color: 'white', border: 'none', borderRadius: '50px', fontSize: '0.9rem' }}
                onClick={() => navigate('/')}
              >
                Try again
              </button>
            </>
          )}
        </div>
      )}

      {!loading && !error && visible.length > 0 && (
        <>
          <div className="recipe-grid">
            {visible.map((recipe, i) => (
              <RecipeCard key={recipe.id} recipe={recipe} rank={i + 1} sortMode={sortMode} isFavourited={isFavourited(recipe.id)} onToggleFavourite={toggleFavourite} />
            ))}
          </div>
          {hasMore && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem 0 3rem' }}>
              <button className="btn-terra" style={{ padding: '12px 36px', fontSize: '0.95rem' }} onClick={() => setVisibleCount(c => c + 9)}>
                Load more
              </button>
            </div>
          )}
        </>
      )}

      <button className="info-btn" onClick={() => setShowInfo(true)} aria-label="How scores are calculated">?</button>

      {showInfo && (
        <div className="info-overlay" onClick={() => setShowInfo(false)}>
          <div className="info-modal" onClick={e => e.stopPropagation()}>
            <div className="info-modal-header">
              <span className="info-modal-title">How we rank recipes</span>
              <button className="info-close" onClick={() => setShowInfo(false)}>×</button>
            </div>

            <div className="info-section">
              <div className="info-section-title">Best Match</div>
              <div className="info-row">
                <div className="info-row-label">Recipe coverage<span>% of recipe's ingredients you have</span></div>
                <div className="info-row-pct">60%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Ingredient use<span>% of your ingredients the recipe uses</span></div>
                <div className="info-row-pct">25%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Overlap<span>Jaccard similarity between both sets</span></div>
                <div className="info-row-pct">15%</div>
              </div>
            </div>

            <div className="info-section">
              <div className="info-section-title">Healthiest</div>
              <div className="info-row">
                <div className="info-row-label">Protein<span>Target: 25g per serving</span></div>
                <div className="info-row-pct">45%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Sugar<span>Penalty above 30g</span></div>
                <div className="info-row-pct">25%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Calories<span>Penalty above 800 kcal</span></div>
                <div className="info-row-pct">30%</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Results
