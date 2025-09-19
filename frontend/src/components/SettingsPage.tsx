'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useUserData } from '@/hooks/useUserData'
import { User, Mail, Calendar, Settings as SettingsIcon, Save, CheckCircle, AlertCircle, LogOut, Trash2 } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import { supabase } from '@/lib/supabase'

export default function SettingsPage() {
  const { user, signOut } = useAuth()
  const { profile, preferences, loading, updateProfile, updatePreferences } = useUserData()
  
  // Form states
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [autoProcess, setAutoProcess] = useState(true)
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [language, setLanguage] = useState('en')
  
  // UI states
  const [isSaving, setIsSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Load user data when component mounts
  useEffect(() => {
    if (user) {
      setEmail(user.email || '')
    }
    if (profile) {
      setDisplayName(profile.display_name || '')
    }
    if (preferences) {
      setAutoProcess(preferences.auto_process)
      setEmailNotifications(preferences.email_notifications)
      setTheme(preferences.theme)
      setLanguage(preferences.language)
    }
  }, [user, profile, preferences])

  const handleSaveProfile = async () => {
    if (!user) return
    
    setIsSaving(true)
    setErrorMessage('')
    setSuccessMessage('')
    
    try {
      const result = await updateProfile({
        display_name: displayName || undefined
      })
      
      if (result?.error) {
        setErrorMessage('Failed to update profile')
      } else {
        setSuccessMessage('Profile updated successfully')
      }
    } catch {
      setErrorMessage('Failed to update profile')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSavePreferences = async () => {
    if (!user) return
    
    setIsSaving(true)
    setErrorMessage('')
    setSuccessMessage('')
    
    try {
      const result = await updatePreferences({
        auto_process: autoProcess,
        email_notifications: emailNotifications,
        theme,
        language
      })
      
      if (result?.error) {
        setErrorMessage('Failed to update preferences')
      } else {
        setSuccessMessage('Preferences updated successfully')
      }
    } catch {
      setErrorMessage('Failed to update preferences')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSignOut = async () => {
    await signOut()
  }

  const handleDeleteAccount = async () => {
    if (!user) return
    
    setIsDeleting(true)
    setErrorMessage('')
    
    try {
      // Clean up user data through our backend API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/user/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to clean up user data')
      }
      
      // Sign out the user
      await signOut()
      
      // Show success message
      setSuccessMessage('Account data deleted successfully. You have been signed out.')
      
    } catch (error) {
      console.error('Error deleting account:', error)
      setErrorMessage('Failed to delete account data. Please try again or contact support.')
    } finally {
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-400">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <SettingsIcon className="h-8 w-8 text-[hsl(var(--tiktok-red))]" />
          <h1 className="text-3xl font-bold text-white">Settings</h1>
        </div>
        <p className="text-gray-400">Manage your account preferences and profile information</p>
      </div>

      {/* Content */}
      <div className="space-y-8">
        {/* Success/Error Messages */}
        {successMessage && (
          <div className="bg-[hsl(var(--tiktok-blue))]/10 border border-[hsl(var(--tiktok-blue))]/20 rounded-lg p-4 flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-[hsl(var(--tiktok-blue))] flex-shrink-0" />
            <p className="text-[hsl(var(--tiktok-blue))]">{successMessage}</p>
          </div>
        )}
        
        {errorMessage && (
          <div className="bg-[hsl(var(--tiktok-red))]/10 border border-[hsl(var(--tiktok-red))]/20 rounded-lg p-4 flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-[hsl(var(--tiktok-red))] flex-shrink-0" />
            <p className="text-[hsl(var(--tiktok-red))]">{errorMessage}</p>
          </div>
        )}

        {/* Profile Section */}
        <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <User className="h-6 w-6 text-[hsl(var(--tiktok-red))]" />
              <h3 className="text-xl font-semibold text-white">Profile Information</h3>
            </div>
            <button
              onClick={handleSaveProfile}
              disabled={isSaving}
              className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 hover-lift disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSaving ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>Save Profile</span>
                </>
              )}
            </button>
          </div>
          
          <div className="space-y-6">
            {/* Display Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your display name"
                className="w-full px-4 py-3 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[hsl(var(--tiktok-red))] focus:border-transparent transition-all duration-200"
              />
            </div>

            {/* Email (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  readOnly
                  className="w-full pl-12 pr-4 py-3 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-gray-400 cursor-not-allowed"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
            </div>

            {/* Account Created Date */}
            {profile?.created_at && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Member Since
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={new Date(profile.created_at).toLocaleDateString()}
                    readOnly
                    className="w-full pl-12 pr-4 py-3 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-gray-400 cursor-not-allowed"
                  />
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Preferences Section */}
        <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <SettingsIcon className="h-6 w-6 text-[hsl(var(--tiktok-red))]" />
              <h3 className="text-xl font-semibold text-white">Preferences</h3>
            </div>
            <button
              onClick={handleSavePreferences}
              disabled={isSaving}
              className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 hover-lift disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSaving ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>Save Preferences</span>
                </>
              )}
            </button>
          </div>
          
          <div className="space-y-6">
            {/* Auto Process */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">
                  Auto Process Files
                </label>
                <p className="text-xs text-gray-500">Automatically process uploaded files</p>
              </div>
              <button
                onClick={() => setAutoProcess(!autoProcess)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  autoProcess ? 'bg-[hsl(var(--tiktok-red))]' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    autoProcess ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Email Notifications */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">
                  Email Notifications
                </label>
                <p className="text-xs text-gray-500">Receive email updates about processing</p>
              </div>
              <button
                onClick={() => setEmailNotifications(!emailNotifications)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  emailNotifications ? 'bg-[hsl(var(--tiktok-red))]' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    emailNotifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Theme */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Theme
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as 'dark' | 'light')}
                className="w-full px-4 py-3 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[hsl(var(--tiktok-red))] focus:border-transparent transition-all duration-200"
                style={{ colorScheme: 'dark' }}
              >
                <option value="dark" className="bg-[hsl(var(--card-background))] text-white">Dark</option>
                <option value="light" className="bg-[hsl(var(--card-background))] text-white">Light</option>
              </select>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-3 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[hsl(var(--tiktok-red))] focus:border-transparent transition-all duration-200"
                style={{ colorScheme: 'dark' }}
              >
                <option value="en" className="bg-[hsl(var(--card-background))] text-white">English</option>
                <option value="es" className="bg-[hsl(var(--card-background))] text-white">Spanish</option>
                <option value="fr" className="bg-[hsl(var(--card-background))] text-white">French</option>
                <option value="de" className="bg-[hsl(var(--card-background))] text-white">German</option>
              </select>
            </div>

          </div>
        </div>

        {/* Account Actions */}
        <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6">
          <div className="flex items-center space-x-3 mb-6">
            <LogOut className="h-6 w-6 text-[hsl(var(--tiktok-red))]" />
            <h3 className="text-xl font-semibold text-white">Account Actions</h3>
          </div>
          
          <div className="space-y-4">
            <button
              onClick={handleSignOut}
              className="w-full bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 hover-lift"
            >
              Sign Out
            </button>
            
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="w-full bg-red-600 hover:bg-red-700 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 hover-lift flex items-center justify-center space-x-2"
            >
              <Trash2 className="h-4 w-4" />
              <span>Delete Account</span>
            </button>
          </div>
        </div>
      </div>

      {/* Delete Account Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <Trash2 className="h-6 w-6 text-red-500" />
              <h3 className="text-xl font-semibold text-white">Delete Account</h3>
            </div>
            
            <p className="text-gray-300 mb-6">
              Are you sure you want to delete your account? This action cannot be undone. 
              All your data, including processed files and preferences, will be permanently removed.
              You will be signed out after deletion.
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={isDeleting}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isDeleting ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    <span>Delete</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
