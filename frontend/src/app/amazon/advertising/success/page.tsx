'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'

export default function AmazonAdvertisingSuccess() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [profiles, setProfiles] = useState<string[]>([])

  useEffect(() => {
    // Get profiles from URL query parameters - handle both formats from the backend
    const profilesParam = searchParams.get('profiles')
    const profileIdParam = searchParams.get('profile_id')
    
    if (profilesParam) {
      setProfiles(profilesParam.split(','))
    } else if (profileIdParam) {
      // If we receive a single profile_id parameter
      setProfiles([profileIdParam])
    }
  }, [searchParams])

  const handleReturnToDashboard = () => {
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white/80 backdrop-blur-lg shadow-xl rounded-2xl p-8 border border-gray-100">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
            <svg className="h-8 w-8 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Successfully Connected!
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Your Amazon Advertising account has been successfully connected.
          </p>
          
          {profiles.length > 0 && (
            <div className="mt-4">
              <p className="font-medium text-gray-700">Connected profiles:</p>
              <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                {profiles.map((profile, index) => (
                  <li key={index}>{profile}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="mt-8">
          <Button 
            onClick={handleReturnToDashboard}
            className="w-full"
          >
            Return to Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
} 