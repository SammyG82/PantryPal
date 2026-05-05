import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import RecipeCard from '../components/RecipeCard'
import { useFavourites } from '../hooks/useFavourites'

function Favourites() {
  const navigate = useNavigate()
  const { favourites, toggleFavourite, isFavourited } = useFavourites()

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
          <div className="results-header">
            <h1 className="results-title">Your favorites</h1>
            <p className="results-sub">
              {favourites.length} saved recipe{favourites.length !== 1 ? 's' : ''}
            </p>
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
