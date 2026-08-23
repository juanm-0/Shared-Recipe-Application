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
      <header>
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
      <div>
        <span>Hello, {me.data.username}</span>
        <button type="button" onClick={() => logout.mutate()} disabled={logout.isPending}>
          Log out
        </button>
        {logout.isError && <p role="alert">{getErrorMessage(logout.error)}</p>}
      </div>
    )
  }

  return (
    <nav>
      <Link to="/login">Log in</Link>
      <Link to="/register">Register</Link>
    </nav>
  )
}
