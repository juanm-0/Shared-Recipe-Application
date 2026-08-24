import { useState } from 'react'
import { StarRatingInput } from './StarRatingInput'
import type { ReviewWriteData } from '../api/recipes'

export interface ReviewFormProps {
  initialValues: ReviewWriteData
  onSubmit: (data: ReviewWriteData) => void
  onCancel?: () => void
  isPending: boolean
  submitLabel: string
  errorMessage?: string
}

export function ReviewForm({
  initialValues,
  onSubmit,
  onCancel,
  isPending,
  submitLabel,
  errorMessage,
}: ReviewFormProps) {
  const [rating, setRating] = useState(initialValues.rating)
  const [comment, setComment] = useState(initialValues.comment)

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    onSubmit({ rating, comment })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-2 flex flex-col gap-3 rounded-md border border-gray-200 bg-gray-50 p-4"
    >
      <StarRatingInput value={rating} onChange={setRating} disabled={isPending} />
      <div className="flex flex-col gap-1">
        <label htmlFor="review-comment" className="text-sm font-medium text-gray-700">
          Comment
        </label>
        <textarea
          id="review-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>
      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isPending}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>
        )}
      </div>
      {errorMessage && (
        <p role="alert" className="text-sm text-red-600">
          {errorMessage}
        </p>
      )}
    </form>
  )
}
