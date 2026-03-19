import { useNavigate, useLocation } from 'react-router-dom'

interface NavBarProps {
  ingredients: string[]
}

function NavBar({ ingredients = [] }: NavBarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const isResults = location.pathname === '/results'

  return (
    <nav>
      <span className="logo" onClick={() => navigate('/')}>
        Pantry<em>Pal</em>
      </span>
      <div className="nav-right">
        {isResults && (
          <>
            <span className="ing-summary-pill">
              {ingredients.length} ingredient{ingredients.length !== 1 ? 's' : ''}
            </span>
            <button className="back-btn" onClick={() => navigate(-1)}>
              ← Back
            </button>
          </>
        )}
      </div>
    </nav>
  )
}

export default NavBar
