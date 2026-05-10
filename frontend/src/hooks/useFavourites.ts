import { useState, useCallback, useMemo } from 'react'
import type { Recipe } from '../types'

const KEY = 'pantrypal_favourites'

function load(): Recipe[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    localStorage.removeItem(KEY)
    return []
  }
}

export function useFavourites() {
  const [favourites, setFavourites] = useState<Recipe[]>(load)

  const toggleFavourite = useCallback((recipe: Recipe) => {
    setFavourites(prev => {
      const next = prev.some(r => r.id === recipe.id)
        ? prev.filter(r => r.id !== recipe.id)
        : [...prev, recipe]
      localStorage.setItem(KEY, JSON.stringify(next))
      return next
    })
  }, [])

  const favouriteIds = useMemo(() => new Set(favourites.map(r => r.id)), [favourites])

  const isFavourited = useCallback((id: number) => favouriteIds.has(id), [favouriteIds])

  return { favourites, toggleFavourite, isFavourited }
}
