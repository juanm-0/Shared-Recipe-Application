import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateReview, type ReviewWriteData } from '../api/recipes'
import { ApiError } from '../api/client'

export function useUpdateReview(recipeId: number, reviewId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReviewWriteData) => updateReview(recipeId, reviewId, data),
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
