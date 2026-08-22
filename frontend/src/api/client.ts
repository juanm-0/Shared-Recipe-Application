export class ApiError extends Error {
  status: number
  code: string
  detail: string
  errors?: unknown
  current?: unknown

  constructor(status: number, body: { detail: string; code: string; errors?: unknown; current?: unknown }) {
    super(body.detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = body.detail
    this.code = body.code
    this.errors = body.errors
    this.current = body.current
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)'),
  )
  return match ? decodeURIComponent(match[1]) : null
}

const CSRF_SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE'])

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)

  if (options.body !== undefined && options.body !== null) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  if (!CSRF_SAFE_METHODS.has(method)) {
    const csrfToken = getCookie('csrftoken')
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken)
    }
  }

  const response = await fetch(path, {
    ...options,
    method,
    headers,
    credentials: 'include',
  })

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  const data = text ? JSON.parse(text) : undefined

  if (!response.ok) {
    throw new ApiError(response.status, data)
  }

  return data as T
}

export async function ensureCsrfCookie(): Promise<void> {
  await apiFetch('/api/auth/csrf/')
}

// Extracts the most specific human-readable message from an ApiError.
// For validation errors, `detail` is just the generic "Validation failed."
// wrapper — the useful message(s) live in `errors`, keyed by field name,
// each an array of strings (DRF's standard validation error shape).
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'validation_error' && error.errors && typeof error.errors === 'object') {
      const messages = Object.values(error.errors as Record<string, unknown>)
        .flatMap((value) => (Array.isArray(value) ? value : [value]))
        .map((value) => String(value))
      if (messages.length > 0) {
        return messages.join(' ')
      }
    }
    return error.detail
  }
  return 'Something went wrong.'
}
