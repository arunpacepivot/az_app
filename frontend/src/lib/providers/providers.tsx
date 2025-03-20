'use client'

import { QueryProvider } from './query-provider'
import { AuthProvider } from '@/lib/context/AuthContext'
import { ErrorBoundary } from '@/components/error-boundary'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </QueryProvider>
    </ErrorBoundary>
  )
} 