import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateReview, type ReviewWriteData } from '../api/recipes'

export function useUpdateReview(recipeId: number, reviewId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReviewWriteData) => updateReview(recipeId, reviewId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
    },
  })
}
