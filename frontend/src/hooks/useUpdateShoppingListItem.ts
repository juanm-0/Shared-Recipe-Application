import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateShoppingListItem } from '../api/shoppingList'
import { ApiError } from '../api/client'

export function useUpdateShoppingListItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ itemId, amount }: { itemId: number; amount: string }) =>
      updateShoppingListItem(itemId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingList'] })
    },
    onError: (error) => {
      // The item is gone (deleted in another tab, or a stale row). Refetch so
      // the view self-corrects instead of showing a raw error on a phantom row.
      if (error instanceof ApiError && error.status === 404) {
        queryClient.invalidateQueries({ queryKey: ['shoppingList'] })
      }
    },
  })
}
