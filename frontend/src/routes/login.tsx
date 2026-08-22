import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useLogin } from '../hooks/useLogin'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const navigate = useNavigate()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    login.mutate(
      { username, password },
      {
        onSuccess: () => {
          navigate({ to: '/' })
        },
      },
    )
  }

  return (
    <div>
      <h1>Log in</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" disabled={login.isPending}>
          Log in
        </button>
      </form>
      {login.isError && <p role="alert">{getErrorMessage(login.error)}</p>}
    </div>
  )
}
