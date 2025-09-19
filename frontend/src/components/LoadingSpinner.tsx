'use client'

import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export default function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6', 
    lg: 'h-12 w-12'
  }

  return (
    <div className={`animate-spin rounded-full border-b-2 border-[hsl(var(--tiktok-red))] ${sizeClasses[size]} ${className}`}></div>
  )
}
