import { useState, useEffect, useRef, useMemo } from 'react'
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

  const urlIngredients = useMemo(() => {
    const param = new URLSearchParams(window.location.search).get('i')
    if (!param) return null
    // URLSearchParams.get() already percent-decodes; do NOT call decodeURIComponent again
    // (double-decoding throws URIError if decoded value contains a bare %)
    const parsed = param.split(',').filter(s => s.trim() !== '')
    return parsed.length > 0 ? parsed : null
  }, [])

  const urlDietary = useMemo(() => {
    const param = new URLSearchParams(window.location.search).get('d')
    if (!param) return []
    return param.split(',').filter(s => s.trim() !== '')
  }, [])

  const raw = location.state?.ingredients
  const ingredients: string[] | null = Array.isArray(raw) ? raw : urlIngredients

  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(ingredients !== null)
  const [error, setError] = useState<string | null>(null)
  const [sortMode, setSortMode] = useState<SortMode>('match')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Recipe[] | null>(null)
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [showInfo, setShowInfo] = useState(false)
  const infoButtonRef = useRef<HTMLButtonElement>(null)
  const [visibleCount, setVisibleCount] = useState(RECIPES_PER_PAGE)
  const [dietaryFilters, setDietaryFilters] = useState<string[]>(urlDietary)
  const handleSortChange = (mode: SortMode) => { setSortMode(mode); setVisibleCount(RECIPES_PER_PAGE) }
  const handleDietaryChange = (filters: string[]) => { setDietaryFilters(filters); setVisibleCount(RECIPES_PER_PAGE) }
  const { toggleFavourite, isFavourited } = useFavourites()
  const [copied, setCopied] = useState(false)
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!showInfo) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setShowInfo(false); infoButtonRef.current?.focus() }
      else if (e.key === 'Tab') e.preventDefault()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [showInfo])

  useEffect(() => {
    if (!ingredients) return
    let desired = '?i=' + ingredients.map(encodeURIComponent).join(',')
    if (dietaryFilters.length > 0) desired += '&d=' + dietaryFilters.map(encodeURIComponent).join(',')
    if (window.location.search !== desired) {
      window.history.replaceState(null, '', desired)
    }
  }, [ingredients, dietaryFilters])

  useEffect(() => {
    return () => { if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current) }
  }, [])

  useEffect(() => {
    if (!ingredients) return

    const controller = new AbortController()

    const fetchRecipes = async () => {
      setLoading(true)
      setError(null)
      setVisibleCount(RECIPES_PER_PAGE)
      try {
        const res = await fetch(`${API}/api/recipes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ingredients, dietary: dietaryFilters }),
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
  }, [ingredients, dietaryFilters])

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
          body: JSON.stringify({ q: searchQuery, ingredients: ingredients ?? [], dietary: dietaryFilters }),
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
  }, [searchQuery, ingredients, dietaryFilters])

  const handleShare = async () => {
    if (!ingredients) return
    let url = `${window.location.origin}/results?i=${ingredients.map(encodeURIComponent).join(',')}`
    if (dietaryFilters.length > 0) url += `&d=${dietaryFilters.map(encodeURIComponent).join(',')}`
    try {
      await navigator.clipboard.writeText(url)
    } catch {
      const ta = document.createElement('textarea')
      ta.value = url
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.focus(); ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current)
    setCopied(true)
    copiedTimerRef.current = setTimeout(() => setCopied(false), 1500)
  }

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

      <div className="results-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 className="results-title">Your recipe matches</h1>
          <p className="results-sub">
            Based on <strong>{ingredients.join(', ')}</strong>
          </p>
        </div>
        <button
          onClick={handleShare}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            fontSize: '0.875rem', fontFamily: "'DM Sans', sans-serif",
            color: copied ? 'var(--sage)' : 'var(--muted)',
            cursor: 'pointer',
            border: '1px solid var(--border)', background: 'none',
            borderRadius: '50px', padding: '6px 14px',
            transition: 'color .2s, border-color .2s',
            flexShrink: 0, minHeight: '36px',
          }}
          aria-label={copied ? 'Link copied to clipboard' : 'Copy share link'}
        >
          {copied
            ? <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 8 6.5 11.5 13 5"/></svg>
            : <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a2.5 2.5 0 0 0 3.5.5l2-2a2.5 2.5 0 0 0-3.5-3.5L6.5 4.5"/><path d="M10 8a2.5 2.5 0 0 0-3.5-.5l-2 2a2.5 2.5 0 0 0 3.5 3.5L9.5 11.5"/></svg>
          }
          {copied ? 'Copied!' : 'Share'}
        </button>
      </div>

      <SortBar
        current={sortMode}
        onChange={handleSortChange}
        count={(loading || searching) ? undefined : sorted.length}
        searchQuery={searchQuery}
        onSearchChange={(q) => { setSearchQuery(q); setSearching(q.trim().length > 0) }}
        dietaryFilters={dietaryFilters}
        onDietaryChange={handleDietaryChange}
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
              <p>{dietaryFilters.length > 0 ? 'Try removing a dietary filter or adding more ingredients.' : 'Try adding more ingredients or different ones.'}</p>
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
          <div className="recipe-grid" role="region" aria-label="Recipe results">
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

      <button ref={infoButtonRef} className="info-btn" onClick={() => setShowInfo(true)} aria-label="How scores are calculated">?</button>

      {showInfo && (
        <div className="info-overlay" onClick={() => { setShowInfo(false); infoButtonRef.current?.focus() }}>
          <div className="info-modal" role="dialog" aria-modal="true" aria-labelledby="info-modal-title" onClick={e => e.stopPropagation()}>
            <div className="info-modal-header">
              <span id="info-modal-title" className="info-modal-title">How we rank recipes</span>
              <button className="info-close" autoFocus onClick={() => { setShowInfo(false); infoButtonRef.current?.focus() }} aria-label="Close">×</button>
            </div>
            <div className="info-modal-sub">Ingredients match approximately · Recipes without nutrition data score 0 for health</div>

            <div className="info-section">
              <div className="info-section-title">Best Match</div>
              <div className="info-row">
                <div className="info-row-label">Recipe coverage<span>% of the recipe's ingredients you already have</span></div>
                <div className="info-row-pct">60%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Ingredient use<span>% of your ingredients the recipe actually uses</span></div>
                <div className="info-row-pct">25%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Overlap<span>Shared ÷ total unique ingredients</span></div>
                <div className="info-row-pct">15%</div>
              </div>
            </div>

            <div className="info-section">
              <div className="info-section-title">Healthiest</div>
              <div className="info-row">
                <div className="info-row-label">Protein<span>Full score at ≥25g per serving — higher doesn't help more</span></div>
                <div className="info-row-pct">45%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Sugar<span>Sugar specifically, not total carbs — penalty scales up to 30g</span></div>
                <div className="info-row-pct">25%</div>
              </div>
              <div className="info-row">
                <div className="info-row-label">Calories<span>Full score below 800 kcal — penalty scales up to 800</span></div>
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
