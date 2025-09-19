import { supabase } from './supabase'

// User Profile Types
export interface UserProfile {
  id: string
  user_id: string
  email: string
  display_name?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export interface UserPreferences {
  id: string
  user_id: string
  auto_process: boolean
  email_notifications: boolean
  theme: 'dark' | 'light'
  language: string
  created_at: string
  updated_at: string
}

// User Profile Functions
export const createUserProfile = async (userId: string, email: string, displayName?: string) => {
  const { data, error } = await supabase
    .from('user_profiles')
    .insert([
      {
        user_id: userId,
        email: email,
        display_name: displayName,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ])
    .select()
    .single()

  return { data, error }
}

export const getUserProfile = async (userId: string) => {
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', userId)
    .single()

  return { data, error }
}

export const updateUserProfile = async (userId: string, updates: Partial<UserProfile>) => {
  const { data, error } = await supabase
    .from('user_profiles')
    .update({
      ...updates,
      updated_at: new Date().toISOString()
    })
    .eq('user_id', userId)
    .select()
    .single()

  return { data, error }
}

// Note: File management functions removed - now using Supabase Storage
// Files are stored directly in Supabase Storage with user-specific folders

// User Preferences Functions
export const createUserPreferences = async (userId: string) => {
  const { data, error } = await supabase
    .from('user_preferences')
    .insert([
      {
        user_id: userId,
        auto_process: true,
        email_notifications: true,
        theme: 'dark',
        language: 'en',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ])
    .select()
    .single()

  return { data, error }
}

export const getUserPreferences = async (userId: string) => {
  const { data, error } = await supabase
    .from('user_preferences')
    .select('*')
    .eq('user_id', userId)
    .single()

  return { data, error }
}

export const updateUserPreferences = async (userId: string, preferences: Partial<UserPreferences>) => {
  const { data, error } = await supabase
    .from('user_preferences')
    .update({
      ...preferences,
      updated_at: new Date().toISOString()
    })
    .eq('user_id', userId)
    .select()
    .single()

  return { data, error }
}

// Note: User stats are now calculated from Supabase Storage files
// in the backend API endpoints, eliminating the need for a separate table
