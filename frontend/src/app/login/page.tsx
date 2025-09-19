'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Mail, Lock, Eye, EyeOff, AlertCircle, CheckCircle, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  
  const { signIn, signUp, user } = useAuth()
  const router = useRouter()

  // Redirect if already authenticated
  useEffect(() => {
    if (user) {
      router.push('/')
    }
  }, [user, router])

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
          setError(error instanceof Error ? error.message : 'Sign up failed')
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
          setError(error instanceof Error ? error.message : 'Sign in failed')
        } else {
          setSuccess('Successfully signed in!')
          setTimeout(() => {
            router.push('/')
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
    setMode(newMode)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-[hsl(var(--tiktok-red))]/10 to-[hsl(var(--tiktok-blue))]/10 flex items-center justify-center p-4">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[hsl(var(--tiktok-red))]/30 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[hsl(var(--tiktok-blue))]/30 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8" style={{ userSelect: 'none' }}>
          <div className="flex items-center justify-center mb-4">
            <img src="/favicon.ico" alt="PIIPal" className="w-16 h-16" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            <span className="bg-gradient-to-r from-[hsl(var(--tiktok-red))] to-pink-500 bg-clip-text text-transparent">
              PIIPal
            </span>
          </h1>
          <p className="text-gray-400 text-lg mb-2">AI-Powered Content Privacy</p>
          <p className="text-gray-500 text-sm select-text" style={{ userSelect: 'text' }}>
            Automatically detect and blur personally identifiable information
          </p>
        </div>


        {/* Auth Card */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          {/* Mode Toggle */}
          <div className="flex bg-black/20 rounded-lg p-1 mb-6">
            <button
              onClick={() => handleModeChange('login')}
              className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                mode === 'login'
                  ? 'bg-[hsl(var(--tiktok-red))] text-white shadow-lg'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => handleModeChange('signup')}
              className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                mode === 'signup'
                  ? 'bg-[hsl(var(--tiktok-red))] text-white shadow-lg'
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
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg pl-12 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
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
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-black/20 border border-white/10 rounded-lg pl-12 pr-12 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
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
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full bg-black/20 border border-white/10 rounded-lg pl-12 pr-12 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
                    placeholder="Confirm your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
                <p className="text-green-300 text-sm">{success}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-[hsl(var(--tiktok-red))] to-pink-500 hover:from-[hsl(var(--tiktok-red))]/90 hover:to-pink-500/90 disabled:from-gray-600 disabled:to-gray-600 text-white py-3 px-4 rounded-lg font-medium transition-all duration-200 hover:shadow-lg hover:shadow-[hsl(var(--tiktok-red))]/25 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="text-white" />
                  <span>{mode === 'login' ? 'Signing In...' : 'Creating Account...'}</span>
                </>
              ) : (
                <>
                  <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
                  <Sparkles className="h-4 w-4" />
                </>
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

        {/* Bottom Text */}
        <div className="text-center mt-8">
          <p className="text-gray-500 text-xs">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  )
}
