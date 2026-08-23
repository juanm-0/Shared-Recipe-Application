import { useMutation, useQueryClient } from '@tanstack/react-query'
import { copyRecipe } from '../api/recipes'

export function useCopyRecipe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => copyRecipe(id),
    onSuccess: (recipe) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.setQueryData(['recipe', recipe.id], recipe)
    },
  })
}
