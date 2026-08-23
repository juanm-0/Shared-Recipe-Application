import { useQuery } from '@tanstack/react-query'
import { listIngredients } from '../api/catalog'

export function useIngredients() {
  return useQuery({
    queryKey: ['ingredients'],
    queryFn: listIngredients,
    staleTime: 5 * 60 * 1000,
  })
}
