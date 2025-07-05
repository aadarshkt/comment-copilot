import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../lib/axios'
import type { User } from '../types/user'

// Query to fetch current user
export const useUserQuery = () => {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: async (): Promise<User> => {
      const response = await api.get('/user/me')
      return response.data
    },
    retry: false, // Don't retry on 401
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Mutation to logout user
export const useLogoutMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/auth/logout')
      return response.data
    },
    onSuccess: () => {
      // Clear user data from cache
      queryClient.setQueryData(['user', 'me'], null)
      // Invalidate user query to ensure clean state
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] })
    },
  })
}
