'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { apiService } from '@/lib/services/api'
import { Button } from '@/components/ui/button'
import { AmazonConnector } from '@/components/amazon/AmazonConnector'

export default function Dashboard() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [connectivityResult, setConnectivityResult] = useState<string | null>(null)
  const [connectivityError, setConnectivityError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  const handleConnectivityTest = async () => {
    try {
      const result = await apiService.testConnectivity('Hello from frontend!')
      setConnectivityResult(result.message)
      setConnectivityError(null)
    } catch (error) {
      console.error('Connectivity test error:', error)
      setConnectivityError('Connectivity test failed')
      setConnectivityResult(null)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white/80 backdrop-blur-lg shadow-xl rounded-2xl p-8 border border-gray-100">
          <div className="flex items-center space-x-4 mb-6">
            <div className="h-16 w-16 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-2xl text-white font-bold">
              {user?.displayName?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase()}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {user?.displayName || 'User'}!
              </h1>
              <p className="text-gray-600">{user?.email}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            <div className="p-6 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 text-white">
              <h2 className="text-xl font-semibold mb-2">Quick Stats</h2>
              <p>Your account was created on {user?.metadata.creationTime}</p>
            </div>
            <div className="p-6 rounded-xl bg-white shadow-sm border border-gray-100">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Account Info</h2>
              <p className="text-gray-600">Last login: {user?.metadata.lastSignInTime}</p>
            </div>
          </div>

          <div className="mt-10">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Amazon Integrations</h2>
            <AmazonConnector />
          </div>
            
          <div className="p-6 rounded-xl bg-white shadow-sm border border-gray-100 mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">API Connection</h2>
            <Button 
              onClick={handleConnectivityTest}
              variant="outline"
              className="mb-4"
            >
              Test Backend Connectivity
            </Button>
            
            {connectivityResult && (
              <div className="p-4 bg-green-100 text-green-800 rounded">
                {connectivityResult}
              </div>
            )}
            
            {connectivityError && (
              <div className="p-4 bg-red-100 text-red-800 rounded">
                {connectivityError}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 