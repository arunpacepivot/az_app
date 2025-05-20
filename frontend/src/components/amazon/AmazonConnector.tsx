'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/context/AuthContext'
import { Button } from '@/components/ui/button'
import { useConnectAmazonAdvertising } from '@/lib/hooks/queries/use-amazon-advertising'
import { AdvertisingAccounts } from './AdvertisingAccounts'
import { AlertTriangle, ArrowRight, ShoppingCart } from 'lucide-react'
import { Icons } from '../icons'

export function AmazonConnector() {
  const { user } = useAuth()
  const [connectError, setConnectError] = useState<string | null>(null)
  
  const { 
    mutate: connectAmazonAdvertising, 
    isPending: isConnectingAdvertising 
  } = useConnectAmazonAdvertising()

  const handleConnectAmazonAdvertising = () => {
    if (!user) return
    setConnectError(null)
    
    connectAmazonAdvertising(
      { 
        userId: user.uid,
        scopes: 'advertising::campaign_management'  // Single scope to match curl example
      },
      {
        onSuccess: (data) => {
          // Redirect user to Amazon's consent screen
          window.location.href = data.authorization_url
        },
        onError: (error) => {
          console.error('Error connecting to Amazon Advertising:', error)
          setConnectError(`Failed to connect to Amazon Advertising: ${error.message}`)
        }
      }
    )
  }

  // This will be implemented in the future
  const handleConnectAmazonSeller = () => {
    alert('Amazon Seller connection will be available soon!')
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Amazon Advertising Connection */}
        <div className="p-6 rounded-xl bg-white shadow-sm border border-gray-100">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
              <Icons.amazonAds className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-800 mb-2">Amazon Advertising</h3>
              <p className="text-gray-600 mb-4">Connect your Amazon Advertising account to manage campaigns and track performance metrics.</p>
              
              <Button 
                onClick={handleConnectAmazonAdvertising}
                disabled={isConnectingAdvertising}
                className="w-full sm:w-auto flex items-center gap-2 bg-amazon hover:bg-amazon/90 text-white"
              >
                {isConnectingAdvertising ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-opacity-50 border-t-transparent rounded-full" />
                    Connecting...
                  </>
                ) : (
                  <>
                    Connect Amazon Advertising
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
          
          {connectError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-md text-red-800 text-sm flex gap-2">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <span>{connectError}</span>
            </div>
          )}
          
          <div className="mt-6">
            <AdvertisingAccounts />
          </div>
        </div>
        
        {/* Amazon Seller Connection - Coming Soon */}
        <div className="p-6 rounded-xl bg-white shadow-sm border border-gray-100 opacity-80">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-full bg-orange-100 flex items-center justify-center">
              <ShoppingCart className="w-5 h-5 text-orange-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-800 mb-2">Amazon Seller (Coming Soon)</h3>
              <p className="text-gray-600 mb-4">Connect your Amazon Seller account to manage inventory, sales, and customer data.</p>
              
              <Button 
                onClick={handleConnectAmazonSeller}
                variant="outline"
                className="w-full sm:w-auto relative border-orange-200 text-orange-700"
                disabled
              >
                <span>Connect Amazon Seller</span>
                <span className="absolute -top-2 -right-2 text-xs bg-orange-500 text-white px-2 py-0.5 rounded-full">
                  Soon
                </span>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 