import React, { createContext, useContext, useEffect, useState } from 'react'
import { useUserQuery } from '../queries/userQueries'
import type { ReactNode } from 'react'
import type { User } from '../types/user'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const { data, error, isLoading: queryLoading } = useUserQuery()

  useEffect(() => {
    if (!queryLoading) {
      if (data && !error) {
        setUser(data)
      } else {
        setUser(null)
      }
      setIsLoading(false)
    }
  }, [data, error, queryLoading])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
