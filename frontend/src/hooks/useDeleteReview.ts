import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteReview } from '../api/recipes'

export function useDeleteReview(recipeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reviewId: number) => deleteReview(recipeId, reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
    },
  })
}
