import { createFileRoute, Link } from '@tanstack/react-router'
import { useRecipe } from '../hooks/useRecipe'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/recipes/$recipeId')({
  component: RecipeDetailPage,
})

function RecipeDetailPage() {
  const { recipeId } = Route.useParams()
  const recipeQuery = useRecipe(Number(recipeId))

  if (recipeQuery.isPending) {
    return <p>Loading recipe...</p>
  }

  if (recipeQuery.isError) {
    return <p role="alert">{getErrorMessage(recipeQuery.error)}</p>
  }

  const recipe = recipeQuery.data

  return (
    <div>
      <p>
        <Link to="/">Back to recipes</Link>
      </p>

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

      {recipe.can_edit && <p>(editing coming soon)</p>}

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

      <h2>Reviews</h2>
      {recipe.reviews.length === 0 ? (
        <p>No reviews yet</p>
      ) : (
        <ul>
          {recipe.reviews.map((review) => (
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
