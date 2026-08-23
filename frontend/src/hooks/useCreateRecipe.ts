import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createRecipe, updateRecipeImage, type RecipeWriteData } from '../api/recipes'

export function useCreateRecipe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ data, image }: { data: RecipeWriteData; image: File | null }) => {
      const created = await createRecipe(data)
      if (image) {
        return updateRecipeImage(created.id, created.version, image)
      }
      return created
    },
    onSuccess: (recipe) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.setQueryData(['recipe', recipe.id], recipe)
    },
  })
}
