'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { 
  getUserProfile, 
  updateUserProfile, 
  getUserPreferences, 
  updateUserPreferences,
  UserProfile,
  UserPreferences
} from '@/lib/supabase-database'

export function useUserData() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      loadUserData()
    } else {
      setProfile(null)
      setPreferences(null)
      setLoading(false)
    }
  }, [user])

  const loadUserData = async () => {
    if (!user) return

    setLoading(true)
    try {
      // Load profile
      const { data: profileData } = await getUserProfile(user.id)
      setProfile(profileData)

      // Load preferences
      const { data: preferencesData } = await getUserPreferences(user.id)
      setPreferences(preferencesData)

    } catch (error) {
      console.error('Error loading user data:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateProfile = async (updates: Partial<UserProfile>) => {
    if (!user) return

    try {
      const { data, error } = await updateUserProfile(user.id, updates)
      if (error) throw error
      setProfile(data)
      return { data, error: null }
    } catch (error) {
      return { data: null, error }
    }
  }

  const updatePreferences = async (updates: Partial<UserPreferences>) => {
    if (!user) return

    try {
      const { data, error } = await updateUserPreferences(user.id, updates)
      if (error) throw error
      setPreferences(data)
      return { data, error: null }
    } catch (error) {
      return { data: null, error }
    }
  }

  // Note: File management functions removed - now using Supabase Storage
  // Files are managed directly through the backend API

  const refreshData = () => {
    if (user) {
      loadUserData()
    }
  }

  return {
    profile,
    preferences,
    loading,
    updateProfile,
    updatePreferences,
    refreshData
  }
}
