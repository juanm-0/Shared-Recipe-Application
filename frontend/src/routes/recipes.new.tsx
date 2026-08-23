import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { RecipeForm } from '../components/RecipeForm'
import { useCreateRecipe } from '../hooks/useCreateRecipe'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/recipes/new')({
  component: NewRecipePage,
})

function NewRecipePage() {
  const createRecipe = useCreateRecipe()
  const navigate = useNavigate()

  return (
    <div>
      <h1>Create recipe</h1>
      <RecipeForm
        initialValues={{ name: '', steps: [''], ingredients: [{ ingredient_name: '', amount: '', unit: 'g' }], tags: [] }}
        submitLabel="Create recipe"
        isPending={createRecipe.isPending}
        errorMessage={createRecipe.isError ? getErrorMessage(createRecipe.error) : undefined}
        onSubmit={(data, image) => {
          createRecipe.mutate(
            { data, image },
            {
              onSuccess: (recipe) => {
                navigate({ to: '/recipes/$recipeId', params: { recipeId: String(recipe.id) } })
              },
            },
          )
        }}
      />
    </div>
  )
}
