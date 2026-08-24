import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteShoppingListItem } from '../api/shoppingList'

export function useDeleteShoppingListItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (itemId: number) => deleteShoppingListItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingList'] })
    },
  })
}
