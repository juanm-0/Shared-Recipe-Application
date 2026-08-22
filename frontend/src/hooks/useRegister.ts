import { useMutation, useQueryClient } from '@tanstack/react-query'
import { register } from '../api/auth'

export function useRegister() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      username,
      email,
      password,
    }: {
      username: string
      email: string
      password: string
    }) => register(username, email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['me'], user)
    },
  })
}
