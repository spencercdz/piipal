'use client'

import React, { useState } from 'react'
import { User, LogOut, ChevronDown } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/hooks/useUserData'

interface UserProfileProps {
  onSignOut: () => void
}

export default function UserProfile({ onSignOut }: UserProfileProps) {
  const { user } = useAuth()
  const { profile } = useUserData()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const handleSignOut = async () => {
    await onSignOut()
    setIsDropdownOpen(false)
  }

  if (!user) return null

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-3 p-3 rounded-lg bg-[hsl(var(--interaction-bg))] hover:bg-[hsl(var(--hover-bg))] transition-all duration-200 hover-lift w-full"
      >
        <div className="w-12 h-12 bg-[hsl(var(--tiktok-red))] rounded-lg flex items-center justify-center flex-shrink-0">
          <User className="h-6 w-6 text-white" />
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm font-medium text-white truncate">
            {profile?.display_name || user.email}
          </p>
          <p className="text-xs text-gray-400 truncate">Free Plan</p>
        </div>
        <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform duration-200 flex-shrink-0 ${
          isDropdownOpen ? 'rotate-180' : ''
        }`} />
      </button>

      {/* Dropdown Menu */}
      {isDropdownOpen && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-[hsl(var(--card-background))] border border-[hsl(var(--border-color))] rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={handleSignOut}
            className="flex items-center space-x-3 p-3 hover:bg-[hsl(var(--hover-bg))] transition-colors w-full text-left"
          >
            <LogOut className="h-4 w-4 text-[hsl(var(--tiktok-red))]" />
            <span className="text-sm text-[hsl(var(--tiktok-red))]">Sign Out</span>
          </button>
        </div>
      )}
    </div>
  )
}
