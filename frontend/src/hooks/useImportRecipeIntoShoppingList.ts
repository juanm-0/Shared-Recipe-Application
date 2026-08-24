import { useMutation, useQueryClient } from '@tanstack/react-query'
import { importRecipeIntoShoppingList } from '../api/shoppingList'

export function useImportRecipeIntoShoppingList() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (recipeId: number) => importRecipeIntoShoppingList(recipeId),
    onSuccess: (shoppingList) => {
      queryClient.setQueryData(['shoppingList'], shoppingList)
    },
  })
}
