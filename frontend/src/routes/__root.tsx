import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { useMe } from '../hooks/useMe'
import { useLogout } from '../hooks/useLogout'
import { ensureCsrfCookie, getErrorMessage } from '../api/client'

let csrfCookiePromise: Promise<void> | null = null

function ensureCsrfCookieOnce(): Promise<void> {
  if (!csrfCookiePromise) {
    csrfCookiePromise = ensureCsrfCookie().catch((error) => {
      csrfCookiePromise = null
      throw error
    })
  }
  return csrfCookiePromise
}

export const Route = createRootRoute({
  beforeLoad: async () => {
    try {
      await ensureCsrfCookieOnce()
    } catch {
      // Non-fatal: if the backend isn't reachable yet, let the app render
      // anyway rather than crashing the whole router. The memo is cleared
      // on failure so the next navigation retries instead of 
      // permanently skipping the CSRF bootstrap.
    }
  },
  component: RootLayout,
})

function RootLayout() {
  return (
    <div>
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <Link to="/" search={{ sort: '-created_at', page: 1 }} className="text-lg font-semibold text-gray-900">
          Shared Recipe Application
        </Link>
        <AuthStatus />
      </header>
      <Outlet />
    </div>
  )
}

function AuthStatus() {
  const me = useMe()
  const logout = useLogout()

  if (me.isLoading) {
    return null
  }

  if (me.isSuccess) {
    return (
      <div className="flex flex-col items-end gap-1">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-700">Hello, {me.data.username}</span>
          <Link
            to="/"
            search={{ sort: '-created_at', page: 1 }}
            className="text-sm text-gray-700 hover:text-blue-600"
          >
            All recipes
          </Link>
          <Link
            to="/"
            search={{ sort: '-created_at', page: 1, owner: me.data.id }}
            className="text-sm text-gray-700 hover:text-blue-600"
          >
            My recipes
          </Link>
          <Link to="/shopping-list" className="text-sm text-gray-700 hover:text-blue-600">
            Shopping list
          </Link>
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Log out
          </button>
        </div>
        {logout.isError && (
          <p role="alert" className="text-sm text-red-600">
            {getErrorMessage(logout.error)}
          </p>
        )}
      </div>
    )
  }

  return (
    <nav className="flex items-center gap-4">
      <Link to="/login" className="text-sm text-gray-700 hover:text-blue-600">
        Log in
      </Link>
      <Link to="/register" className="text-sm text-gray-700 hover:text-blue-600">
        Register
      </Link>
    </nav>
  )
}
