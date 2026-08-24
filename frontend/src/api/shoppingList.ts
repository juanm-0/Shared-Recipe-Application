import { apiFetch } from './client'
import type { RecipeUnit } from './recipes'

export interface ShoppingListItem {
  id: number
  ingredient_name: string
  amount: string
  unit: RecipeUnit
  is_checked: boolean
  source_recipe: number | null
}

export interface ShoppingList {
  id: number
  items: ShoppingListItem[]
}

export interface ShoppingListItemCreateData {
  ingredient_name: string
  amount: string
  unit: RecipeUnit
}

export function getShoppingList(): Promise<ShoppingList> {
  return apiFetch('/api/shopping-list/')
}

export function createShoppingListItem(data: ShoppingListItemCreateData): Promise<ShoppingListItem> {
  return apiFetch('/api/shopping-list/items/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateShoppingListItem(itemId: number, amount: string): Promise<ShoppingListItem> {
  return apiFetch(`/api/shopping-list/items/${itemId}/`, {
    method: 'PATCH',
    body: JSON.stringify({ amount }),
  })
}

export function deleteShoppingListItem(itemId: number): Promise<void> {
  return apiFetch(`/api/shopping-list/items/${itemId}/`, { method: 'DELETE' })
}

export function importRecipeIntoShoppingList(recipeId: number): Promise<ShoppingList> {
  return apiFetch('/api/shopping-list/import/', {
    method: 'POST',
    body: JSON.stringify({ recipe_id: recipeId }),
  })
}
