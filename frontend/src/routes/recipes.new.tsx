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
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Create recipe</h1>
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
        <p role="alert" className="mt-4 text-sm text-red-600">
          Recipe saved, but the image could not be uploaded: {createRecipe.data.imageError}.{' '}
          <Link
            to="/recipes/$recipeId"
            params={{ recipeId: String(createRecipe.data.recipe.id) }}
            className="text-blue-600 hover:underline"
          >
            View recipe
          </Link>
        </p>
      )}
    </div>
  )
}
