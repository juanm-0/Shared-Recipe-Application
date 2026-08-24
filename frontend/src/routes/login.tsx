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
    <div className="mx-auto mt-12 max-w-sm p-6">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Log in</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="username" className="text-sm font-medium text-gray-700">
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="password" className="text-sm font-medium text-gray-700">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={login.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Log in
        </button>
      </form>
      {login.isError && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          {getErrorMessage(login.error)}
        </p>
      )}
    </div>
  )
}
