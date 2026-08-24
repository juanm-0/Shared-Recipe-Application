import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createShoppingListItem, type ShoppingListItemCreateData } from '../api/shoppingList'

export function useAddShoppingListItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ShoppingListItemCreateData) => createShoppingListItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingList'] })
    },
  })
}
