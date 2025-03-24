'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { onAuthStateChanged, User, signOut as firebaseSignOut } from 'firebase/auth'
import { auth } from '@/lib/firebase'

interface AuthContextType {
  user: User | null
  loading: boolean
  error: Error | null
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  error: null,
  signOut: async () => {}
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [authInitialized, setAuthInitialized] = useState(false)

  const signOut = async () => {
    try {
      if (auth) {
        await firebaseSignOut(auth);
      }
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  useEffect(() => {
    // Only run this effect on the client side
    if (typeof window === 'undefined') return;

    let timeoutId: NodeJS.Timeout;
    let unsubscribe: () => void;

    const initializeAuth = async () => {
      try {
        if (!auth) {
          throw new Error('Firebase auth not initialized');
        }

        // Set up timeout
        timeoutId = setTimeout(() => {
          if (loading && !authInitialized) {
            setLoading(false)
            setError(new Error('Auth initialization timed out'))
          }
        }, 5000) // Reduced to 5 seconds

        // Set up auth state listener
        unsubscribe = onAuthStateChanged(
          auth,
          (user) => {
            setUser(user)
            setLoading(false)
            setError(null)
            setAuthInitialized(true)
            clearTimeout(timeoutId)
          },
          (error) => {
            console.error('Auth error:', error)
            setError(error)
            setLoading(false)
            setAuthInitialized(true)
            clearTimeout(timeoutId)
          }
        )
      } catch (error) {
        console.error('Auth setup error:', error)
        setError(error instanceof Error ? error : new Error('Auth setup failed'))
        setLoading(false)
        setAuthInitialized(true)
        clearTimeout(timeoutId)
      }
    }

    initializeAuth()

    return () => {
      if (unsubscribe) unsubscribe()
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [])

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
        <div className="text-red-400 text-center p-4">
          <p>Authentication Error</p>
          <p className="text-sm">{error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
        <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-yellow-400"></div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext) 