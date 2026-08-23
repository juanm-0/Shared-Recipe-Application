import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteRecipe } from '../api/recipes'

export function useDeleteRecipe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteRecipe(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.removeQueries({ queryKey: ['recipe', id] })
    },
  })
}
