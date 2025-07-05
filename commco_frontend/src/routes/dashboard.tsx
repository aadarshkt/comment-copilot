import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'
import { useAuth } from '../hooks/useAuth'

export const Route = createFileRoute('/dashboard')({
  beforeLoad: ({ context }) => {
    // This will be called before the route loads
    // We'll handle auth check in the component instead
  },
  component: DashboardLayout,
})

function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Redirect if not authenticated
  if (!isAuthenticated) {
    window.location.href = '/'
    return null
  }

  // Render dashboard if authenticated
  return (
    <div className="container mx-auto px-4 py-8">
      <Outlet />
    </div>
  )
}
