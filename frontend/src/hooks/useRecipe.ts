import { useQuery } from '@tanstack/react-query'
import { getRecipe } from '../api/recipes'
import { ApiError } from '../api/client'

export function useRecipe(id: number) {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: () => getRecipe(id),
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 3,
  })
}
