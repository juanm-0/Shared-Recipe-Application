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
    <p>
      <Link to="/" search={(prev) => prev}>
        Back to recipes
      </Link>
    </p>
  )

  if (Number.isNaN(numericRecipeId)) {
    return (
      <div>
        {backLink}
        <p role="alert">Recipe not found.</p>
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
    <div>
      {backLink}

      <h1>{recipe.name}</h1>

      {recipe.image ? (
        <img src={recipe.image} alt={recipe.name} width={300} height={300} />
      ) : (
        <div>No image</div>
      )}

      <p>By {recipe.owner}</p>

      {(recipe.original_recipe !== null || recipe.original_owner !== null) && (
        <p>
          {recipe.original_recipe !== null ? (
            <>
              This is a copy of{' '}
              <Link to="/recipes/$recipeId" params={{ recipeId: String(recipe.original_recipe) }}>
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

      {recipe.can_edit && (
        <p>
          <Link to="/recipes/$recipeId/edit" params={{ recipeId: String(recipe.id) }}>
            Edit
          </Link>
          <button type="button" onClick={handleDelete} disabled={deleteRecipe.isPending}>
            Delete
          </button>
          {deleteRecipe.isError && <p role="alert">{getErrorMessage(deleteRecipe.error)}</p>}
        </p>
      )}

      <CopyButton recipe={recipe} />

      <h2>Steps</h2>
      <ol>
        {recipe.steps.map((step, index) => (
          <li key={index}>{step}</li>
        ))}
      </ol>

      <h2>Ingredients</h2>
      <ul>
        {recipe.ingredients.map((ingredient) => (
          <li key={ingredient.order}>
            {ingredient.amount} {ingredient.unit} {ingredient.ingredient_name}
          </li>
        ))}
      </ul>

      <h2>Tags</h2>
      <ul>
        {recipe.tags.map((tag) => (
          <li key={tag.id}>{tag.name}</li>
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
      <h2>Reviews</h2>

      {myReview && !isEditingReview && (
        <div>
          <strong>Your review</strong>
          <p>{myReview.rating}/5</p>
          {myReview.comment && <p>{myReview.comment}</p>}
          <button type="button" onClick={() => setIsEditingReview(true)}>
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
          >
            Delete
          </button>
          {deleteReview.isError && <p role="alert">{getErrorMessage(deleteReview.error)}</p>}
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

      {recipe.reviews.length === 0 && <p>No reviews yet</p>}

      {otherReviews.length > 0 && (
        <ul>
          {otherReviews.map((review) => (
            <li key={review.id}>
              <strong>{review.username}</strong> - {review.rating}/5
              {review.comment && <p>{review.comment}</p>}
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
      errorMessage={updateReview.isError ? getErrorMessage(updateReview.error) : undefined}
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
    <p>
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
      >
        Copy recipe
      </button>
      {copyRecipe.isError && <p role="alert">{getErrorMessage(copyRecipe.error)}</p>}
    </p>
  )
}
