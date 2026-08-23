import { useQuery } from '@tanstack/react-query'
import { listRecipes, type ListRecipesParams } from '../api/recipes'

export function useRecipes(params: ListRecipesParams) {
  return useQuery({
    queryKey: ['recipes', params],
    queryFn: () => listRecipes(params),
  })
}
