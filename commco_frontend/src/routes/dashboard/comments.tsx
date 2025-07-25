import { useState } from 'react'
import { createFileRoute, useSearch } from '@tanstack/react-router'
import {
  useCommentsQuery,
  useReplyToCommentMutation,
  useSyncChannelMutation,
} from '../../queries/commentQueries'
import { Button } from '../../components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Skeleton } from '../../components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '../../components/ui/tooltip'

const CATEGORIES = [
  'Reply to Question',
  'Appreciate Fan',
  'Ideas',
  'Criticisms',
  'Delete Junk',
  'Miscellaneous',
  'All',
]

export const Route = createFileRoute('/dashboard/comments')({
  component: CommentsPage,
  validateSearch: (search: Record<string, unknown>) => ({
    category: search.category as string | undefined,
  }),
})

function CommentsPage() {
  const search = useSearch({ from: '/dashboard/comments' })
  const category = search.category || 'Reply to Question'
  const { data, isLoading, isError, error } = useCommentsQuery(category)
  const syncMutation = useSyncChannelMutation()
  const replyMutation = useReplyToCommentMutation()
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState<'success' | 'error'>('success')
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyTexts, setReplyTexts] = useState<Record<number, string>>({})

  const showToastMessage = (
    message: string,
    type: 'success' | 'error' = 'success',
  ) => {
    setToastMessage(message)
    setToastType(type)
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  const handleSync = async () => {
    try {
      await syncMutation.mutateAsync()
      showToastMessage('Comments have been refreshed.')
    } catch (error) {
      showToastMessage('Failed to sync comments. Please try again.', 'error')
    }
  }

  const handleReplyClick = (commentId: number) => {
    if (replyingTo === commentId) {
      // If already replying to this comment, close it
      setReplyingTo(null)
      setReplyTexts((prev) => {
        const newState = { ...prev }
        delete newState[commentId]
        return newState
      })
    } else {
      // Open reply section for this comment
      setReplyingTo(commentId)
      setReplyTexts((prev) => ({ ...prev, [commentId]: '' }))
    }
  }

  const handleSendReply = async (commentId: number) => {
    const replyText = (replyTexts[commentId] || '').trim()
    if (!replyText) return

    try {
      await replyMutation.mutateAsync({
        commentId,
        replyText,
      })
      setReplyingTo(null)
      setReplyTexts((prev) => {
        const newState = { ...prev }
        delete newState[commentId]
        return newState
      })
      showToastMessage('Reply sent successfully!')
    } catch (error) {
      console.error('Failed to send reply:', error)
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Failed to send reply. Please try again.'
      showToastMessage(errorMessage, 'error')
    }
  }

  const handleCancelReply = (commentId: number) => {
    setReplyingTo(null)
    setReplyTexts((prev) => {
      const newState = { ...prev }
      delete newState[commentId]
      return newState
    })
  }

  const handleReplyTextChange = (commentId: number, text: string) => {
    setReplyTexts((prev) => ({ ...prev, [commentId]: text }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Tabs value={category} className="w-full">
          <TabsList>
            {CATEGORIES.map((cat) => (
              <TabsTrigger key={cat} value={cat} asChild>
                <a
                  href={`?category=${encodeURIComponent(cat)}`}
                  className={category === cat ? 'font-bold' : ''}
                >
                  {cat}
                </a>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Button
          onClick={handleSync}
          disabled={syncMutation.isPending}
          className="ml-4"
        >
          {syncMutation.isPending ? 'Syncing...' : 'Sync Channel'}
        </Button>
      </div>
      {showToast && (
        <div className="fixed top-4 right-4 z-50">
          <Alert variant={toastType === 'success' ? 'default' : 'destructive'}>
            <AlertTitle>
              {toastType === 'success' ? 'Success' : 'Error'}
            </AlertTitle>
            <AlertDescription>{toastMessage}</AlertDescription>
          </Alert>
        </div>
      )}

      <div className="mt-6">
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        ) : isError ? (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {error instanceof Error
                ? error.message
                : 'Failed to load comments.'}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-4">
            {data && data.length > 0 ? (
              data.map((comment) => (
                <div
                  key={comment.id}
                  className="border rounded-lg p-4 bg-white shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex justify-center items-center">
                      <div className="font-semibold">{comment.author_name}</div>
                      <div className="flex text-xs text-gray-400 justify-center items-center">
                        <a
                          href={`https://www.youtube.com/watch?v=${comment.video_id}&lc=${comment.youtube_comment_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
                        >
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <svg
                                className="w-3 h-3 inline-block ml-1"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                xmlns="http://www.w3.org/2000/svg"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                />
                              </svg>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Link to comment on YouTube</p>
                            </TooltipContent>
                          </Tooltip>
                        </a>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        comment.category === 'Reply to Question'
                          ? 'bg-blue-100 text-blue-800'
                          : comment.category === 'Quick Acknowledge'
                            ? 'bg-green-100 text-green-800'
                            : comment.category === 'Ideas'
                              ? 'bg-yellow-100 text-yellow-800'
                              : comment.category === 'Criticisms'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {comment.category}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(comment.published_at).toLocaleDateString()}
                  </div>
                  <div className="mt-2">{comment.text_original}</div>

                  <div className="mt-3">
                    <Button
                      size="default"
                      variant="outline"
                      onClick={() => handleReplyClick(comment.id)}
                      disabled={replyMutation.isPending}
                    >
                      {replyMutation.isPending && replyingTo === comment.id
                        ? 'Sending...'
                        : 'Reply'}
                    </Button>
                  </div>

                  {/* Inline Reply Section */}
                  {replyingTo === comment.id && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="space-y-3">
                        <textarea
                          value={replyTexts[comment.id] || ''}
                          onChange={(e) =>
                            handleReplyTextChange(comment.id, e.target.value)
                          }
                          placeholder={`Reply to ${comment.author_name}...`}
                          className="w-full h-20 p-3 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCancelReply(comment.id)}
                            disabled={replyMutation.isPending}
                          >
                            Cancel
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleSendReply(comment.id)}
                            disabled={
                              replyMutation.isPending ||
                              !(replyTexts[comment.id] || '').trim()
                            }
                          >
                            {replyMutation.isPending
                              ? 'Sending...'
                              : 'Send Reply'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500">
                No comments found for this category.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
