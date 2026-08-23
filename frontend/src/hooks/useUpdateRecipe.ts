import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateRecipe, updateRecipeImage, type RecipeWriteData } from '../api/recipes'

export function useUpdateRecipe(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      data,
      image,
    }: {
      data: RecipeWriteData & { version: number }
      image: File | null
    }) => {
      const updated = await updateRecipe(id, data)
      if (image) {
        return updateRecipeImage(id, updated.version, image)
      }
      return updated
    },
    onSuccess: (recipe) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.setQueryData(['recipe', id], recipe)
    },
  })
}
