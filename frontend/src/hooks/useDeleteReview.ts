import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteReview } from '../api/recipes'
import { ApiError } from '../api/client'

export function useDeleteReview(recipeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (reviewId: number) => deleteReview(recipeId, reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
    },
    onError: (error) => {
      // Handle a case where the review was deleted (another tab or staff)
      // Refetch so the view self-corrects back to the "leave a review" form
      if (error instanceof ApiError && error.status === 404) {
        queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      }
    },
  })
}
