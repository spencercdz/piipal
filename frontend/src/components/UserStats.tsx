'use client'

import React, { useState, useEffect } from 'react'
import { FileImage, Video, CheckCircle, XCircle, Calendar } from 'lucide-react'
import { apiService } from '@/lib/api'
import LoadingSpinner from '@/components/LoadingSpinner'

interface UserStats {
  total_files: number
  completed_files: number
  images_processed: number
  videos_processed: number
  this_month: number
}

export default function UserStats() {
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await apiService.getUserStats()
        if (response.data) {
          setStats(response.data)
        }
      } catch (error) {
        console.error('Error loading user stats:', error)
      } finally {
        setLoading(false)
      }
    }

    loadStats()
  }, [])

  if (loading) {
    return (
      <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6">
        <LoadingSpinner size="md" className="mx-auto mb-4" />
        <div className="h-6 bg-gray-700 rounded mb-4 animate-pulse"></div>
        <div className="grid grid-cols-2 gap-4">
          <div className="h-16 bg-gray-700 rounded animate-pulse"></div>
          <div className="h-16 bg-gray-700 rounded animate-pulse"></div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const successRate = stats.total_files > 0 
    ? Math.round((stats.completed_files / stats.total_files) * 100)
    : 0

  return (
    <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 hover-glow transition-all duration-200">
      <h3 className="text-lg font-semibold mb-4 text-white text-center">
        <span className="gradient-text">Your Stats</span>
      </h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Total Files */}
        <div className="bg-[hsl(var(--interaction-bg))] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white mb-1">{stats.total_files}</div>
          <div className="text-sm text-gray-400">Total Files</div>
        </div>

        {/* Success Rate */}
        <div className="bg-[hsl(var(--interaction-bg))] rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400 mb-1">{successRate}%</div>
          <div className="text-sm text-gray-400">Success Rate</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        {/* Images */}
        <div className="bg-[hsl(var(--interaction-bg))] rounded-lg p-3 text-center">
          <FileImage className="h-6 w-6 text-blue-400 mx-auto mb-1" />
          <div className="text-lg font-semibold text-white">{stats.images_processed}</div>
          <div className="text-xs text-gray-400">Images</div>
        </div>

        {/* Videos */}
        <div className="bg-[hsl(var(--interaction-bg))] rounded-lg p-3 text-center">
          <Video className="h-6 w-6 text-purple-400 mx-auto mb-1" />
          <div className="text-lg font-semibold text-white">{stats.videos_processed}</div>
          <div className="text-xs text-gray-400">Videos</div>
        </div>

        {/* This Month */}
        <div className="bg-[hsl(var(--interaction-bg))] rounded-lg p-3 text-center">
          <Calendar className="h-6 w-6 text-orange-400 mx-auto mb-1" />
          <div className="text-lg font-semibold text-white">{stats.this_month}</div>
          <div className="text-xs text-gray-400">This Month</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2 text-[hsl(var(--tiktok-blue))]">
          <CheckCircle className="h-4 w-4" />
          <span>{stats.completed_files} completed</span>
        </div>
        <div className="flex items-center space-x-2 text-[hsl(var(--tiktok-red))]">
          <XCircle className="h-4 w-4" />
          <span>{stats.total_files - stats.completed_files} failed</span>
        </div>
      </div>
    </div>
  )
}
