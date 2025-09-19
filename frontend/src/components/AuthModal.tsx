'use client'

import React, { useState } from 'react'
import { X, Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  mode: 'login' | 'signup'
  onModeChange: (mode: 'login' | 'signup') => void
}

export default function AuthModal({ isOpen, onClose, mode, onModeChange }: AuthModalProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { signIn, signUp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      if (mode === 'signup') {
        if (password !== confirmPassword) {
          setError('Passwords do not match')
          setLoading(false)
          return
        }
        if (password.length < 6) {
          setError('Password must be at least 6 characters')
          setLoading(false)
          return
        }
        
        const { data, error } = await signUp(email, password)
        if (error) {
          setError(error.message)
        } else {
          setSuccess('Check your email for verification link!')
          // Reset form
          setEmail('')
          setPassword('')
          setConfirmPassword('')
        }
      } else {
        const { data, error } = await signIn(email, password)
        if (error) {
          setError(error.message)
        } else {
          setSuccess('Successfully signed in!')
          setTimeout(() => {
            onClose()
          }, 1000)
        }
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setError('')
    setSuccess('')
  }

  const handleModeChange = (newMode: 'login' | 'signup') => {
    resetForm()
    onModeChange(newMode)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[hsl(var(--card-background))] border border-[hsl(var(--border-color))] rounded-xl p-6 w-full max-w-md relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-gray-400">
            {mode === 'login' 
              ? 'Sign in to your PIIPal account' 
              : 'Join PIIPal to protect your content'
            }
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="flex bg-[hsl(var(--interaction-bg))] rounded-lg p-1 mb-6">
          <button
            onClick={() => handleModeChange('login')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
              mode === 'login'
                ? 'bg-[hsl(var(--tiktok-red))] text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => handleModeChange('signup')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
              mode === 'signup'
                ? 'bg-[hsl(var(--tiktok-red))] text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
                placeholder="Enter your email"
                required
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg pl-10 pr-12 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Confirm Password Field (Signup only) */}
          {mode === 'signup' && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg pl-10 pr-12 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
                  placeholder="Confirm your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-3 flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-900/20 border border-green-700 rounded-lg p-3 flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
              <p className="text-green-300 text-sm">{success}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 disabled:bg-gray-600 text-white py-3 px-4 rounded-lg font-medium transition-all duration-200 hover-lift hover-glow disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>{mode === 'login' ? 'Signing In...' : 'Creating Account...'}</span>
              </div>
            ) : (
              mode === 'login' ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-gray-400 text-sm">
            {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => handleModeChange(mode === 'login' ? 'signup' : 'login')}
              className="text-[hsl(var(--tiktok-red))] hover:text-[hsl(var(--tiktok-red))]/80 font-medium transition-colors"
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
