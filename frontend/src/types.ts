export interface Upload {
  id: string
  url: string
  ingredient: string | null
  detecting: boolean
}

export interface Recipe {
  id: number
  name: string
  match_score: number
  health_score: number
  calories: number
  protein: number
  fat: number
  carbs: number
  cook_time: string
  servings: number | null
  matched_count: number
  total_ingredients: number
  tags: string[]
  url: string
  img_src: string
}
