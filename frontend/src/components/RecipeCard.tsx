import { useState } from 'react'
import type { Recipe } from '../types'

const TAG_CLASSES: Record<string, string> = {
  Healthy: 'tag-healthy',
  Balanced: 'tag-balanced',
  Indulgent: 'tag-indulgent',
}

function getEmoji(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('chicken')) return '🍗'
  if (n.includes('egg') || n.includes('omelette') || n.includes('omelet')) return '🍳'
  if (n.includes('pasta') || n.includes('spaghetti') || n.includes('linguine') || n.includes('fettuccine')) return '🍝'
  if (n.includes('soup') || n.includes('stew') || n.includes('chowder') || n.includes('bisque')) return '🍲'
  if (n.includes('salad')) return '🥗'
  if (n.includes('smoothie') || n.includes('shake')) return '🥤'
  if (n.includes('pizza')) return '🍕'
  if (n.includes('burger') || n.includes('sandwich')) return '🍔'
  if (n.includes('taco') || n.includes('burrito') || n.includes('quesadilla')) return '🌮'
  if (n.includes('fish') || n.includes('salmon') || n.includes('tuna') || n.includes('shrimp')) return '🐟'
  if (n.includes('beef') || n.includes('steak')) return '🥩'
  if (n.includes('pork') || n.includes('bacon')) return '🥓'
  if (n.includes('rice')) return '🍚'
  if (n.includes('bread') || n.includes('toast')) return '🍞'
  if (n.includes('cake') || n.includes('cookie') || n.includes('brownie') || n.includes('dessert')) return '🍰'
  if (n.includes('apple') || n.includes('fruit')) return '🍎'
  if (n.includes('vegetable') || n.includes('veggie') || n.includes('stir-fry')) return '🥦'
  if (n.includes('curry')) return '🍛'
  if (n.includes('mushroom')) return '🍄'
  return '🍽️'
}

function getGradient(tags: string[]): string {
  const tag = tags[0]
  if (tag === 'Healthy') return 'linear-gradient(135deg, #EBF2E5 0%, #D4E3C8 100%)'
  if (tag === 'Balanced') return 'linear-gradient(135deg, #FAF0C8 0%, #F5E08A 100%)'
  if (tag === 'Indulgent') return 'linear-gradient(135deg, #FAF0EB 0%, #F5D9CC 100%)'
  return 'linear-gradient(135deg, #EBF2E5 0%, #D4E3C8 100%)'
}

function getScoreClass(score: number): string {
  if (score >= 70) return 'score-high'
  if (score >= 40) return 'score-mid'
  return 'score-low'
}

interface RecipeCardProps {
  recipe: Recipe
  rank: number
  sortMode: string
  isFavourited?: boolean
  onToggleFavourite?: (recipe: Recipe) => void
}

function RecipeCard({ recipe, rank, sortMode, isFavourited, onToggleFavourite }: RecipeCardProps) {
  const [popping, setPopping] = useState(false)

  const handleHeartClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!onToggleFavourite) return
    setPopping(true)
    onToggleFavourite(recipe)
  }

  const {
    name,
    match_score,
    health_score,
    calories,
    protein,
    fat,
    carbs,
    cook_time,
    matched_count,
    total_ingredients,
    tags,
    url,
  } = recipe

  const primaryScore = sortMode === 'health' ? health_score : match_score

  return (
    <div className="recipe-card">
      <div className="recipe-img" style={{ background: getGradient(tags) }}>
        {getEmoji(name)}
        <span className="rank-badge">#{rank}</span>
        <span className={`score-badge ${getScoreClass(primaryScore)}`}>
          {primaryScore}%
        </span>
        {onToggleFavourite && (
          <button
            className={`heart-btn${isFavourited ? ' hearted' : ''}${popping ? ' popping' : ''}`}
            onClick={handleHeartClick}
            onAnimationEnd={() => setPopping(false)}
            aria-label={isFavourited ? 'Remove from favorites' : 'Add to favorites'}
          >
            <svg viewBox="0 0 24 24" width="16" height="16" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        )}
      </div>

      <div className="recipe-body">
        <div className="recipe-tags">
          {tags.map((t) => (
            <span key={t} className={`tag ${TAG_CLASSES[t] ?? 'tag-balanced'}`}>{t}</span>
          ))}
        </div>

        <div className="recipe-name">{name}</div>

        <div className="recipe-meta">
          <span>⏱ {cook_time || 'N/A'}</span>
          <span>{matched_count} of {total_ingredients} ingredients</span>
        </div>

        {sortMode === 'match' ? (
          <>
            <div className="match-row">
              <span className="match-label">Match</span>
              <div className="match-bar-bg">
                <div className="match-bar-fill" style={{ width: `${match_score}%` }} />
              </div>
              <span className="match-val">{match_score}%</span>
            </div>
            <div className="health-row">
              <span className="health-label">Health</span>
              <div className="health-bar-bg">
                <div className="health-bar-fill" style={{ width: `${health_score}%`, background: 'var(--sage)' }} />
              </div>
              <span className="health-val">{health_score}%</span>
            </div>
          </>
        ) : (
          <>
            <div className="health-row">
              <span className="health-label">Health</span>
              <div className="health-bar-bg">
                <div className="health-bar-fill" style={{ width: `${health_score}%`, background: 'var(--sage)' }} />
              </div>
              <span className="health-val">{health_score}%</span>
            </div>
            <div className="match-row">
              <span className="match-label">Match</span>
              <div className="match-bar-bg">
                <div className="match-bar-fill" style={{ width: `${match_score}%` }} />
              </div>
              <span className="match-val">{match_score}%</span>
            </div>
          </>
        )}

        <div className="recipe-stats">
          <div className="stat-item">
            <div className="stat-val">{calories || '–'}</div>
            <div className="stat-key">kcal</div>
          </div>
          <div className="stat-item">
            <div className="stat-val">{protein ? `${Math.round(protein)}g` : '–'}</div>
            <div className="stat-key">protein</div>
          </div>
          <div className="stat-item">
            <div className="stat-val">{fat ? `${Math.round(fat)}g` : '–'}</div>
            <div className="stat-key">fat</div>
          </div>
          <div className="stat-item">
            <div className="stat-val">{carbs ? `${Math.round(carbs)}g` : '–'}</div>
            <div className="stat-key">carbs</div>
          </div>
        </div>

        {url && (
          <a className="view-btn" href={url} target="_blank" rel="noopener noreferrer">View full recipe →</a>
        )}
      </div>
    </div>
  )
}

export default RecipeCard
