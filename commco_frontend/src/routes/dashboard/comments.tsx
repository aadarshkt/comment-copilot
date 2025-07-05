import { useState } from 'react'
import { createFileRoute, useSearch } from '@tanstack/react-router'
import {
  useCommentsQuery,
  useSyncChannelMutation,
} from '../../queries/commentQueries'
import { Button } from '../../components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Skeleton } from '../../components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert'

const CATEGORIES = [
  'Needs Action',
  'Quick Acknowledge',
  'Review & Delete',
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
  const category = search.category || 'Needs Action'
  const { data, isLoading, isError, error } = useCommentsQuery(category)
  const syncMutation = useSyncChannelMutation()
  const [showToast, setShowToast] = useState(false)

  const handleSync = async () => {
    await syncMutation.mutateAsync()
    setShowToast(true)
    setTimeout(() => setShowToast(false), 2000)
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
          <Alert>
            <AlertTitle>Sync Complete</AlertTitle>
            <AlertDescription>Comments have been refreshed.</AlertDescription>
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
                    <div className="font-semibold">{comment.author_name}</div>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        comment.category === 'Needs Action'
                          ? 'bg-blue-100 text-blue-800'
                          : comment.category === 'Quick Acknowledge'
                            ? 'bg-green-100 text-green-800'
                            : comment.category === 'Review & Delete'
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
                  <div className="mt-2 text-xs text-gray-400">
                    Video ID: {comment.video_id}
                  </div>
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
