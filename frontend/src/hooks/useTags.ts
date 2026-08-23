import { useQuery } from '@tanstack/react-query'
import { listTags } from '../api/catalog'

export function useTags() {
  return useQuery({
    queryKey: ['tags'],
    queryFn: listTags,
    staleTime: 5 * 60 * 1000,
  })
}
