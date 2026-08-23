import { apiFetch } from './client'

export interface Tag {
  id: number
  name: string
}

export interface Ingredient {
  id: number
  name: string
}

export function listTags(): Promise<Tag[]> {
  return apiFetch('/api/tags/')
}

export function listIngredients(): Promise<Ingredient[]> {
  return apiFetch('/api/ingredients/')
}
