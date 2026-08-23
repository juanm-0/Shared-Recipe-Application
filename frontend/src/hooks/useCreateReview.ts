import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createReview, type ReviewWriteData } from '../api/recipes'
import { ApiError } from '../api/client'

export function useCreateReview(recipeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReviewWriteData) => createReview(recipeId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
    },
    onError: (error) => {
      // A duplicate-review rejection (e.g. a second tab that hadn't
      // refreshed) is correct, not a real failure — refetch so the view
      // self-corrects to show the review that already exists, instead of
      // leaving a dead "leave a review" form up with an error under it.
      if (error instanceof ApiError && error.code === 'duplicate_review') {
        queryClient.invalidateQueries({ queryKey: ['recipe', recipeId] })
      }
    },
  })
}
