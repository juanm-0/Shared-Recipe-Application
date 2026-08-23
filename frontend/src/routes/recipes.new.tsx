import { useEffect } from 'react'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { RecipeForm } from '../components/RecipeForm'
import { useCreateRecipe } from '../hooks/useCreateRecipe'
import { useMe } from '../hooks/useMe'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/recipes/new')({
  component: NewRecipePage,
})

function NewRecipePage() {
  const createRecipe = useCreateRecipe()
  const me = useMe()
  const navigate = useNavigate()

  useEffect(() => {
    if (!me.isLoading && !me.isSuccess) {
      navigate({ to: '/login' })
    }
  }, [me.isLoading, me.isSuccess, navigate])

  if (me.isLoading || !me.isSuccess) {
    return null
  }

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
              onSuccess: ({ recipe, imageError }) => {
                if (imageError) {
                  return
                }
                navigate({ to: '/recipes/$recipeId', params: { recipeId: String(recipe.id) } })
              },
            },
          )
        }}
      />
      {createRecipe.isSuccess && createRecipe.data.imageError && (
        <p role="alert">
          Recipe saved, but the image could not be uploaded: {createRecipe.data.imageError}.{' '}
          <Link to="/recipes/$recipeId" params={{ recipeId: String(createRecipe.data.recipe.id) }}>
            View recipe
          </Link>
        </p>
      )}
    </div>
  )
}
