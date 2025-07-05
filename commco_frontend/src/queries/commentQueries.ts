import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../lib/axios'
import type { Comment } from '../types/comment'

// Query to fetch comments for a specific category
export const useCommentsQuery = (category: string) => {
  return useQuery({
    queryKey: ['comments', category],
    queryFn: async (): Promise<Array<Comment>> => {
      const response = await api.get('/comments', {
        params: { category },
      })
      return response.data
    },
    enabled: !!category,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Mutation to sync channel comments
export const useSyncChannelMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/channel/sync')
      return response.data
    },
    onSuccess: () => {
      // Invalidate all comments queries to refetch data
      queryClient.invalidateQueries({ queryKey: ['comments'] })
    },
  })
}

// Mutation to reply to a comment
export const useReplyToCommentMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      commentId,
      replyText,
    }: {
      commentId: number
      replyText: string
    }) => {
      const response = await api.post(`/comments/${commentId}/reply`, {
        reply_text: replyText,
      })
      return response.data
    },
    onSuccess: () => {
      // Invalidate all comments queries to refetch data
      queryClient.invalidateQueries({ queryKey: ['comments'] })
    },
  })
}
