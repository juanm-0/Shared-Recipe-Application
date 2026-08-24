import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useShoppingList } from '../hooks/useShoppingList'
import { useAddShoppingListItem } from '../hooks/useAddShoppingListItem'
import { useUpdateShoppingListItem } from '../hooks/useUpdateShoppingListItem'
import { useDeleteShoppingListItem } from '../hooks/useDeleteShoppingListItem'
import { useIngredients } from '../hooks/useIngredients'
import { UNIT_OPTIONS, type RecipeUnit } from '../api/recipes'
import type { ShoppingListItem } from '../api/shoppingList'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/shopping-list')({
  component: ShoppingListPage,
})

function ShoppingListPage() {
  const shoppingListQuery = useShoppingList()

  return (
    <div>
      <h1>Shopping list</h1>

      {shoppingListQuery.isPending && <p>Loading shopping list...</p>}
      {shoppingListQuery.isError && <p role="alert">{getErrorMessage(shoppingListQuery.error)}</p>}

      {shoppingListQuery.isSuccess && (
        <>
          {shoppingListQuery.data.items.length === 0 ? (
            <p>No items yet</p>
          ) : (
            <ul>
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

  function handleSave() {
    updateItem.mutate({ itemId: item.id, amount })
  }

  return (
    <li>
      {item.ingredient_name} —{' '}
      <input
        type="number"
        step="0.01"
        min="0"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />{' '}
      {item.unit}
      <button type="button" onClick={handleSave} disabled={updateItem.isPending}>
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
      >
        Delete
      </button>
      {updateItem.isError && <p role="alert">{getErrorMessage(updateItem.error)}</p>}
      {deleteItem.isError && <p role="alert">{getErrorMessage(deleteItem.error)}</p>}
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
    <form onSubmit={handleSubmit}>
      <h2>Add item</h2>
      <datalist id="shopping-list-ingredient-suggestions">
        {ingredientsQuery.data?.map((ingredient) => (
          <option key={ingredient.id} value={ingredient.name} />
        ))}
      </datalist>
      <div>
        <label htmlFor="shopping-item-name">Ingredient</label>
        <input
          id="shopping-item-name"
          type="text"
          list="shopping-list-ingredient-suggestions"
          value={ingredientName}
          onChange={(e) => setIngredientName(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="shopping-item-amount">Amount</label>
        <input
          id="shopping-item-amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="shopping-item-unit">Unit</label>
        <select id="shopping-item-unit" value={unit} onChange={(e) => setUnit(e.target.value as RecipeUnit)}>
          {UNIT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <button type="submit" disabled={addItem.isPending}>
        Add item
      </button>
      {addItem.isError && <p role="alert">{getErrorMessage(addItem.error)}</p>}
    </form>
  )
}
