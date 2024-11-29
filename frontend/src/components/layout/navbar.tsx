'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/context/AuthContext'
import { authService } from '@/lib/services/auth'
import { useRouter, usePathname } from 'next/navigation'

export default function Navbar() {
  const { user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = async () => {
    try {
      await authService.signOut()
      router.push('/')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  // Hide auth buttons on login and signup pages
  const isAuthPage = pathname === '/login' || pathname === '/signup'

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex items-center">
              <span className="text-xl font-bold">AI Assistant</span>
            </Link>
          </div>
          
          <div className="flex items-center">
            {!isAuthPage && (
              user ? (
                <div className="flex items-center space-x-4">
                  <Link 
                    href="/dashboard"
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <Link 
                    href="/login"
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Login
                  </Link>
                  <Link
                    href="/signup"
                    className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-500"
                  >
                    Sign up
                  </Link>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}