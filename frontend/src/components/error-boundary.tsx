'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error) {
    console.error('Error caught by boundary:', error)
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
            <div className="text-red-400 text-center p-4">
              <h2>Something went wrong</h2>
              <p className="text-sm">{this.state.error?.message}</p>
              <button
                className="mt-4 px-4 py-2 bg-yellow-400 text-black rounded hover:bg-yellow-300"
                onClick={() => this.setState({ hasError: false })}
              >
                Try again
              </button>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
} 