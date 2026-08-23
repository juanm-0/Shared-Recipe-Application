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

export type RecipeUnit =
  | 'g' | 'kg' | 'ml' | 'l' | 'cup' | 'tbsp' | 'tsp'
  | 'pinch' | 'dash' | 'to_taste' | 'whole' | 'clove'

// Matches RecipeIngredient.UNIT_CHOICES in backend/recipes/models.py exactly.
export const UNIT_OPTIONS: { value: RecipeUnit; label: string }[] = [
  { value: 'g', label: 'Gram' },
  { value: 'kg', label: 'Kilogram' },
  { value: 'ml', label: 'Milliliter' },
  { value: 'l', label: 'Liter' },
  { value: 'cup', label: 'Cup' },
  { value: 'tbsp', label: 'Tablespoon' },
  { value: 'tsp', label: 'Teaspoon' },
  { value: 'pinch', label: 'Pinch' },
  { value: 'dash', label: 'Dash' },
  { value: 'to_taste', label: 'To taste' },
  { value: 'whole', label: 'Whole' },
  { value: 'clove', label: 'Clove' },
]

// Matches RecipeIngredientWriteSerializer in backend/recipes/serializers.py exactly.
export interface RecipeIngredientWrite {
  ingredient_name: string
  amount: string
  unit: RecipeUnit
}

// Matches RecipeWriteSerializer's JSON-only fields
export interface RecipeWriteData {
  name: string
  steps: string[]
  ingredients: RecipeIngredientWrite[]
  tags: string[]
}

export interface ReviewWriteData {
  rating: number
  comment: string
}

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

export function createRecipe(data: RecipeWriteData): Promise<RecipeDetail> {
  return apiFetch('/api/recipes/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateRecipe(
  id: number,
  data: RecipeWriteData & { version: number },
): Promise<RecipeDetail> {
  return apiFetch(`/api/recipes/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

// Separate request from updateRecipe/createRecipe 
// DRF's multipart parser doesn't deserialize the nested `ingredients` list, 
// so image and structured data can't travel in one 
// multipart request without a backend change.
export function updateRecipeImage(id: number, version: number, image: File): Promise<RecipeDetail> {
  const formData = new FormData()
  formData.append('version', String(version))
  formData.append('image', image)
  return apiFetch(`/api/recipes/${id}/`, {
    method: 'PATCH',
    body: formData,
  })
}

export function deleteRecipe(id: number): Promise<void> {
  return apiFetch(`/api/recipes/${id}/`, { method: 'DELETE' })
}

export function createReview(recipeId: number, data: ReviewWriteData): Promise<ReviewRead> {
  return apiFetch(`/api/recipes/${recipeId}/reviews/`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateReview(
  recipeId: number,
  reviewId: number,
  data: ReviewWriteData,
): Promise<ReviewRead> {
  return apiFetch(`/api/recipes/${recipeId}/reviews/${reviewId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteReview(recipeId: number, reviewId: number): Promise<void> {
  return apiFetch(`/api/recipes/${recipeId}/reviews/${reviewId}/`, { method: 'DELETE' })
}

export function copyRecipe(id: number): Promise<RecipeDetail> {
  return apiFetch(`/api/recipes/${id}/copy/`, { method: 'POST' })
}
