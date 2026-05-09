import { useNavigate, useLocation } from 'react-router-dom'

interface NavBarProps {
  ingredients: string[]
  lastIngredients?: string[]
}

function NavBar({ ingredients = [], lastIngredients }: NavBarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const isResults = location.pathname === '/results'
  const isFavorites = location.pathname === '/favorites'

  return (
    <nav>
      <span
        className="logo"
        onClick={() => navigate('/')}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/') }}
        role="button"
        tabIndex={0}
      >
        Pantry<em>Pal</em>
      </span>
      <div className="nav-right">
        {isResults ? (
          <>
            <span className="ing-summary-pill">
              {ingredients.length} ingredient{ingredients.length !== 1 ? 's' : ''}
            </span>
            <button className="back-btn" onClick={() => navigate('/', { state: { lastIngredients: ingredients } })}>
              ← Back
            </button>
            <button className="back-btn" onClick={() => navigate('/favorites')}>
              Favorites
            </button>
          </>
        ) : isFavorites ? (
          <button className="back-btn" onClick={() => navigate('/')}>
            ← Back
          </button>
        ) : (
          <>
            <button className="back-btn" disabled={!lastIngredients?.length} onClick={() => navigate('/results', { state: { ingredients: lastIngredients } })}>
              Results
            </button>
            <button className="back-btn" onClick={() => navigate('/favorites')}>
              Favorites
            </button>
          </>
        )}
      </div>
    </nav>
  )
}

export default NavBar
