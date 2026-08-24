import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateShoppingListItem } from '../api/shoppingList'

export function useUpdateShoppingListItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ itemId, amount }: { itemId: number; amount: string }) =>
      updateShoppingListItem(itemId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingList'] })
    },
  })
}
