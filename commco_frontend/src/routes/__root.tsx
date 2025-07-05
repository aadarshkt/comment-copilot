import { Outlet, createRootRoute } from '@tanstack/react-router'
import { AuthProvider } from '../context/AuthContext'
import Header from '../components/Header'

export const Route = createRootRoute({
  component: () => (
    <AuthProvider>
      <Header />
      <Outlet />
    </AuthProvider>
  ),
})
