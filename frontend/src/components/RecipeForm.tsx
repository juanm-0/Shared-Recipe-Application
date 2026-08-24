import { useState } from 'react'
import { useTags } from '../hooks/useTags'
import { useIngredients } from '../hooks/useIngredients'
import { UNIT_OPTIONS, type RecipeIngredientWrite, type RecipeUnit, type RecipeWriteData } from '../api/recipes'

export interface RecipeFormValues {
  name: string
  steps: string[]
  ingredients: RecipeIngredientWrite[]
  tags: string[]
}

export interface RecipeFormProps {
  initialValues: RecipeFormValues
  onSubmit: (data: RecipeWriteData, image: File | null) => void
  isPending: boolean
  submitLabel: string
  errorMessage?: string
}

const MAX_TAGS = 5

export function RecipeForm({ initialValues, onSubmit, isPending, submitLabel, errorMessage }: RecipeFormProps) {
  const [name, setName] = useState(initialValues.name)
  const [steps, setSteps] = useState<string[]>(initialValues.steps)
  const [ingredients, setIngredients] = useState<RecipeIngredientWrite[]>(initialValues.ingredients)
  const [tags, setTags] = useState<string[]>(initialValues.tags)
  const [image, setImage] = useState<File | null>(null)

  const tagsQuery = useTags()
  const ingredientsQuery = useIngredients()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    onSubmit(
      {
        name,
        steps: steps.filter((s) => s.trim() !== ''),
        ingredients: ingredients.filter((ing) => ing.ingredient_name.trim() !== ''),
        tags: tags.filter((t) => t.trim() !== ''),
      },
      image,
    )
  }

  function updateStep(index: number, value: string) {
    setSteps((prev) => prev.map((s, i) => (i === index ? value : s)))
  }

  function updateIngredient(index: number, patch: Partial<RecipeIngredientWrite>) {
    setIngredients((prev) => prev.map((ing, i) => (i === index ? { ...ing, ...patch } : ing)))
  }

  function updateTag(index: number, value: string) {
    setTags((prev) => prev.map((t, i) => (i === index ? value : t)))
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <label htmlFor="recipe-name" className="text-sm font-medium text-gray-700">
          Name
        </label>
        <input
          id="recipe-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-700">Steps</legend>
        <div className="flex flex-col gap-3">
          {steps.map((step, index) => (
            <div key={index} className="flex flex-wrap items-end gap-2">
              <div className="flex flex-1 flex-col gap-1">
                <label htmlFor={`step-${index}`} className="text-sm font-medium text-gray-700">
                  Step {index + 1}
                </label>
                <input
                  id={`step-${index}`}
                  type="text"
                  value={step}
                  onChange={(e) => updateStep(index, e.target.value)}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <button
                type="button"
                onClick={() => setSteps((prev) => prev.filter((_, i) => i !== index))}
                className="rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Remove step
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setSteps((prev) => [...prev, ''])}
          className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Add step
        </button>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-700">Ingredients</legend>
        <datalist id="ingredient-suggestions">
          {ingredientsQuery.data?.map((ing) => <option key={ing.id} value={ing.name} />)}
        </datalist>
        <div className="flex flex-col gap-3">
          {ingredients.map((ingredient, index) => (
            <div key={index} className="flex flex-wrap items-end gap-2">
              <div className="flex flex-1 flex-col gap-1">
                <label htmlFor={`ingredient-name-${index}`} className="text-sm font-medium text-gray-700">
                  Ingredient
                </label>
                <input
                  id={`ingredient-name-${index}`}
                  type="text"
                  list="ingredient-suggestions"
                  value={ingredient.ingredient_name}
                  onChange={(e) => updateIngredient(index, { ingredient_name: e.target.value })}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="flex w-24 flex-col gap-1">
                <label htmlFor={`ingredient-amount-${index}`} className="text-sm font-medium text-gray-700">
                  Amount
                </label>
                <input
                  id={`ingredient-amount-${index}`}
                  type="number"
                  step="0.01"
                  min="0"
                  value={ingredient.amount}
                  onChange={(e) => updateIngredient(index, { amount: e.target.value })}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label htmlFor={`ingredient-unit-${index}`} className="text-sm font-medium text-gray-700">
                  Unit
                </label>
                <select
                  id={`ingredient-unit-${index}`}
                  value={ingredient.unit}
                  onChange={(e) => updateIngredient(index, { unit: e.target.value as RecipeUnit })}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {UNIT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => setIngredients((prev) => prev.filter((_, i) => i !== index))}
                className="rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Remove ingredient
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() =>
            setIngredients((prev) => [...prev, { ingredient_name: '', amount: '', unit: 'g' }])
          }
          className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Add ingredient
        </button>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-gray-700">Tags (max {MAX_TAGS})</legend>
        <datalist id="tag-suggestions">
          {tagsQuery.data?.map((tag) => <option key={tag.id} value={tag.name} />)}
        </datalist>
        <div className="flex flex-col gap-3">
          {tags.map((tag, index) => (
            <div key={index} className="flex flex-wrap items-end gap-2">
              <div className="flex flex-1 flex-col gap-1">
                <label htmlFor={`tag-${index}`} className="text-sm font-medium text-gray-700">
                  Tag {index + 1}
                </label>
                <input
                  id={`tag-${index}`}
                  type="text"
                  list="tag-suggestions"
                  value={tag}
                  onChange={(e) => updateTag(index, e.target.value)}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <button
                type="button"
                onClick={() => setTags((prev) => prev.filter((_, i) => i !== index))}
                className="rounded-md border border-red-300 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Remove tag
              </button>
            </div>
          ))}
        </div>
        {tags.length < MAX_TAGS && (
          <button
            type="button"
            onClick={() => setTags((prev) => [...prev, ''])}
            className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Add tag
          </button>
        )}
      </fieldset>

      <div className="flex flex-col gap-1">
        <label htmlFor="recipe-image" className="text-sm font-medium text-gray-700">
          Image
        </label>
        <input
          id="recipe-image"
          type="file"
          accept="image/*"
          onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          className="text-sm text-gray-700 file:mr-3 file:rounded-md file:border file:border-gray-300 file:bg-white file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-gray-700 hover:file:bg-gray-50"
        />
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitLabel}
      </button>
      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}
    </form>
  )
}
