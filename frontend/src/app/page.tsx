'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Upload, Video, Image, Download, Loader2, CheckCircle, AlertCircle, HomeIcon, Search, ChevronRight, Play, Pause, Volume2, VolumeX, Plus, Trash2 } from 'lucide-react';
import Link from 'next/link';

interface ProcessingResult {
  message: string;
  output_file: string;
  download_url: string;
}

interface FileInfo {
  filename: string;
  size: number;
  download_url: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<'video' | 'image'>('video');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [processedFiles, setProcessedFiles] = useState<FileInfo[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [showControls, setShowControls] = useState(false);
  const [selectedCensoredFile, setSelectedCensoredFile] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const originalVideoRef = useRef<HTMLVideoElement>(null);
  const censoredVideoRef = useRef<HTMLVideoElement>(null);

  // Memoize the video URL to prevent recreation on every render
  const videoUrl = useMemo(() => {
    return file ? URL.createObjectURL(file) : null;
  }, [file]);

  // Cleanup video URL when component unmounts or file changes
  useEffect(() => {
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  }, [videoUrl]);

  const API_BASE_URL = 'http://localhost:8000';

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
      
      // Determine file type
      const isVideo = selectedFile.type.startsWith('video/');
      const isImage = selectedFile.type.startsWith('image/');
      
      if (isVideo) {
        setFileType('video');
        setIsPlaying(true); // Auto-play videos
      } else if (isImage) {
        setFileType('image');
      } else {
        setError('Please select a valid video or image file');
        setFile(null);
      }
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
      setResult(null);
      
      const isVideo = droppedFile.type.startsWith('video/');
      const isImage = droppedFile.type.startsWith('image/');
      
      if (isVideo) {
        setFileType('video');
      } else if (isImage) {
        setFileType('image');
      } else {
        setError('Please select a valid video or image file');
        setFile(null);
      }
    }
  }, []);

  const handleVideoMouseEnter = useCallback(() => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
      controlsTimeoutRef.current = null;
    }
  }, []);

  const handleVideoMouseLeave = useCallback(() => {
    // Only hide controls if mouse leaves the entire video container area
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      setShowControls(false);
    }, 0);
  }, []);

  const handleControlsMouseEnter = useCallback(() => {
    // Keep controls visible when hovering over controls
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
      controlsTimeoutRef.current = null;
    }
  }, []);

  const handleControlsMouseLeave = useCallback(() => {
    // Only hide controls when leaving the entire video area
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      setShowControls(false);
    }, 0);
  }, []);

  const fetchProcessedFiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files`);
      if (response.ok) {
        const data = await response.json();
        
        // Merge with existing localStorage data to maintain persistence
        const existingFiles = localStorage.getItem('recentFiles');
        if (existingFiles) {
          try {
            const parsedExisting = JSON.parse(existingFiles);
            const mergedFiles = [...parsedExisting, ...data.files];
            // Remove duplicates based on filename
            const uniqueFiles = mergedFiles.filter((file, index, self) => 
              index === self.findIndex(f => f.filename === file.filename)
            );
            setProcessedFiles(uniqueFiles);
          } catch (error) {
            setProcessedFiles(data.files);
          }
        } else {
          setProcessedFiles(data.files);
        }
      }
    } catch (error) {
      console.error('Failed to fetch processed files:', error);
      // Fallback to localStorage if backend is unavailable
      const savedFiles = localStorage.getItem('recentFiles');
      if (savedFiles) {
        try {
          const parsedFiles = JSON.parse(savedFiles);
          setProcessedFiles(parsedFiles);
        } catch (error) {
          console.error('Error loading saved files:', error);
        }
      }
    }
  }, []);

  const addToRecentFiles = useCallback((newFile: FileInfo) => {
    setProcessedFiles(prev => {
      const updated = [newFile, ...prev.filter(f => f.filename !== newFile.filename)];
      return updated.slice(0, 20); // Keep only last 20 files
    });
  }, []);

  const processFile = useCallback(async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Use single endpoint for both video and image processing
      const response = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process file');
      }

      const resultData = await response.json();
      setResult(resultData);
      
      // Add to recent files
      const newFile: FileInfo = {
        filename: resultData.output_file,
        size: 0, // We don't have size info from the response, will be updated when fetched
        download_url: resultData.download_url
      };
      addToRecentFiles(newFile);
      
      // Refresh the list of processed files from backend
      fetchProcessedFiles();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsProcessing(false);
    }
  }, [file, fetchProcessedFiles, addToRecentFiles]);

  const downloadFile = useCallback(async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/download/${filename}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to download file');
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    if (fileType === 'video' && videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [fileType, isPlaying]);

  const toggleMute = useCallback(() => {
    if (fileType === 'video' && videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [fileType, isMuted]);

  const handleProgressBarClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!videoRef.current) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickPercentage = clickX / rect.width;
    const videoDuration = videoRef.current.duration;
    const seekTime = clickPercentage * videoDuration;

    videoRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  }, []);

  const formatTime = useCallback((seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}:${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
  }, []);

  // Update current time for progress bar with more frequent updates
  useEffect(() => {
    if (videoRef.current && fileType === 'video') {
      const handleTimeUpdate = () => {
        if (videoRef.current) {
          setCurrentTime(videoRef.current.currentTime);
        }
      };
      
      // Add timeupdate event listener
      videoRef.current.addEventListener('timeupdate', handleTimeUpdate);
      
      // Also add a more frequent update interval for smoother progress bar
      const interval = setInterval(() => {
        if (videoRef.current) {
          setCurrentTime(videoRef.current.currentTime);
        }
      }, 50); // Update every 50ms for very smooth progress bar
      
      return () => {
        if (videoRef.current) {
          videoRef.current.removeEventListener('timeupdate', handleTimeUpdate);
        }
        clearInterval(interval);
      };
    }
  }, [fileType, file]); // Add file dependency to ensure proper cleanup and re-initialization

  // Reset current time when file changes
  useEffect(() => {
    setCurrentTime(0);
  }, [file]);

  // Auto-restart video when it ends (infinite loop like reels)
  useEffect(() => {
    if (videoRef.current && fileType === 'video') {
      const handleVideoEnd = () => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
          videoRef.current.play();
        }
      };
      
      videoRef.current.addEventListener('ended', handleVideoEnd);
      return () => {
        if (videoRef.current) {
          videoRef.current.removeEventListener('ended', handleVideoEnd);
        }
      };
    }
  }, [fileType]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  // Fetch processed files on component mount and load from localStorage
  useEffect(() => {
    fetchProcessedFiles();
    
    // Load recent files from localStorage
    const savedFiles = localStorage.getItem('recentFiles');
    if (savedFiles) {
      try {
        const parsedFiles = JSON.parse(savedFiles);
        setProcessedFiles(parsedFiles);
      } catch (error) {
        console.error('Error loading saved files:', error);
      }
    }
  }, [fetchProcessedFiles]);

  // Save files to localStorage whenever they change
  useEffect(() => {
    if (processedFiles.length > 0) {
      localStorage.setItem('recentFiles', JSON.stringify(processedFiles));
    }
  }, [processedFiles]);

  // Memoized video component to prevent unnecessary re-renders
  const VideoPlayer = useMemo(() => (
    <div className="relative" onMouseEnter={handleVideoMouseEnter} onMouseLeave={handleVideoMouseLeave}>
      <video
        key={videoUrl}
        ref={videoRef}
        src={videoUrl || undefined}
        className="w-full h-auto max-h-[40vh] max-w-full object-contain cursor-pointer"
        autoPlay
        loop
        muted={isMuted}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={() => {
          if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
          }
        }}
        onClick={togglePlayPause}
      />
    </div>
  ), [file, fileType, videoUrl, isMuted, isPlaying, handleVideoMouseEnter, handleVideoMouseLeave, togglePlayPause]);

  // Separate VideoControls component that can update independently
  const VideoControls = useMemo(() => {
    if (!file || fileType !== 'video') return null;
    
    return (
      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-all duration-200 ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
        onMouseEnter={handleControlsMouseEnter}
        onMouseLeave={handleControlsMouseLeave}
      >
        {/* Progress Bar */}
        <div className="mb-3">
          <div 
            className="w-full h-2 bg-white/30 rounded-full cursor-pointer relative"
            onClick={handleProgressBarClick}
          >
            <div 
              className="h-full bg-[hsl(var(--tiktok-red))] rounded-full transition-all duration-100"
              style={{ width: `${(currentTime / (videoRef.current?.duration || 1)) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-white text-xs mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(videoRef.current?.duration || 0)}</span>
          </div>
        </div>
        
        {/* Control Buttons */}
        <div className="flex items-center justify-center space-x-4">
          <button
            onClick={togglePlayPause}
            className="bg-white/20 hover:bg-white/30 text-white p-2 rounded-full transition-all duration-200 hover-lift"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </button>
          
          <button
            onClick={toggleMute}
            className="bg-white/20 hover:bg-white/30 text-white p-2 rounded-full transition-all duration-200 hover-lift"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </button>
        </div>
      </div>
    );
  }, [file, fileType, showControls, currentTime, isPlaying, isMuted, handleProgressBarClick, formatTime, togglePlayPause, toggleMute, handleControlsMouseEnter, handleControlsMouseLeave]);

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-white flex overflow-x-hidden">
      {/* Left Sidebar */}
      <div className="fixed left-0 top-0 h-full w-64 bg-[hsl(var(--sidebar-bg))] border-r border-[hsl(var(--border-color))] p-6 pt-8 overflow-y-auto">
        {/* Logo and Title */}
        <div className="mb-8">
          <Link href="/" className="flex items-center space-x-3 group">
            <img src="/favicon.ico" alt="PII Pal" className="w-8 h-8" />
            <div>
              <h2 className="text-xl font-bold text-white group-hover:text-[hsl(var(--tiktok-red))] transition-all duration-200">
                PII Pal
              </h2>
              <p className="text-sm text-gray-400">AI Reels Moderation Tool</p>
            </div>
          </Link>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search processed files..."
              className="w-full bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200"
            />
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="space-y-2">
          <Link href="/" className="flex items-center space-x-3 p-3 rounded-lg bg-[hsl(var(--tiktok-red))]/10 text-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/20 transition-all duration-200 hover-lift" onClick={() => setFile(null)}>
            <HomeIcon className="h-5 w-5" />
            <span>Home</span>
          </Link>
          <Link href="/explore" className="flex items-center space-x-3 p-3 rounded-lg text-gray-300 hover:bg-[hsl(var(--hover-bg))] hover:text-white transition-all duration-200 hover-lift">
            <Search className="h-5 w-5" />
            <span>Explore</span>
            <ChevronRight className="h-4 w-4 ml-auto" />
          </Link>
        </nav>

        {/* Footer */}
        <div className="absolute bottom-6 left-6 right-6">
          <div className="text-xs text-gray-500 space-y-2">
            <p>© 2025 CatGPT TechJam 2025</p>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 ml-64 overflow-y-auto">
        <div className="p-6 pt-8 max-w-full">
          {/* Top Bar */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                <span className="gradient-text">PII Agent</span>
              </h1>
              <p className="text-gray-400">
                Automatically detects and blurs personally identifiable information in your content.
              </p>
            </div>
            <div className="flex space-x-4">
              <a 
                href="https://devpost.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-4 py-2 text-gray-300 hover:text-white transition-all duration-200 hover:bg-[hsl(var(--hover-bg))] rounded-lg"
              >
                DevPost
              </a>
              <a 
                href="https://github.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-4 py-2 text-gray-300 hover:text-white transition-all duration-200 hover:bg-[hsl(var(--hover-bg))] rounded-lg"
              >
                GitHub
              </a>
              <a 
                href="#demo" 
                className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 text-white px-6 py-2 rounded-lg font-medium transition-all duration-200 hover-lift hover-glow"
              >
                Demo
              </a>
            </div>
          </div>

          {/* Upload Content Section - Only show when no file is selected */}
          {!file && (
            <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 hover-glow transition-all duration-200 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-white text-center">
                <span className="gradient-text">Upload Content</span>
              </h2>
              
              <div className="max-w-2xl mx-auto">
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
                    dragActive
                      ? 'border-[hsl(var(--tiktok-red))] bg-[hsl(var(--tiktok-red))]/10' 
                      : 'border-[hsl(var(--border-color))] hover:border-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--border-color))]/10'
                  }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                >
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg text-white mb-2">Drop your file here</p>
                  <p className="text-gray-400 mb-4">or</p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 text-white py-2 px-6 rounded-lg font-medium transition-all duration-200 hover-lift hover-glow"
                  >
                    Browse Files
                  </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*,image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
                </div>
                  </div>
                </div>
              )}

          {/* File Preview and Processing - Show when file is selected */}
          {file && (
            <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 hover-glow transition-all duration-200 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-white text-center">
                <span className="gradient-text">
                  {result ? 'Processing Complete' : 'File Preview'}
                </span>
              </h2>
              
              <div className="max-w-6xl mx-auto">
                {/* Video/Image Preview - Only show when not yet processed */}
                {!result && (
                  <div className="relative bg-[hsl(var(--interaction-bg))] rounded-lg overflow-hidden mb-6" onMouseEnter={handleVideoMouseEnter} onMouseLeave={handleVideoMouseLeave}>
                    {fileType === 'video' ? (
                      <>
                        {VideoPlayer}
                        {VideoControls}
                        {/* Close Button - Top Right of Video */}
                        <button
                          onClick={() => setFile(null)}
                          className="absolute top-3 right-3 text-white hover:text-[hsl(var(--tiktok-red))] hover:bg-black/50 bg-black/30 p-2 rounded-full transition-all duration-200 hover-lift z-10"
                          title="Close preview and return to upload"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </>
                    ) : (
                      <>
                        <img
                          src={URL.createObjectURL(file)}
                          alt="Preview"
                          className="w-full h-auto max-h-[40vh] max-w-full object-contain"
                        />
                        {/* Close Button - Top Right of Image */}
                        <button
                          onClick={() => setFile(null)}
                          className="absolute top-3 right-3 text-white hover:text-[hsl(var(--tiktok-red))] hover:bg-black/50 bg-black/30 p-2 rounded-full transition-all duration-200 hover-lift z-10"
                          title="Close preview and return to upload"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Processing Options - Show when not yet processed */}
                {!result && (
                  <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-4 hover-glow transition-all duration-200">
                    <h3 className="text-lg font-semibold mb-3 text-white text-center">
                      <span className="gradient-text">PiiPal is Ready!</span>
                    </h3>
                    
                    <p className="text-gray-400 text-center mb-4">
                      Files are automatically processed using YOLOE detection and pixelation censoring.
                    </p>
                    
                    <div className="text-center">
              <button
                onClick={processFile}
                disabled={isProcessing}
                        className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 disabled:bg-gray-600 text-white py-3 px-8 rounded-lg font-medium transition-all duration-200 hover-lift hover-glow disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Processing...</span>
                          </div>
                ) : (
                          'Censor'
                )}
              </button>
                    </div>
            </div>
          )}

                {/* Processing Complete - Show when processing is done */}
          {result && (
                  <>
                    {/* Side by Side Comparison */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                      {/* Original File */}
                      <div>
                        <h4 className="text-white font-medium mb-3 text-center">Original</h4>
                        <div className="relative bg-[hsl(var(--interaction-bg))] rounded-lg overflow-hidden" onMouseEnter={() => setShowControls(true)} onMouseLeave={() => setShowControls(false)}>
                          {fileType === 'video' ? (
                            <>
                              <video
                                ref={originalVideoRef}
                                src={file ? URL.createObjectURL(file) : undefined}
                                className="w-full h-auto max-h-[40vh] max-w-full object-contain cursor-pointer"
                                autoPlay
                                loop
                                muted
                                onTimeUpdate={() => {
                                  if (originalVideoRef.current && censoredVideoRef.current) {
                                    censoredVideoRef.current.currentTime = originalVideoRef.current.currentTime;
                                  }
                                }}
                                onClick={(e) => {
                                  const video = e.currentTarget;
                                  if (video.paused) {
                                    video.play();
                                  } else {
                                    video.pause();
                                  }
                                }}
                              />
                              {/* Play/Pause Indicator */}
                              {showControls && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity duration-200">
                                  <div className="bg-black/50 rounded-full p-3">
                                    <Play className="h-6 w-6 text-white" />
                                  </div>
                                </div>
                              )}
                            </>
                          ) : (
                            <img
                              src={file ? URL.createObjectURL(file) : undefined}
                              alt="Original"
                              className="w-full h-auto max-h-[40vh] max-w-full object-contain"
                            />
                          )}
                        </div>
                      </div>
                      
                      {/* Censored File */}
                <div>
                        <h4 className="text-white font-medium mb-3 text-center">Censored</h4>
                        <div className="relative bg-[hsl(var(--interaction-bg))] rounded-lg overflow-hidden" onMouseEnter={() => setShowControls(true)} onMouseLeave={() => setShowControls(false)}>
                          {fileType === 'video' ? (
                            <>
                              <video
                                ref={censoredVideoRef}
                                src={`${API_BASE_URL}/download/${result.output_file}`}
                                className="w-full h-auto max-h-[40vh] max-w-full object-contain cursor-pointer"
                                autoPlay
                                loop
                                muted
                                onTimeUpdate={() => {
                                  if (censoredVideoRef.current && originalVideoRef.current) {
                                    originalVideoRef.current.currentTime = censoredVideoRef.current.currentTime;
                                  }
                                }}
                                onClick={(e) => {
                                  const video = e.currentTarget;
                                  if (video.paused) {
                                    video.play();
                                  } else {
                                    video.pause();
                                  }
                                }}
                              />
                              {/* Play/Pause Indicator */}
                              {showControls && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity duration-200">
                                  <div className="bg-black/50 rounded-full p-3">
                                    <Play className="h-6 w-6 text-white" />
                                  </div>
                                </div>
                              )}
                            </>
                          ) : (
                            <img
                              src={`${API_BASE_URL}/download/${result.output_file}`}
                              alt="Censored"
                              className="w-full h-auto max-h-[40vh] max-w-full object-contain"
                            />
                          )}
                        </div>
                </div>
              </div>

                    {/* Success Message */}
                    <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 flex items-center space-x-3 mb-6">
                      <CheckCircle className="h-6 w-6 text-green-400" />
                      <div>
                        <p className="font-medium text-green-300">{result.message}</p>
                        <p className="text-green-400 text-sm">Output: {result.output_file}</p>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center justify-center space-x-4">
              <button
                onClick={() => downloadFile(result.output_file)}
                        className="bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-2 hover-lift hover-glow"
              >
                <Download className="h-4 w-4" />
                <span>Download Processed File</span>
              </button>
                      
                      <button
                        onClick={() => {
                          setFile(null);
                          setResult(null);
                          setError(null);
                        }}
                        className="bg-[hsl(var(--tiktok-blue))] hover:bg-[hsl(var(--tiktok-blue))]/90 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-2 hover-lift hover-glow"
                      >
                        <Plus className="h-4 w-4" />
                        <span>New File</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-6 w-6" />
                <p className="text-red-300">{error}</p>
              </div>
            </div>
          )}

          {/* Recent Files - Always show */}
          {processedFiles.length > 0 && (
            <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 hover-glow transition-all duration-200">
              <h3 className="text-lg font-semibold mb-4 text-white text-center">
                <span className="gradient-text">Recent Files</span>
              </h3>
              
              <div className="max-w-4xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {processedFiles.slice(0, 6).map((fileInfo, index) => {
                    const isVideo = fileInfo.filename.toLowerCase().includes('.mp4') || 
                                   fileInfo.filename.toLowerCase().includes('.avi') || 
                                   fileInfo.filename.toLowerCase().includes('.mov');
                    const isImage = fileInfo.filename.toLowerCase().includes('.jpg') || 
                                  fileInfo.filename.toLowerCase().includes('.jpeg') || 
                                  fileInfo.filename.toLowerCase().includes('.png');
                    
                    return (
                  <div
                    key={index}
                        className="border border-[hsl(var(--border-color))] rounded-lg bg-[hsl(var(--interaction-bg))] hover:bg-[hsl(var(--hover-bg))] transition-all duration-200 hover-lift cursor-pointer overflow-hidden"
                        onClick={() => setSelectedCensoredFile(selectedCensoredFile === fileInfo.filename ? null : fileInfo.filename)}
                      >
                        {/* File Preview */}
                        <div className="relative aspect-video bg-[hsl(var(--interaction-bg))] overflow-hidden">
                          {isVideo ? (
                            <video
                              className="w-full h-full object-cover"
                              src={`${API_BASE_URL}/download/${fileInfo.filename}`}
                              muted
                              loop
                              preload="metadata"
                            />
                          ) : isImage ? (
                            <img
                              src={`${API_BASE_URL}/download/${fileInfo.filename}`}
                              alt="File Preview"
                              className="w-full h-full object-cover"
                              loading="lazy"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Download className="h-8 w-8 text-gray-400" />
                            </div>
                          )}
                        </div>
                        
                        {/* File Info */}
                        <div className="p-3">
                          <p className="font-medium text-white text-sm truncate mb-1">{fileInfo.filename}</p>
                          <p className="text-gray-400 text-xs mb-2">
                        {(fileInfo.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                              {isVideo ? 'VIDEO' : isImage ? 'IMAGE' : 'FILE'}
                            </span>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  // Remove file from processed files
                                  setProcessedFiles(prev => prev.filter(f => f.filename !== fileInfo.filename));
                                  // Remove from localStorage
                                  const savedFiles = localStorage.getItem('recentFiles');
                                  if (savedFiles) {
                                    try {
                                      const parsedFiles = JSON.parse(savedFiles);
                                      const updatedFiles = parsedFiles.filter((f: FileInfo) => f.filename !== fileInfo.filename);
                                      localStorage.setItem('recentFiles', JSON.stringify(updatedFiles));
                                    } catch (error) {
                                      console.error('Error updating localStorage:', error);
                                    }
                                  }
                                }}
                                className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg text-xs font-medium transition-all duration-200 hover-lift hover-glow flex-shrink-0"
                                title="Delete from history"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  downloadFile(fileInfo.filename);
                                }}
                                className="bg-[hsl(var(--tiktok-blue))] hover:bg-[hsl(var(--tiktok-blue))]/90 text-white p-2 rounded-lg text-xs font-medium transition-all duration-200 hover-lift hover-glow flex-shrink-0"
                                title="Download file"
                              >
                                <Download className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* Selected File Full Preview */}
                {selectedCensoredFile && (
                  <div className="mt-6 bg-[hsl(var(--interaction-bg))] rounded-lg border border-[hsl(var(--border-color))] p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-white font-medium">Preview: {selectedCensoredFile}</h4>
                      <button
                        onClick={() => setSelectedCensoredFile(null)}
                        className="text-gray-400 hover:text-white hover:bg-[hsl(var(--hover-bg))] p-2 rounded-lg transition-all duration-200"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="relative bg-black rounded-lg overflow-hidden">
                      {selectedCensoredFile.toLowerCase().includes('.mp4') || 
                       selectedCensoredFile.toLowerCase().includes('.avi') || 
                       selectedCensoredFile.toLowerCase().includes('.mov') ? (
                        <video
                          className="w-full h-auto max-h-[50vh] max-w-full object-contain cursor-pointer"
                          src={`${API_BASE_URL}/download/${selectedCensoredFile}`}
                          autoPlay
                          loop
                          muted
                          preload="metadata"
                          onClick={(e) => {
                            const video = e.currentTarget;
                            if (video.paused) {
                              video.play();
                            } else {
                              video.pause();
                            }
                          }}
                        />
                      ) : (
                        <img
                          src={`${API_BASE_URL}/download/${selectedCensoredFile}`}
                          alt="File Preview"
                          className="w-full h-auto max-h-[50vh] max-w-full object-contain"
                          loading="lazy"
                        />
                      )}
                    </div>
                  </div>
                )}
                
                {processedFiles.length > 6 && (
                  <div className="mt-4 text-center">
                    <Link 
                      href="/explore" 
                      className="text-[hsl(var(--tiktok-red))] hover:text-[hsl(var(--tiktok-red))]/80 font-medium transition-all duration-200 hover:underline text-sm"
                    >
                      View All Files →
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
