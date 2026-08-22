import { useState } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRegister } from '../hooks/useRegister'
import { getErrorMessage } from '../api/client'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

function RegisterPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const register = useRegister()
  const navigate = useNavigate()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    register.mutate(
      { username, email, password },
      {
        onSuccess: () => {
          navigate({ to: '/' })
        },
      },
    )
  }

  return (
    <div>
      <h1>Register</h1>
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
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
        <button type="submit" disabled={register.isPending}>
          Register
        </button>
      </form>
      {register.isError && <p role="alert">{getErrorMessage(register.error)}</p>}
    </div>
  )
}
