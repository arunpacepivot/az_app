'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/context/AuthContext'

type AdvertisingProfile = {
  profileId: string
  accountInfo?: {
    marketplaceStringId?: string
    id?: string
    name?: string
  }
  error?: string
}

export function AdvertisingAccounts() {
  const { user } = useAuth()
  const [profiles, setProfiles] = useState<AdvertisingProfile[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchProfiles = async () => {
      if (!user) {
        setIsLoading(false)
        setError('Authentication required')
        return
      }
      
      try {
        setIsLoading(true)
        // Get the user's ID token for authentication
        const idToken = await user.getIdToken()
        
        const response = await fetch('/api/amazon/advertising/profiles', {
          headers: {
            'Authorization': `Bearer ${idToken}`
          }
        })
        
        if (!response.ok) {
          throw new Error('Failed to fetch advertising profiles')
        }
        
        const data = await response.json()
        setProfiles(data)
      } catch (error) {
        console.error('Error fetching advertising profiles:', error)
        setError('Failed to load your Amazon Advertising accounts')
      } finally {
        setIsLoading(false)
      }
    }

    fetchProfiles()
  }, [user])

  if (isLoading) {
    return (
      <div className="p-4 flex justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 rounded-md bg-red-50 text-red-600">
        {error}
      </div>
    )
  }

  if (profiles.length === 0) {
    return (
      <div className="p-4 rounded-md bg-gray-50 text-gray-600">
        No Amazon Advertising accounts connected.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-md font-medium text-gray-800">Connected Accounts</h3>
      <div className="space-y-2">
        {profiles.map((profile) => (
          <div 
            key={profile.profileId}
            className="p-3 rounded-md border border-gray-200 bg-white flex justify-between items-center"
          >
            <div>
              <div className="font-medium">{profile.accountInfo?.name || 'Advertising Profile'}</div>
              <div className="text-sm text-gray-500">ID: {profile.profileId}</div>
              {profile.accountInfo?.marketplaceStringId && (
                <div className="text-sm text-gray-500">Marketplace: {profile.accountInfo.marketplaceStringId}</div>
              )}
              {profile.error && (
                <div className="text-sm text-red-500">{profile.error}</div>
              )}
            </div>
            <Button variant="outline" size="sm">
              View
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
} 