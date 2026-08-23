import { useQuery } from '@tanstack/react-query'
import { getRecipe } from '../api/recipes'

export function useRecipe(id: number) {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: () => getRecipe(id),
  })
}
