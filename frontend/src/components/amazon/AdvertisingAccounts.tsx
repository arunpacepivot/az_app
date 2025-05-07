'use client'

import { Button } from '@/components/ui/button'
import { useAmazonAdvertisingProfiles } from '@/lib/hooks/queries/use-amazon-advertising'

export function AdvertisingAccounts() {
  // Disabling profile fetching for now
  // const { data: profiles, isLoading, error, isError } = useAmazonAdvertisingProfiles()
  
  // Instead, show a placeholder message
  return (
    <div className="space-y-4">
      <h3 className="text-md font-medium text-gray-800">Connected Accounts</h3>
      <div className="p-4 rounded-md bg-gray-50 text-gray-600">
        To view your connected Amazon Advertising accounts, please connect your account first.
      </div>
    </div>
  )
} 