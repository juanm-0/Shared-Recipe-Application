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

const PAGE_SIZE = 18

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
  const recipesQuery = useRecipes({ ...search, page_size: PAGE_SIZE })
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
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Recipes</h1>
        <Link
          to="/recipes/new"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Create recipe
        </Link>
      </div>

      <div className="mb-6 flex flex-wrap items-end gap-4 rounded-md border border-gray-200 bg-gray-50 p-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="sort" className="text-sm font-medium text-gray-700">
            Sort
          </label>
          <select
            id="sort"
            value={search.sort}
            onChange={(event) => updateSearch({ sort: event.target.value as RecipeSort })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="tag-filter" className="text-sm font-medium text-gray-700">
            Tag
          </label>
          <select
            id="tag-filter"
            value={search.tag ?? ''}
            onChange={(event) =>
              updateSearch({ tag: event.target.value === '' ? undefined : Number(event.target.value) })
            }
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All tags</option>
            {tagsQuery.data?.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="ingredient-filter" className="text-sm font-medium text-gray-700">
            Ingredient
          </label>
          <select
            id="ingredient-filter"
            value={search.ingredient ?? ''}
            onChange={(event) =>
              updateSearch({
                ingredient: event.target.value === '' ? undefined : Number(event.target.value),
              })
            }
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All ingredients</option>
            {ingredientsQuery.data?.map((ingredient) => (
              <option key={ingredient.id} value={ingredient.id}>
                {ingredient.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="min-rating" className="text-sm font-medium text-gray-700">
            Min rating
          </label>
          <input
            id="min-rating"
            type="number"
            min={0}
            max={5}
            step={0.5}
            value={minRatingInput}
            onChange={(event) => setMinRatingInput(event.target.value)}
            className="w-24 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {recipesQuery.isPending && <p className="text-sm text-gray-500">Loading recipes...</p>}
      {recipesQuery.isError && (
        <p role="alert" className="text-sm text-red-600">
          {getErrorMessage(recipesQuery.error)}
        </p>
      )}

      {recipesQuery.isSuccess && (
        <>
          <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {recipesQuery.data.results.map((recipe) => (
              <li
                key={recipe.id}
                className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition hover:shadow-md"
              >
                <Link to="/recipes/$recipeId" params={{ recipeId: String(recipe.id) }} search={search} className="block">
                  {recipe.image ? (
                    <img src={recipe.image} alt={recipe.name} className="aspect-square w-full object-cover" />
                  ) : (
                    <div className="flex aspect-square w-full items-center justify-center bg-gray-100 text-sm text-gray-400">
                      No image
                    </div>
                  )}
                  <div className="p-4">
                    <h2 className="font-medium text-gray-900">{recipe.name}</h2>
                    <p className="mt-1 text-sm text-gray-600">
                      {recipe.average_rating !== null ? recipe.average_rating.toFixed(1) : 'No ratings yet'}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {recipe.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag.id}
                          className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {tag.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              type="button"
              disabled={isFirstPage}
              onClick={() => updateSearch({ page: search.page - 1 }, false)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">Page {search.page}</span>
            <button
              type="button"
              disabled={isLastPage}
              onClick={() => updateSearch({ page: search.page + 1 }, false)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
