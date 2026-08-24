import { useState } from 'react'
import type { ReactNode } from 'react'
import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useRecipe } from '../hooks/useRecipe'
import { useDeleteRecipe } from '../hooks/useDeleteRecipe'
import { useMe } from '../hooks/useMe'
import { useCreateReview } from '../hooks/useCreateReview'
import { useUpdateReview } from '../hooks/useUpdateReview'
import { useDeleteReview } from '../hooks/useDeleteReview'
import { useCopyRecipe } from '../hooks/useCopyRecipe'
import { useImportRecipeIntoShoppingList } from '../hooks/useImportRecipeIntoShoppingList'
import { ApiError, getErrorMessage } from '../api/client'
import { ReviewForm } from '../components/ReviewForm'
import type { RecipeDetail, ReviewRead } from '../api/recipes'

export const Route = createFileRoute('/recipes/$recipeId')({
  validateSearch: (search: Record<string, unknown>) => search,
  component: RecipeDetailPage,
})

function RecipeDetailPage() {
  const { recipeId } = Route.useParams()
  const numericRecipeId = Number(recipeId)

  const backLink = (
    <p className="mb-4">
      <Link to="/" search={(prev) => prev} className="text-sm text-gray-600 hover:text-blue-600">
        Back to recipes
      </Link>
    </p>
  )

  if (Number.isNaN(numericRecipeId)) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        {backLink}
        <p role="alert" className="text-sm text-red-600">
          Recipe not found.
        </p>
      </div>
    )
  }

  return <RecipeDetailView recipeId={numericRecipeId} backLink={backLink} />
}

function RecipeDetailView({ recipeId, backLink }: { recipeId: number; backLink: ReactNode }) {
  const recipeQuery = useRecipe(recipeId)
  const deleteRecipe = useDeleteRecipe()
  const navigate = useNavigate()

  if (recipeQuery.isPending) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        {backLink}
        <p className="text-sm text-gray-500">Loading recipe...</p>
      </div>
    )
  }

  if (recipeQuery.isError) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        {backLink}
        <p role="alert" className="text-sm text-red-600">
          {getErrorMessage(recipeQuery.error)}
        </p>
      </div>
    )
  }

  const recipe = recipeQuery.data

  function handleDelete() {
    if (!window.confirm(`Delete "${recipe.name}"? This cannot be undone.`)) {
      return
    }
    deleteRecipe.mutate(recipeId, {
      onSuccess: () => {
        navigate({ to: '/' })
      },
    })
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      {backLink}

      {recipe.image ? (
        <img
          src={recipe.image}
          alt={recipe.name}
          className="aspect-square w-full max-w-md rounded-lg object-cover"
        />
      ) : (
        <div className="flex aspect-square w-full max-w-md items-center justify-center rounded-lg bg-gray-100 text-sm text-gray-400">
          No image
        </div>
      )}

      <h1 className="mt-4 text-3xl font-semibold text-gray-900">{recipe.name}</h1>
      <p className="mt-1 text-sm text-gray-600">By {recipe.owner}</p>

      {(recipe.original_recipe !== null || recipe.original_owner !== null) && (
        <p className="mt-2 text-sm italic text-gray-500">
          {recipe.original_recipe !== null ? (
            <>
              This is a copy of{' '}
              <Link
                to="/recipes/$recipeId"
                params={{ recipeId: String(recipe.original_recipe) }}
                className="not-italic text-blue-600 hover:underline"
              >
                the original recipe
              </Link>
              , originally by{' '}
              {recipe.original_owner !== null ? recipe.original_owner : 'a deleted user'}.
            </>
          ) : (
            <>
              This is a copy of a recipe originally by {recipe.original_owner}. The original
              recipe has since been deleted.
            </>
          )}
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {recipe.can_edit && (
          <>
            <Link
              to="/recipes/$recipeId/edit"
              params={{ recipeId: String(recipe.id) }}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Edit
            </Link>
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleteRecipe.isPending}
              className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Delete
            </button>
          </>
        )}
        <CopyButton recipe={recipe} />
        <AddToShoppingListButton recipeId={recipe.id} />
      </div>
      {recipe.can_edit && deleteRecipe.isError && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {getErrorMessage(deleteRecipe.error)}
        </p>
      )}

      <h2 className="mt-8 text-lg font-semibold text-gray-900">Steps</h2>
      <ol className="mt-2 list-decimal space-y-2 pl-5 text-gray-700">
        {recipe.steps.map((step, index) => (
          <li key={index}>{step}</li>
        ))}
      </ol>

      <h2 className="mt-8 text-lg font-semibold text-gray-900">Ingredients</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-700">
        {recipe.ingredients.map((ingredient) => (
          <li key={ingredient.order}>
            {ingredient.amount} {ingredient.unit} {ingredient.ingredient_name}
          </li>
        ))}
      </ul>

      <h2 className="mt-8 text-lg font-semibold text-gray-900">Tags</h2>
      <ul className="mt-2 flex flex-wrap gap-2">
        {recipe.tags.map((tag) => (
          <li key={tag.id} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {tag.name}
          </li>
        ))}
      </ul>

      <ReviewsSection recipe={recipe} recipeId={recipeId} />
    </div>
  )
}

