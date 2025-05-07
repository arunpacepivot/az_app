'use client'

import { Button } from '@/components/ui/button'
import { useAmazonAdvertisingProfiles } from '@/lib/hooks/queries/use-amazon-advertising'

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
  const { data: profiles, isLoading, error, isError } = useAmazonAdvertisingProfiles()

  if (isLoading) {
    return (
      <div className="p-4 flex justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-4 rounded-md bg-red-50 text-red-600">
        {error?.message || 'Failed to load your Amazon Advertising accounts'}
      </div>
    )
  }

  if (!profiles || profiles.length === 0) {
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