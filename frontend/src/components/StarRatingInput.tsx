export interface StarRatingInputProps {
  value: number
  onChange: (value: number) => void
  disabled?: boolean
}

const STAR_VALUES = [1, 2, 3, 4, 5]

export function StarRatingInput({ value, onChange, disabled }: StarRatingInputProps) {
  return (
    <div role="radiogroup" aria-label="Rating">
      {STAR_VALUES.map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star === 1 ? '' : 's'}`}
          disabled={disabled}
          onClick={() => onChange(star)}
        >
          {star <= value ? '★' : '☆'}
        </button>
      ))}
    </div>
  )
}
