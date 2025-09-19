'use client'

import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from './LoadingSpinner'

interface ProtectedRouteProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  onSignIn?: () => void
}

export default function ProtectedRoute({ children, fallback, onSignIn }: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-[hsl(var(--background))] flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return fallback || (
      <div className="min-h-screen bg-[hsl(var(--background))] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Authentication Required</h1>
          <p className="text-gray-400 mb-6">Please sign in to access this content.</p>
          {onSignIn && (
            <button
              onClick={onSignIn}
              className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 hover-lift hover-glow"
            >
              Join Now!
            </button>
          )}
        </div>
      </div>
    )
  }

  return <>{children}</>
}
