import { useEffect, useState } from 'react'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { RecipeForm } from '../components/RecipeForm'
import { useRecipe } from '../hooks/useRecipe'
import { useUpdateRecipe } from '../hooks/useUpdateRecipe'
import { ApiError, getErrorMessage } from '../api/client'
import type { RecipeDetail, RecipeUnit } from '../api/recipes'

export const Route = createFileRoute('/recipes/$recipeId_/edit')({
  component: EditRecipePage,
})

function EditRecipePage() {
  const { recipeId } = Route.useParams()
  const numericRecipeId = Number(recipeId)

  if (Number.isNaN(numericRecipeId)) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        <p className="mb-4">
          <Link to="/" className="text-sm text-gray-600 hover:text-blue-600">
            Back to recipes
          </Link>
        </p>
        <p role="alert" className="text-sm text-red-600">
          Recipe not found.
        </p>
      </div>
    )
  }

  return <EditRecipeView recipeId={numericRecipeId} />
}

function EditRecipeView({ recipeId }: { recipeId: number }) {
  const recipeQuery = useRecipe(recipeId)
  const updateRecipe = useUpdateRecipe(recipeId)
  const navigate = useNavigate()

  // pinnedRecipe is the version the user is editing against.
  // resetKey forces the internal state to reflect a fresh start on request.
  const [resetKey, setResetKey] = useState(0)
  const [pinnedRecipe, setPinnedRecipe] = useState<RecipeDetail | null>(null)

  useEffect(() => {
    if (recipeQuery.data && pinnedRecipe === null) {
      setPinnedRecipe(recipeQuery.data)
    }
  }, [recipeQuery.data, pinnedRecipe])

  const backLink = (
    <p className="mb-4">
      <Link
        to="/recipes/$recipeId"
        params={{ recipeId: String(recipeId) }}
        className="text-sm text-gray-600 hover:text-blue-600"
      >
        Back to recipe
      </Link>
    </p>
  )

  if (recipeQuery.isPending) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        {backLink}
        <p className="text-sm text-gray-500">Loading recipe...</p>
      </div>
    )
  }

  if (recipeQuery.isError) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        {backLink}
        <p role="alert" className="text-sm text-red-600">
          {getErrorMessage(recipeQuery.error)}
        </p>
      </div>
    )
  }

  const recipe = pinnedRecipe

  if (recipe === null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        {backLink}
        <p className="text-sm text-gray-500">Loading recipe...</p>
      </div>
    )
  }

  if (!recipe.can_edit) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-8">
        {backLink}
        <p role="alert" className="text-sm text-red-600">
          You don't have permission to edit this recipe.
        </p>
      </div>
    )
  }

  const isStaleWrite = updateRecipe.isError && updateRecipe.error instanceof ApiError && updateRecipe.error.code === 'stale_write'

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      {backLink}
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Edit recipe</h1>
      {isStaleWrite && (
        <div role="alert" className="mb-6 rounded-md border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">
            This recipe was changed by someone else since you loaded it. Your edits below were not saved.
          </p>
          <button
            type="button"
            onClick={() => {
              const current = (updateRecipe.error as ApiError).current as RecipeDetail
              setPinnedRecipe(current)
              setResetKey((k) => k + 1)
              updateRecipe.reset()
            }}
            className="mt-2 rounded-md border border-amber-300 bg-white px-3 py-1.5 text-sm font-medium text-amber-800 hover:bg-amber-100"
          >
            Reload latest version
          </button>
        </div>
      )}
      <RecipeForm
        key={resetKey}
        initialValues={{
          name: recipe.name,
          steps: recipe.steps,
          ingredients: recipe.ingredients.map((ing) => ({
            ingredient_name: ing.ingredient_name,
            amount: ing.amount,
            unit: ing.unit as RecipeUnit,
          })),
          tags: recipe.tags.map((tag) => tag.name),
        }}
        submitLabel="Save changes"
        isPending={updateRecipe.isPending}
        errorMessage={
          updateRecipe.isError && !isStaleWrite ? getErrorMessage(updateRecipe.error) : undefined
        }
        onSubmit={(data, image) => {
          updateRecipe.mutate(
            { data: { ...data, version: recipe.version }, image },
            {
              onSuccess: ({ imageError }) => {
                if (imageError) {
                  return
                }
                navigate({ to: '/recipes/$recipeId', params: { recipeId: String(recipeId) } })
              },
            },
          )
        }}
      />
      {updateRecipe.isSuccess && updateRecipe.data.imageError && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          Recipe saved, but the image could not be uploaded: {updateRecipe.data.imageError}.{' '}
          <Link
            to="/recipes/$recipeId"
            params={{ recipeId: String(recipeId) }}
            className="text-blue-600 hover:underline"
          >
            View recipe
          </Link>
        </p>
      )}
    </div>
  )
}
