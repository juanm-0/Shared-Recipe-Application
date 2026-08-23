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
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="recipe-name">Name</label>
        <input id="recipe-name" type="text" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>

      <fieldset>
        <legend>Steps</legend>
        {steps.map((step, index) => (
          <div key={index}>
            <label htmlFor={`step-${index}`}>Step {index + 1}</label>
            <input
              id={`step-${index}`}
              type="text"
              value={step}
              onChange={(e) => updateStep(index, e.target.value)}
            />
            <button type="button" onClick={() => setSteps((prev) => prev.filter((_, i) => i !== index))}>
              Remove step
            </button>
          </div>
        ))}
        <button type="button" onClick={() => setSteps((prev) => [...prev, ''])}>
          Add step
        </button>
      </fieldset>

      <fieldset>
        <legend>Ingredients</legend>
        <datalist id="ingredient-suggestions">
          {ingredientsQuery.data?.map((ing) => <option key={ing.id} value={ing.name} />)}
        </datalist>
        {ingredients.map((ingredient, index) => (
          <div key={index}>
            <label htmlFor={`ingredient-name-${index}`}>Ingredient</label>
            <input
              id={`ingredient-name-${index}`}
              type="text"
              list="ingredient-suggestions"
              value={ingredient.ingredient_name}
              onChange={(e) => updateIngredient(index, { ingredient_name: e.target.value })}
            />
            <label htmlFor={`ingredient-amount-${index}`}>Amount</label>
            <input
              id={`ingredient-amount-${index}`}
              type="number"
              step="0.01"
              min="0"
              value={ingredient.amount}
              onChange={(e) => updateIngredient(index, { amount: e.target.value })}
            />
            <label htmlFor={`ingredient-unit-${index}`}>Unit</label>
            <select
              id={`ingredient-unit-${index}`}
              value={ingredient.unit}
              onChange={(e) => updateIngredient(index, { unit: e.target.value as RecipeUnit })}
            >
              {UNIT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setIngredients((prev) => prev.filter((_, i) => i !== index))}
            >
              Remove ingredient
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() =>
            setIngredients((prev) => [...prev, { ingredient_name: '', amount: '', unit: 'g' }])
          }
        >
          Add ingredient
        </button>
      </fieldset>

      <fieldset>
        <legend>Tags (max {MAX_TAGS})</legend>
        <datalist id="tag-suggestions">
          {tagsQuery.data?.map((tag) => <option key={tag.id} value={tag.name} />)}
        </datalist>
        {tags.map((tag, index) => (
          <div key={index}>
            <label htmlFor={`tag-${index}`}>Tag {index + 1}</label>
            <input
              id={`tag-${index}`}
              type="text"
              list="tag-suggestions"
              value={tag}
              onChange={(e) => updateTag(index, e.target.value)}
            />
            <button type="button" onClick={() => setTags((prev) => prev.filter((_, i) => i !== index))}>
              Remove tag
            </button>
          </div>
        ))}
        {tags.length < MAX_TAGS && (
          <button type="button" onClick={() => setTags((prev) => [...prev, ''])}>
            Add tag
          </button>
        )}
      </fieldset>

      <div>
        <label htmlFor="recipe-image">Image</label>
        <input
          id="recipe-image"
          type="file"
          accept="image/*"
          onChange={(e) => setImage(e.target.files?.[0] ?? null)}
        />
      </div>

      <button type="submit" disabled={isPending}>
        {submitLabel}
      </button>
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </form>
  )
}
