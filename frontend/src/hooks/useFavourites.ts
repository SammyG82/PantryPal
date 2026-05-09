import { useState, useCallback, useMemo, useEffect } from 'react'
import type { Recipe } from '../types'
import { API } from '../utils'

const KEY = 'pantrypal_favourites'

function load(): Recipe[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]')
  } catch {
    return []
  }
}

export function useFavourites() {
  const [favourites, setFavourites] = useState<Recipe[]>(load)

  // Backfill ingredients for recipes saved before this field existed
  useEffect(() => {
    const stale = favourites.filter((r: any) => r.ingredients == null)
    if (stale.length === 0) return

    Promise.all(
      stale.map(r =>
        fetch(`${API}/api/recipe/${r.id}`)
          .then(res => res.ok ? res.json() as Promise<{ ingredients: string[] }> : null)
          .catch(() => null)
      )
    ).then(results => {
      const updates = new Map<number, string[]>()
      stale.forEach((r, i) => {
        const result = results[i]
        if (result) updates.set(r.id, result.ingredients)
      })
      if (updates.size === 0) return
      setFavourites(prev => {
        const next = prev.map(r =>
          updates.has(r.id) ? { ...r, ingredients: updates.get(r.id)! } : r
        )
        localStorage.setItem(KEY, JSON.stringify(next))
        return next
      })
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
