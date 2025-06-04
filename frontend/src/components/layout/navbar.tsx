'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useState, useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/lib/context/AuthContext'
import { Button } from '@/components/ui/button'

export function Navbar() {
  const pathname = usePathname()
  const { user, signOut } = useAuth()
  const [isToolsOpen, setIsToolsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Define tools for dropdown with categories for better organization
  const toolCategories = [
    {
      name: "Content Generation",
      tools: [
        { name: 'Listing Generator', href: '/lister', description: 'Generate optimized product listings' },
    
      ]
    },
    {
      name: "Catalog",
      tools: [
        { name: 'SQP Analysis', href: '/sqp', description: 'Analyze search query performance data' },
        { name: 'Cerebro Analysis', href: '/cerebro', description: 'Advanced keyword research and analysis' },
      ]
    },
    {
      name: "Bulk File",
      tools: [
        { name: 'Bulk File Optimizer', href: '/sp', description: 'Optimize your Sponsored Products campaigns' },
      ]
    },
    {
      name: "Advertising",
      tools: [
        { name: 'N-gram Analysis', href: '/ngram', description: 'Analyze keyword performance using n-gram techniques' },
        { name: 'Topical Analysis', href: '/topical', description: 'Advanced topic and trend analysis' },
      ]
    },
    // Future categories can be added here
  ]
  
  // Flatten tools for active check
  const allTools = toolCategories.flatMap(category => category.tools)
  const isToolActive = allTools.some(tool => pathname?.startsWith(tool.href))

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsToolsOpen(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <nav className="bg-gray-900 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            {/* Logo */}
            <Link href={user ? "/" : "/login"} className="flex items-center h-16">
              <div className="relative h-10 w-40 bg-white/10 rounded-md p-1">
                <Image
                  src="/logo.jpg"
                  alt="PacePivot Logo"
                  fill
                  sizes="(max-width: 768px) 120px, 160px"
                  className="object-contain"
                  priority
                />
              </div>
            </Link>
            
            {/* Main Navigation - Only shown when logged in */}
            {user && (
              <div className="hidden md:block ml-10">
                <div className="flex items-center space-x-4">
                  <Link href="/dashboard" className={`px-3 py-2 rounded-md text-sm font-medium ${
                    pathname === '/dashboard' 
                      ? 'bg-gray-800 text-white' 
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}>
                    Dashboard
                  </Link>
                  
                  {/* Tools Dropdown */}
                  <div className="relative" ref={dropdownRef}>
                    <button
                      onClick={() => setIsToolsOpen(!isToolsOpen)}
                      className={`px-3 py-2 rounded-md text-sm font-medium flex items-center ${
                        isToolActive
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      Tools
                      <ChevronDownIcon 
                        className={`ml-1 h-4 w-4 transition-transform ${isToolsOpen ? 'rotate-180' : ''}`} 
                      />
                    </button>
                    
                    {/* Enhanced Dropdown Menu with Categories */}
                    {isToolsOpen && (
                      <div className="absolute dropdown-menu mt-2 w-80 bg-gray-800 rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 focus:outline-none max-h-[calc(100vh-120px)] overflow-y-auto">
                        {toolCategories.map((category, idx) => (
                          <div key={category.name} className={idx > 0 ? "mt-2" : ""}>
                            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700">
                              {category.name}
                            </div>
                            <div>
                              {category.tools.map((tool) => (
                                <Link
                                  key={tool.href}
                                  href={tool.href}
                                  className={`block px-4 py-3 hover:bg-gray-700 transition-colors ${
                                    pathname === tool.href ? 'bg-gray-700/60 border-l-2 border-yellow-400' : ''
                                  }`}
                                  onClick={() => setIsToolsOpen(false)}
                                >
                                  <div className="font-medium text-white">{tool.name}</div>
                                  <div className="text-xs text-gray-400 mt-1">{tool.description}</div>
                                </Link>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* User Menu */}
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              {user ? (
                <Button 
                  variant="ghost" 
                  className="ml-2 text-gray-300 hover:bg-gray-700 hover:text-white"
                  onClick={() => signOut()}
                >
                  Sign Out
                </Button>
              ) : (
                <Link href="/login">
                  <Button className="bg-yellow-400 text-black hover:bg-yellow-300">Sign In</Button>
                </Link>
              )}
            </div>
          </div>
          
          {/* Mobile menu button - Only shown when logged in */}
          {user && (
            <div className="md:hidden flex items-center">
              <button
                type="button"
                className="bg-gray-800 inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none"
                aria-controls="mobile-menu"
                aria-expanded="false"
                onClick={() => setIsToolsOpen(!isToolsOpen)}
              >
                <span className="sr-only">Open main menu</span>
                {/* Icon for menu - 3 horizontal lines */}
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
                {/* Icon for X - close menu */}
                <svg className="hidden h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile menu - Only shown when logged in */}
      {user && isToolsOpen && (
        <div className="md:hidden z-50 relative" id="mobile-menu">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link href="/dashboard" className={`block px-3 py-2 rounded-md text-base font-medium ${
              pathname === '/dashboard' 
                ? 'bg-gray-800 text-white' 
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}>
              Dashboard
            </Link>
            
            {/* Mobile Categories */}
            {toolCategories.map((category) => (
              <div key={category.name}>
                <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {category.name}
                </div>
                
                {/* Tool Links */}
                {category.tools.map((tool) => (
                  <Link
                    key={tool.href}
                    href={tool.href}
                    className={`block px-3 py-2 rounded-md text-base font-medium ${
                      pathname === tool.href
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    {tool.name}
                  </Link>
                ))}
              </div>
            ))}
          </div>
          
          {/* Mobile user menu */}
          <div className="pt-4 pb-3 border-t border-gray-700">
            <div className="px-2 space-y-1">
              <button
                className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                onClick={() => signOut()}
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}