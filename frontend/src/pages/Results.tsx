import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import SortBar from '../components/SortBar'
import RecipeCard from '../components/RecipeCard'
import { useFavourites } from '../hooks/useFavourites'
import type { Recipe } from '../types'

const API = import.meta.env.VITE_API_URL ?? ''

function Results() {
  const location = useLocation()
  const navigate = useNavigate()

  const ingredients: string[] | null = location.state?.ingredients ?? null

  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortMode, setSortMode] = useState('match')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Recipe[] | null>(null)
  const [searching, setSearching] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [visibleCount, setVisibleCount] = useState(9)
  const handleSortChange = (mode: string) => { setSortMode(mode); setVisibleCount(9) }
  const { toggleFavourite, isFavourited } = useFavourites()

  useEffect(() => {
    if (!ingredients) return

    const fetchRecipes = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API}/api/recipes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ingredients }),
        })
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        const data = await res.json() as Recipe[]
        setRecipes(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchRecipes()
  }, [ingredients])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      setSearching(false)
      return
    }
    let cancelled = false
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await fetch(`${API}/api/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q: searchQuery, ingredients: ingredients ?? [] }),
        })
        if (cancelled) return
        if (res.ok) {
          setSearchResults(await res.json() as Recipe[])
        } else {
          setSearchResults(null)
        }
      } catch {
        if (!cancelled) setSearchResults(null)
      } finally {
        if (!cancelled) setSearching(false)
      }
    }, 300)
    return () => { clearTimeout(timer); cancelled = true }
  }, [searchQuery, ingredients])

  if (!ingredients) return (
    <div>
      <NavBar ingredients={[]} />
      <div className="empty-state" style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1.25rem' }}>🥗</div>
        <h3>No ingredients yet</h3>
        <p style={{ marginTop: '0.5rem' }}>Head back and upload a photo or type in what you have — we'll find recipes you can make right now.</p>
        <button
          style={{ marginTop: '1.75rem', padding: '12px 32px', cursor: 'pointer', fontFamily: 'DM Sans, sans-serif', background: 'var(--terra)', color: 'white', border: 'none', borderRadius: '50px', fontSize: '0.95rem', fontWeight: 500 }}
          onClick={() => navigate('/')}
        >
          Add ingredients →
        </button>
      </div>
    </div>
  )

  const isSearching = searchQuery.trim().length > 0
  const searchReady = isSearching && searchResults !== null
  const displayRecipes = searchReady
    ? searchResults!.filter((r) => r.match_score > 0)
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
        onSearchChange={setSearchQuery}
      />

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

      {!loading && !error && !searching && visible.length === 0 && (!isSearching || searchReady) && (
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
