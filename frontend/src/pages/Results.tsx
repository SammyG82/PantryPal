import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import SortBar from '../components/SortBar'
import RecipeCard from '../components/RecipeCard'
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

  const sorted = [...recipes].sort((a, b) =>
    sortMode === 'health' ? b.health_score - a.health_score : b.match_score - a.match_score
  )

  return (
    <div>
      <NavBar ingredients={ingredients} />

      <div className="results-header">
        <h1 className="results-title">Your recipe matches</h1>
        <p className="results-sub">
          Based on <strong>{ingredients.join(', ')}</strong>
        </p>
      </div>

      <SortBar current={sortMode} onChange={setSortMode} count={loading ? undefined : sorted.length} />

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

      {!loading && !error && sorted.length === 0 && (
        <div className="empty-state">
          <h3>No matches found</h3>
          <p>Try adding more ingredients or different ones.</p>
          <button
            style={{ marginTop: '1.5rem', padding: '10px 28px', cursor: 'pointer', fontFamily: 'DM Sans, sans-serif', background: 'var(--terra)', color: 'white', border: 'none', borderRadius: '50px', fontSize: '0.9rem' }}
            onClick={() => navigate('/')}
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && sorted.length > 0 && (
        <div className="recipe-grid">
          {sorted.map((recipe, i) => (
            <RecipeCard key={recipe.id} recipe={recipe} rank={i + 1} sortMode={sortMode} />
          ))}
        </div>
      )}
    </div>
  )
}

export default Results
