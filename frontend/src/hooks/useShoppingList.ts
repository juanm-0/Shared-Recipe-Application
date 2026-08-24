import { useQuery } from '@tanstack/react-query'
import { getShoppingList } from '../api/shoppingList'

export function useShoppingList() {
  return useQuery({
    queryKey: ['shoppingList'],
    queryFn: getShoppingList,
  })
}
