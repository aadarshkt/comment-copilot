import { useEffect } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/ui/card'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth()

  // Redirect to dashboard if authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      window.location.href = '/dashboard/comments'
    }
  }, [isAuthenticated, isLoading])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-4xl font-bold text-gray-900 mb-4">
            Comment Copilot
          </CardTitle>
          <CardDescription className="text-xl text-gray-600">
            Streamline your YouTube comment management with AI-powered insights
            and organization
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Organize comments by category</span>
            </div>
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>AI-powered comment analysis</span>
            </div>
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>Seamless YouTube integration</span>
            </div>
          </div>

          <Button asChild size="lg" className="w-full max-w-xs">
            <a href="http://localhost:5001/api/auth/google/login">
              Get Started with Google
            </a>
          </Button>

          <p className="text-sm text-gray-500">
            Sign in with your Google account to connect your YouTube channel
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
