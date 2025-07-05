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

const CATEGORIES = ['Needs Action', 'Resolved', 'Spam', 'All']

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
                  <div className="font-semibold">{comment.author}</div>
                  <div className="text-sm text-gray-500">
                    {comment.published_at}
                  </div>
                  <div className="mt-2">{comment.text}</div>
                  <div className="mt-2 text-xs text-gray-400">
                    {comment.video_title}
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
