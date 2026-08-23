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
    <form onSubmit={handleSubmit}>
      <StarRatingInput value={rating} onChange={setRating} disabled={isPending} />
      <div>
        <label htmlFor="review-comment">Comment</label>
        <textarea
          id="review-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </div>
      <button type="submit" disabled={isPending}>
        {submitLabel}
      </button>
      {onCancel && (
        <button type="button" onClick={onCancel} disabled={isPending}>
          Cancel
        </button>
      )}
      {errorMessage && <p role="alert">{errorMessage}</p>}
    </form>
  )
}
