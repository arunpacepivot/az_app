'use client'

import { Button } from '@/components/ui/button'
import { useAmazonAdvertisingProfiles } from '@/lib/hooks/queries/use-amazon-advertising'
import { useState } from 'react'
import { Badge } from '../ui/badge'
import { AlertCircle } from 'lucide-react'

export function AdvertisingAccounts() {
  const { data: profiles, isLoading, error, isError, refetch } = useAmazonAdvertisingProfiles()
  const [isRefetching, setIsRefetching] = useState(false)
  
  const handleRefresh = async () => {
    setIsRefetching(true)
    await refetch()
    setIsRefetching(false)
  }
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-md font-medium text-gray-800">Connected Accounts</h3>
        {profiles && profiles.length > 0 && (
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleRefresh} 
            disabled={isLoading || isRefetching}
          >
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </Button>
        )}
      </div>
      
      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-600"></div>
        </div>
      ) : isError ? (
        <div className="p-4 rounded-md bg-red-50 text-red-800 flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Failed to load connected accounts</p>
            <p className="text-sm">{error?.message || 'Please try again later'}</p>
          </div>
        </div>
      ) : profiles && profiles.length > 0 ? (
        <div className="space-y-3">
          {profiles.map((profile, index) => (
            <div key={index} className="p-4 rounded-md bg-white border border-gray-200 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-gray-900">{profile.profileName || profile.profile_id}</h4>
                  <p className="text-sm text-gray-500">{profile.accountId || 'Amazon Advertising'}</p>
                </div>
                <Badge variant={profile.status === 'enabled' ? 'success' : 'secondary'}>
                  {profile.status || 'Connected'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-5 rounded-md bg-gray-50 border border-gray-200 text-gray-600 text-center">
          <p className="mb-2">No advertising accounts connected yet</p>
          <p className="text-sm">Connect your Amazon Advertising account to manage campaigns and view performance metrics.</p>
        </div>
      )}
    </div>
  )
} 