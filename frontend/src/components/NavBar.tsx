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
      <button className="logo" onClick={() => navigate('/')}>
        Pantry<em>Pal</em>
      </button>
      <div className="nav-right">
        {isResults ? (
          <>
            <button className="back-btn" onClick={() => navigate('/', { state: { lastIngredients: ingredients } })}>
              Home
            </button>
            <button className="back-btn" onClick={() => navigate('/favorites', { state: { lastResultsSearch: window.location.search } })}>
              Favorites
            </button>
          </>
        ) : isFavorites ? (
          <>
            <button className="back-btn" onClick={() => navigate('/')}>
              Home
            </button>
            <button
              className="back-btn"
              disabled={!(location.state as { lastResultsSearch?: string } | null)?.lastResultsSearch}
              onClick={() => navigate('/results' + (location.state as { lastResultsSearch?: string }).lastResultsSearch)}
            >
              Results
            </button>
          </>
        ) : (
          <>
            <button className="back-btn" disabled={!lastIngredients?.length && !ingredients.length} onClick={() => navigate('/results', { state: { ingredients: lastIngredients ?? ingredients } })}>
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
