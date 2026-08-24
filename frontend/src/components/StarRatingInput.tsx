export interface StarRatingInputProps {
  value: number
  onChange: (value: number) => void
  disabled?: boolean
}

const STAR_VALUES = [1, 2, 3, 4, 5]

export function StarRatingInput({ value, onChange, disabled }: StarRatingInputProps) {
  return (
    <div role="radiogroup" aria-label="Rating" className="flex gap-1">
      {STAR_VALUES.map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star === 1 ? '' : 's'}`}
          disabled={disabled}
          onClick={() => onChange(star)}
          className={`text-2xl leading-none disabled:cursor-not-allowed disabled:opacity-50 ${
            star <= value ? 'text-amber-400' : 'text-gray-300'
          }`}
        >
          {star <= value ? '★' : '☆'}
        </button>
      ))}
    </div>
  )
}
