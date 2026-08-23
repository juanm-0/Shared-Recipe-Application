import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateRecipe, updateRecipeImage, type RecipeWriteData } from '../api/recipes'
import { getErrorMessage } from '../api/client'
import type { RecipeMutationResult } from './useCreateRecipe'

export function useUpdateRecipe(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      data,
      image,
    }: {
      data: RecipeWriteData & { version: number }
      image: File | null
    }): Promise<RecipeMutationResult> => {
      const updated = await updateRecipe(id, data)
      if (!image) {
        return { recipe: updated }
      }
      try {
        const withImage = await updateRecipeImage(id, updated.version, image)
        return { recipe: withImage }
      } catch (error) {
        return { recipe: updated, imageError: getErrorMessage(error) }
      }
    },
    onSuccess: ({ recipe }) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      queryClient.setQueryData(['recipe', id], recipe)
    },
  })
}
