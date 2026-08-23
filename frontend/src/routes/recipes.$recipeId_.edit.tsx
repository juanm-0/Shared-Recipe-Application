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
      <div>
        <p>
          <Link to="/">Back to recipes</Link>
        </p>
        <p role="alert">Recipe not found.</p>
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
    <p>
      <Link to="/recipes/$recipeId" params={{ recipeId: String(recipeId) }}>
        Back to recipe
      </Link>
    </p>
  )

  if (recipeQuery.isPending) {
    return (
      <div>
        {backLink}
        <p>Loading recipe...</p>
      </div>
    )
  }

  if (recipeQuery.isError) {
    return (
      <div>
        {backLink}
        <p role="alert">{getErrorMessage(recipeQuery.error)}</p>
      </div>
    )
  }

  const recipe = pinnedRecipe

  if (recipe === null) {
    return (
      <div>
        {backLink}
        <p>Loading recipe...</p>
      </div>
    )
  }

  if (!recipe.can_edit) {
    return (
      <div>
        {backLink}
        <p role="alert">You don't have permission to edit this recipe.</p>
      </div>
    )
  }

  const isStaleWrite = updateRecipe.isError && updateRecipe.error instanceof ApiError && updateRecipe.error.code === 'stale_write'

  return (
    <div>
      {backLink}
      <h1>Edit recipe</h1>
      {isStaleWrite && (
        <div role="alert">
          <p>This recipe was changed by someone else since you loaded it. Your edits below were not saved.</p>
          <button
            type="button"
            onClick={() => {
              const current = (updateRecipe.error as ApiError).current as RecipeDetail
              setPinnedRecipe(current)
              setResetKey((k) => k + 1)
              updateRecipe.reset()
            }}
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
        <p role="alert">
          Recipe saved, but the image could not be uploaded: {updateRecipe.data.imageError}.{' '}
          <Link to="/recipes/$recipeId" params={{ recipeId: String(recipeId) }}>
            View recipe
          </Link>
        </p>
      )}
    </div>
  )
}
