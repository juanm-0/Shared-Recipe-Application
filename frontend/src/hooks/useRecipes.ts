import { useQuery } from '@tanstack/react-query'
import { listRecipes, type ListRecipesParams } from '../api/recipes'
import { ApiError } from '../api/client'

export function useRecipes(params: ListRecipesParams) {
  return useQuery({
    queryKey: ['recipes', params],
    queryFn: () => listRecipes(params),
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 3,
  })
}
