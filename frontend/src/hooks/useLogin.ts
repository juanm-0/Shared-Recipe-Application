import { useMutation, useQueryClient } from '@tanstack/react-query'
import { login } from '../api/auth'

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      login(username, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['me'], user)
    },
  })
}
