'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/icons'
import Link from 'next/link'

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
            <Icons.error className="h-8 w-8 text-red-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Connection Error
          </h2>
          <p className="mt-4 text-sm text-gray-600 bg-red-50 p-4 rounded-lg border border-red-100">
            {errorMessage}
          </p>
          
          <div className="mt-6 text-left bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-medium text-gray-800 mb-2">Troubleshooting Tips:</h3>
            <ul className="text-sm text-gray-600 space-y-2 list-disc pl-5">
              <li>Make sure you have admin access to your Amazon Advertising account</li>
              <li>Check that cookies are enabled in your browser</li>
              <li>Try using a different browser or clearing your cache</li>
              <li>Ensure you're logged into the correct Amazon account</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8 space-y-3">
          <Button 
            onClick={handleTryAgain}
            className="w-full bg-gradient-to-r from-indigo-600 to-blue-500 hover:from-indigo-700 hover:to-blue-600"
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
          
          <div className="text-center text-sm text-gray-500">
            <Link href="/support" className="text-indigo-600 hover:text-indigo-700 hover:underline">
              Contact support for assistance
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
} 