function ReviewsSection({ recipe, recipeId }: { recipe: RecipeDetail; recipeId: number }) {
  const me = useMe()
  const createReview = useCreateReview(recipeId)
  const deleteReview = useDeleteReview(recipeId)
  const [isEditingReview, setIsEditingReview] = useState(false)

  const myReview = me.data ? recipe.reviews.find((r) => r.username === me.data.username) : undefined
  const otherReviews = recipe.reviews.filter((r) => r !== myReview)

  return (
    <div>
      <h2 className="mt-8 text-lg font-semibold text-gray-900">Reviews</h2>

      {myReview && !isEditingReview && (
        <div className="mt-2 rounded-md border border-gray-200 bg-gray-50 p-4">
          <p className="text-sm font-medium text-gray-900">Your review</p>
          <p className="mt-1 text-sm text-amber-500">★ {myReview.rating}/5</p>
          {myReview.comment && <p className="mt-1 text-sm text-gray-700">{myReview.comment}</p>}
          <div className="mt-2 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsEditingReview(true)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => {
                if (window.confirm('Delete your review?')) {
                  deleteReview.mutate(myReview.id)
                }
              }}
              disabled={deleteReview.isPending}
              className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Delete
            </button>
          </div>
          {deleteReview.isError &&
            !(deleteReview.error instanceof ApiError && deleteReview.error.status === 404) && (
              <p role="alert" className="mt-2 text-sm text-red-600">
                {getErrorMessage(deleteReview.error)}
              </p>
            )}
        </div>
      )}

      {myReview && isEditingReview && (
        <EditReviewForm
          recipeId={recipeId}
          review={myReview}
          onDone={() => setIsEditingReview(false)}
        />
      )}

      {!myReview && me.isSuccess && <NewReviewForm createReview={createReview} />}

      {recipe.reviews.length === 0 && <p className="mt-2 text-sm text-gray-500">No reviews yet</p>}

      {otherReviews.length > 0 && (
        <ul className="mt-4 space-y-4">
          {otherReviews.map((review) => (
            <li key={review.id} className="border-t border-gray-200 pt-4">
              <p className="text-sm font-medium text-gray-900">{review.username}</p>
              <p className="mt-1 text-sm text-amber-500">★ {review.rating}/5</p>
              {review.comment && <p className="mt-1 text-sm text-gray-700">{review.comment}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function NewReviewForm({
  createReview,
}: {
  createReview: ReturnType<typeof useCreateReview>
}) {
  const isDuplicateError =
    createReview.isError && createReview.error instanceof ApiError && createReview.error.code === 'duplicate_review'

  return (
    <ReviewForm
      initialValues={{ rating: 5, comment: '' }}
      submitLabel="Submit review"
      isPending={createReview.isPending}
      errorMessage={createReview.isError && !isDuplicateError ? getErrorMessage(createReview.error) : undefined}
      onSubmit={(data) => createReview.mutate(data)}
    />
  )
}

function EditReviewForm({
  recipeId,
  review,
  onDone,
}: {
  recipeId: number
  review: ReviewRead
  onDone: () => void
}) {
  const updateReview = useUpdateReview(recipeId, review.id)

  return (
    <ReviewForm
      initialValues={{ rating: review.rating, comment: review.comment }}
      submitLabel="Save review"
      isPending={updateReview.isPending}
      errorMessage={
        updateReview.isError && !(updateReview.error instanceof ApiError && updateReview.error.status === 404)
          ? getErrorMessage(updateReview.error)
          : undefined
      }
      onCancel={onDone}
      onSubmit={(data) => {
        updateReview.mutate(data, { onSuccess: onDone })
      }}
    />
  )
}

function CopyButton({ recipe }: { recipe: RecipeDetail }) {
  const me = useMe()
  const copyRecipe = useCopyRecipe()
  const navigate = useNavigate()

  if (!me.data || recipe.owner === me.data.username) {
    return null
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => {
          copyRecipe.mutate(recipe.id, {
            onSuccess: (newRecipe) => {
              navigate({ to: '/recipes/$recipeId', params: { recipeId: String(newRecipe.id) } })
            },
          })
        }}
        disabled={copyRecipe.isPending}
        className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Copy recipe
      </button>
      {copyRecipe.isError && (
        <p role="alert" className="absolute left-0 top-full mt-1 w-max max-w-xs text-sm text-red-600">
          {getErrorMessage(copyRecipe.error)}
        </p>
      )}
    </div>
  )
}

function AddToShoppingListButton({ recipeId }: { recipeId: number }) {
  const me = useMe()
  const importRecipe = useImportRecipeIntoShoppingList()

  if (!me.data) {
    return null
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => importRecipe.mutate(recipeId)}
        disabled={importRecipe.isPending}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Add to shopping list
      </button>
      {importRecipe.isSuccess && (
        <span className="absolute left-0 top-full mt-1 w-max text-sm text-green-600">
          Added to shopping list.
        </span>
      )}
      {importRecipe.isError && (
        <p role="alert" className="absolute left-0 top-full mt-1 w-max max-w-xs text-sm text-red-600">
          {getErrorMessage(importRecipe.error)}
        </p>
      )}
    </div>
  )
}
