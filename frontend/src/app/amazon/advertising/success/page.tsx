'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/icons'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'

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
            <Icons.success className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Successfully Connected!
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Your Amazon Advertising account has been successfully connected to PacePivot.
          </p>
          
          {profiles.length > 0 && (
            <div className="mt-6">
              <p className="font-medium text-gray-700 mb-3">Connected profiles:</p>
              <div className="space-y-3">
                {profiles.map((profile, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="font-medium text-gray-800 flex items-center">
                      <Icons.amazonAds className="w-5 h-5 text-blue-600 mr-2" />
                      <span>{profile}</span>
                    </div>
                    <Badge variant="success">Active</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="mt-8 space-y-3">
          <Button 
            onClick={handleReturnToDashboard}
            className="w-full bg-gradient-to-r from-indigo-600 to-blue-500 hover:from-indigo-700 hover:to-blue-600"
          >
            Go to Dashboard
          </Button>
          
          <div className="text-center text-sm text-gray-500">
            <Link href="/support" className="text-indigo-600 hover:text-indigo-700 hover:underline">
              Need help with your connection?
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
} 