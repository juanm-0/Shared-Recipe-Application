import { apiFetch } from './client'

export interface User {
  id: number
  username: string
}

export function getMe(): Promise<User> {
  return apiFetch<User>('/api/auth/me/')
}

export function login(username: string, password: string): Promise<User> {
  return apiFetch<User>('/api/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function register(username: string, email: string, password: string): Promise<User> {
  return apiFetch<User>('/api/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
}

export function logout(): Promise<void> {
  return apiFetch<void>('/api/auth/logout/', {
    method: 'POST',
  })
}
