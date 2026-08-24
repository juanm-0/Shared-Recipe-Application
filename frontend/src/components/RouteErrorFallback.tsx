import type { ErrorComponentProps } from '@tanstack/react-router'
import { Link } from '@tanstack/react-router'

export function RouteErrorFallback({ error, reset }: ErrorComponentProps) {
  return (
    <div className="mx-auto max-w-2xl px-6 py-16 text-center">
      <h1 className="text-2xl font-semibold text-gray-900">Something went wrong</h1>
      <p className="mt-2 text-sm text-gray-600">{error.message || 'An unexpected error occurred.'}</p>
      <div className="mt-6 flex items-center justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Try again
        </button>
        <Link
          to="/"
          search={{ sort: '-created_at', page: 1 }}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Go to recipes
        </Link>
      </div>
    </div>
  )
}
