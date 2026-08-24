import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useShoppingList } from '../hooks/useShoppingList'
import { useAddShoppingListItem } from '../hooks/useAddShoppingListItem'
import { useUpdateShoppingListItem } from '../hooks/useUpdateShoppingListItem'
import { useDeleteShoppingListItem } from '../hooks/useDeleteShoppingListItem'
import { useIngredients } from '../hooks/useIngredients'
import { UNIT_OPTIONS, type RecipeUnit } from '../api/recipes'
import type { ShoppingListItem } from '../api/shoppingList'
import { ApiError, getErrorMessage } from '../api/client'

export const Route = createFileRoute('/shopping-list')({
  component: ShoppingListPage,
})

function ShoppingListPage() {
  const shoppingListQuery = useShoppingList()

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Shopping list</h1>

      {shoppingListQuery.isPending && <p className="text-sm text-gray-500">Loading shopping list...</p>}
      {shoppingListQuery.isError && (
        <p role="alert" className="text-sm text-red-600">
          {getErrorMessage(shoppingListQuery.error)}
        </p>
      )}

      {shoppingListQuery.isSuccess && (
        <>
          {shoppingListQuery.data.items.length === 0 ? (
            <p className="rounded-md border border-gray-200 bg-gray-50 p-8 text-center text-sm text-gray-500">
              Your shopping list is empty.
            </p>
          ) : (
            <ul className="flex flex-col gap-3">
              {shoppingListQuery.data.items.map((item) => (
                <ShoppingListItemRow key={item.id} item={item} />
              ))}
            </ul>
          )}
        </>
      )}

      <AddItemForm />
    </div>
  )
}

function ShoppingListItemRow({ item }: { item: ShoppingListItem }) {
  const [amount, setAmount] = useState(item.amount)
  const updateItem = useUpdateShoppingListItem()
  const deleteItem = useDeleteShoppingListItem()

  useEffect(() => {
    setAmount(item.amount)
  }, [item.amount])

  function handleSave() {
    if (!(Number(amount) > 0)) {
      return
    }
    updateItem.mutate({ itemId: item.id, amount })
  }

  return (
    <li className="rounded-md border border-gray-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex-1 text-sm text-gray-900">{item.ingredient_name}</span>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          aria-label={`Amount of ${item.ingredient_name}`}
          className="w-20 rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-600">{item.unit}</span>
        <button
          type="button"
          onClick={handleSave}
          disabled={updateItem.isPending}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Save
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm(`Remove ${item.ingredient_name} from your shopping list?`)) {
              deleteItem.mutate(item.id)
            }
          }}
          disabled={deleteItem.isPending}
          className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Delete
        </button>
      </div>
      {updateItem.isError && !(updateItem.error instanceof ApiError && updateItem.error.status === 404) && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {getErrorMessage(updateItem.error)}
        </p>
      )}
      {deleteItem.isError && !(deleteItem.error instanceof ApiError && deleteItem.error.status === 404) && (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {getErrorMessage(deleteItem.error)}
        </p>
      )}
    </li>
  )
}

function AddItemForm() {
  const [ingredientName, setIngredientName] = useState('')
  const [amount, setAmount] = useState('')
  const [unit, setUnit] = useState<RecipeUnit>('g')
  const addItem = useAddShoppingListItem()
  const ingredientsQuery = useIngredients()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    addItem.mutate(
      { ingredient_name: ingredientName, amount, unit },
      {
        onSuccess: () => {
          setIngredientName('')
          setAmount('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-gray-900">Add item</h2>
      <datalist id="shopping-list-ingredient-suggestions">
        {ingredientsQuery.data?.map((ingredient) => (
          <option key={ingredient.id} value={ingredient.name} />
        ))}
      </datalist>
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-1 flex-col gap-1">
          <label htmlFor="shopping-item-name" className="text-sm font-medium text-gray-700">
            Ingredient
          </label>
          <input
            id="shopping-item-name"
            type="text"
            list="shopping-list-ingredient-suggestions"
            value={ingredientName}
            onChange={(e) => setIngredientName(e.target.value)}
            required
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="flex w-24 flex-col gap-1">
          <label htmlFor="shopping-item-amount" className="text-sm font-medium text-gray-700">
            Amount
          </label>
          <input
            id="shopping-item-amount"
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="shopping-item-unit" className="text-sm font-medium text-gray-700">
            Unit
          </label>
          <select
            id="shopping-item-unit"
            value={unit}
            onChange={(e) => setUnit(e.target.value as RecipeUnit)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {UNIT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      <button
        type="submit"
        disabled={addItem.isPending}
        className="self-start rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Add item
      </button>
      {addItem.isError && (
        <p role="alert" className="text-sm text-red-600">
          {getErrorMessage(addItem.error)}
        </p>
      )}
    </form>
  )
}
