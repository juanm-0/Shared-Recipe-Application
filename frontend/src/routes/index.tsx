import { useEffect, useState } from 'react'
import { createFileRoute, Link, type SearchSchemaInput } from '@tanstack/react-router'
import { useRecipes } from '../hooks/useRecipes'
import { useTags } from '../hooks/useTags'
import { useIngredients } from '../hooks/useIngredients'
import { getErrorMessage } from '../api/client'
import type { RecipeSort } from '../api/recipes'

const SORT_OPTIONS: { value: RecipeSort; label: string }[] = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'name', label: 'Name (A-Z)' },
  { value: '-name', label: 'Name (Z-A)' },
  { value: '-rating', label: 'Rating (high to low)' },
  { value: 'rating', label: 'Rating (low to high)' },
]

const SORT_VALUES = SORT_OPTIONS.map((option) => option.value)

const PAGE_SIZE = 20

interface RecipeSearch {
  sort: RecipeSort
  tag?: number
  ingredient?: number
  owner?: number
  min_rating?: number
  page: number
}

function isRecipeSort(value: unknown): value is RecipeSort {
  return typeof value === 'string' && (SORT_VALUES as string[]).includes(value)
}

function parseOptionalNumber(value: unknown): number | undefined {
  if (value === undefined || value === null || value === '') return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

export const Route = createFileRoute('/')({
  validateSearch: (search: Record<string, unknown> & SearchSchemaInput): RecipeSearch => ({
    sort: isRecipeSort(search.sort) ? search.sort : '-created_at',
    tag: parseOptionalNumber(search.tag),
    ingredient: parseOptionalNumber(search.ingredient),
    owner: parseOptionalNumber(search.owner),
    min_rating: parseOptionalNumber(search.min_rating),
    page: parseOptionalNumber(search.page) ?? 1,
  }),
  component: HomePage,
})

function HomePage() {
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const recipesQuery = useRecipes(search)
  const tagsQuery = useTags()
  const ingredientsQuery = useIngredients()

  function updateSearch(patch: Partial<RecipeSearch>, resetPage = true) {
    navigate({
      search: (prev) => ({
        ...prev,
        ...patch,
        page: resetPage ? 1 : (patch.page ?? prev.page),
      }),
    })
  }

  // Debounced so typing a rating doesn't fire a request per keystroke.
  // Local state holds the raw text; a timer commits it to the URL (and
  // thus triggers the actual fetch) once the user stops typing.
  const [minRatingInput, setMinRatingInput] = useState(
    search.min_rating !== undefined ? String(search.min_rating) : '',
  )

  useEffect(() => {
    setMinRatingInput(search.min_rating !== undefined ? String(search.min_rating) : '')
  }, [search.min_rating])

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      const parsed = minRatingInput === '' ? undefined : Number(minRatingInput)
      const normalized = parsed !== undefined && Number.isFinite(parsed) ? parsed : undefined
      if (normalized !== search.min_rating) {
        navigate({ search: (prev) => ({ ...prev, min_rating: normalized, page: 1 }) })
      }
    }, 400)
    return () => clearTimeout(timeoutId)
  }, [minRatingInput, search.min_rating, navigate])

  const count = recipesQuery.data?.count ?? 0
  const isFirstPage = search.page <= 1
  const isLastPage = search.page * PAGE_SIZE >= count

  return (
    <div>
      <h1>Recipes</h1>

      <p>
        <Link to="/recipes/new">Create recipe</Link>
      </p>

      <div>
        <label htmlFor="sort">Sort</label>
        <select
          id="sort"
          value={search.sort}
          onChange={(event) => updateSearch({ sort: event.target.value as RecipeSort })}
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <label htmlFor="tag-filter">Tag</label>
        <select
          id="tag-filter"
          value={search.tag ?? ''}
          onChange={(event) =>
            updateSearch({ tag: event.target.value === '' ? undefined : Number(event.target.value) })
          }
        >
          <option value="">All tags</option>
          {tagsQuery.data?.map((tag) => (
            <option key={tag.id} value={tag.id}>
              {tag.name}
            </option>
          ))}
        </select>

        <label htmlFor="ingredient-filter">Ingredient</label>
        <select
          id="ingredient-filter"
          value={search.ingredient ?? ''}
          onChange={(event) =>
            updateSearch({
              ingredient: event.target.value === '' ? undefined : Number(event.target.value),
            })
          }
        >
          <option value="">All ingredients</option>
          {ingredientsQuery.data?.map((ingredient) => (
            <option key={ingredient.id} value={ingredient.id}>
              {ingredient.name}
            </option>
          ))}
        </select>

        <label htmlFor="min-rating">Min rating</label>
        <input
          id="min-rating"
          type="number"
          min={0}
          max={5}
          step={0.5}
          value={minRatingInput}
          onChange={(event) => setMinRatingInput(event.target.value)}
        />
      </div>

      {recipesQuery.isPending && <p>Loading recipes...</p>}
      {recipesQuery.isError && <p role="alert">{getErrorMessage(recipesQuery.error)}</p>}

      {recipesQuery.isSuccess && (
        <>
          <ul>
            {recipesQuery.data.results.map((recipe) => (
              <li key={recipe.id}>
                <Link to="/recipes/$recipeId" params={{ recipeId: String(recipe.id) }} search={search}>
                  {recipe.image ? (
                    <img src={recipe.image} alt={recipe.name} width={120} height={120} />
                  ) : (
                    <div>No image</div>
                  )}
                  <div>{recipe.name}</div>
                  <div>
                    {recipe.average_rating !== null ? recipe.average_rating.toFixed(1) : 'No ratings yet'}
                  </div>
                  <div>
                    {recipe.tags.slice(0, 3).map((tag) => (
                      <span key={tag.id}>{tag.name}</span>
                    ))}
                  </div>
                </Link>
              </li>
            ))}
          </ul>

          <div>
            <button
              type="button"
              disabled={isFirstPage}
              onClick={() => updateSearch({ page: search.page - 1 }, false)}
            >
              Previous
            </button>
            <span>Page {search.page}</span>
            <button
              type="button"
              disabled={isLastPage}
              onClick={() => updateSearch({ page: search.page + 1 }, false)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
