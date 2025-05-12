'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'

export default function AmazonAdvertisingError() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [errorMessage, setErrorMessage] = useState('An error occurred during the Amazon Advertising connection process.')

  useEffect(() => {
    // Get error from URL query parameters - backend uses 'message'
    const messageParam = searchParams.get('message')
    const errorParam = searchParams.get('error')
    
    if (messageParam) {
      setErrorMessage(messageParam)
    } else if (errorParam) {
      setErrorMessage(errorParam)
    }
  }, [searchParams])

  const handleReturnToDashboard = () => {
    router.push('/dashboard')
  }

  const handleTryAgain = () => {
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white/80 backdrop-blur-lg shadow-xl rounded-2xl p-8 border border-gray-100">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
            <svg className="h-8 w-8 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Connection Error
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {errorMessage}
          </p>
        </div>
        
        <div className="mt-8 space-y-3">
          <Button 
            onClick={handleTryAgain}
            className="w-full bg-indigo-600 hover:bg-indigo-500"
          >
            Try Again
          </Button>
          
          <Button 
            onClick={handleReturnToDashboard}
            variant="outline"
            className="w-full"
          >
            Return to Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
} 