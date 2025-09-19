'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { createUserProfile, createUserPreferences, getUserProfile } from '@/lib/supabase-database'
// Note: session-storage removed - auth state managed by Supabase

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (email: string, password: string) => Promise<{ data: any; error: any }>
  signIn: (email: string, password: string) => Promise<{ data: any; error: any }>
  signOut: () => Promise<{ error: any }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  // Note: Auth state persistence removed - managed by Supabase

  useEffect(() => {
    let mounted = true

    // Get initial session
    const getInitialSession = async () => {
      try {
        console.log('🔍 Getting initial session...')
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('❌ Error getting session:', error)
        }
        
        console.log('📋 Session data:', session ? 'Found' : 'None')
        
        if (mounted) {
          setSession(session)
          setUser(session?.user ?? null)
          setLoading(false)
          console.log('✅ Loading set to false')
          
          // Initialize user data in background (don't block loading)
          if (session?.user) {
            initializeUserData(session.user)
          }
        }
      } catch (error) {
        console.error('❌ Error in getInitialSession:', error)
        if (mounted) {
          setLoading(false)
          console.log('✅ Loading set to false (error case)')
        }
      }
    }

    getInitialSession()

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('🔄 Auth state changed:', event, session?.user?.email)
      
      if (mounted) {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
        console.log('✅ Loading set to false (auth change)')
        
        // Initialize user data in background (don't block loading)
        if (session?.user) {
          initializeUserData(session.user)
        }
      }
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  const initializeUserData = async (user: User) => {
    try {
      // Check if user profile exists
      const { data: profile, error: profileError } = await getUserProfile(user.id)
      
      if (profileError && profileError.code === 'PGRST116') {
        // Profile doesn't exist, create it
        console.log('Creating user profile for:', user.email)
        await createUserProfile(user.id, user.email || '', user.user_metadata?.display_name)
        await createUserPreferences(user.id)
      }
    } catch (error) {
      console.error('Error initializing user data:', error)
      // Don't block the auth flow if profile creation fails
    }
  }

  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    return { data, error }
  }

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    // Clear local auth state on sign out
    // Note: Auth state clearing removed - managed by Supabase
    return { error }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
