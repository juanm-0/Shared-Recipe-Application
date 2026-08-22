import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { useMe } from '../hooks/useMe'
import { useLogout } from '../hooks/useLogout'
import { ensureCsrfCookie } from '../api/client'

let csrfCookieEnsured = false

export const Route = createRootRoute({
  beforeLoad: async () => {
    if (!csrfCookieEnsured) {
      csrfCookieEnsured = true
      await ensureCsrfCookie()
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
