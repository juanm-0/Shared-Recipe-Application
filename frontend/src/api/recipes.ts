import { apiFetch } from './client'
import type { Tag } from './catalog'

// Matches RecipeListSerializer in backend/recipes/serializers.py exactly.
export interface RecipeListItem {
  id: number
  name: string
  image: string | null
  average_rating: number | null
  review_count: number
  tags: Tag[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// Valid `sort` values accepted by RecipeViewSet._apply_sort.
export type RecipeSort = 'name' | '-name' | 'created_at' | '-created_at' | 'rating' | '-rating'

export interface ListRecipesParams {
  sort?: RecipeSort
  tag?: number
  ingredient?: number
  owner?: number
  min_rating?: number
  page?: number
}

export interface RecipeIngredientRead {
  ingredient_name: string
  amount: string
  unit: string
  order: number
}

export interface ReviewRead {
  id: number
  username: string
  rating: number
  comment: string
  created_at: string
  updated_at: string
}

export interface RecipeDetail {
  id: number
  name: string
  steps: string[]
  image: string | null
  owner: string
  original_recipe: number | null
  original_owner: string | null
  ingredients: RecipeIngredientRead[]
  tags: Tag[]
  reviews: ReviewRead[]
  can_edit: boolean
  version: number
  created_at: string
  updated_at: string
}

export function getRecipe(id: number): Promise<RecipeDetail> {
  return apiFetch(`/api/recipes/${id}/`)
}

export function listRecipes(params: ListRecipesParams = {}): Promise<PaginatedResponse<RecipeListItem>> {
  const query = new URLSearchParams()

  if (params.sort !== undefined) query.set('sort', params.sort)
  if (params.tag !== undefined) query.set('tag', String(params.tag))
  if (params.ingredient !== undefined) query.set('ingredient', String(params.ingredient))
  if (params.owner !== undefined) query.set('owner', String(params.owner))
  if (params.min_rating !== undefined) query.set('min_rating', String(params.min_rating))
  if (params.page !== undefined) query.set('page', String(params.page))

  const queryString = query.toString()
  const path = queryString ? `/api/recipes/?${queryString}` : '/api/recipes/'
  return apiFetch(path)
}
