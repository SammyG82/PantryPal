import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import RecipeCard from '../components/RecipeCard'
import { useFavourites } from '../hooks/useFavourites'

function Favourites() {
  const navigate = useNavigate()
  const { favourites, toggleFavourite, isFavourited } = useFavourites()
  const [copied, setCopied] = useState(false)
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => { if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current) }
  }, [])

  const handleShare = async () => {
    const url = window.location.href
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

  return (
    <div>
      <NavBar ingredients={[]} />

      {favourites.length === 0 ? (
        <div className="empty-state empty-state--full">
          <div style={{ fontSize: '2.5rem', marginBottom: '1.25rem' }}>🤍</div>
          <h3>No favorites yet</h3>
          <p style={{ marginTop: '0.5rem', maxWidth: '340px', lineHeight: 1.7 }}>
            We hope you find recipes you love. Tap the heart on any recipe to save it here.
          </p>
          <button
            className="btn-terra"
            style={{ marginTop: '1.75rem', padding: '12px 32px', fontSize: '0.95rem' }}
            onClick={() => navigate('/')}
          >
            Find recipes →
          </button>
        </div>
      ) : (
        <>
          <div className="results-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div>
              <h1 className="results-title">Your favorites</h1>
              <p className="results-sub">
                {favourites.length} saved recipe{favourites.length !== 1 ? 's' : ''}
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
          <div className="recipe-grid">
            {favourites.map((recipe, i) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                rank={i + 1}
                sortMode="match"
                isFavourited={isFavourited(recipe.id)}
                onToggleFavourite={toggleFavourite}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default Favourites
