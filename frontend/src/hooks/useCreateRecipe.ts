import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createRecipe, updateRecipeImage, type RecipeWriteData, type RecipeDetail } from '../api/recipes'
import { getErrorMessage } from '../api/client'

export interface RecipeMutationResult {
  recipe: RecipeDetail
  imageError?: string
}

export function useCreateRecipe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ data, image }: { data: RecipeWriteData; image: File | null }): Promise<RecipeMutationResult> => {
      const created = await createRecipe(data)
      if (!image) {
        return { recipe: created }
      }
      try {
        const withImage = await updateRecipeImage(created.id, created.version, image)
        return { recipe: withImage }
      } catch (error) {
        return { recipe: created, imageError: getErrorMessage(error) }
      }
    },
    onSuccess: ({ recipe }) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.setQueryData(['recipe', recipe.id], recipe)
    },
  })
}
