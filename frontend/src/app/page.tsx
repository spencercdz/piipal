'use client';

import { useState, useRef, useEffect } from 'react';
import { Upload, Video, Image, Download, Loader2, CheckCircle, AlertCircle, HomeIcon, Search, ChevronRight, Play, Pause, Volume2, VolumeX } from 'lucide-react';
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
  const [method, setMethod] = useState<string>('ocr');
  const [redactionMode, setRedactionMode] = useState<string>('pixelate');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processedFiles, setProcessedFiles] = useState<FileInfo[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const API_BASE_URL = 'http://localhost:8000';

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
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
        setMethod('ocr'); // Default for videos
        setIsPlaying(true); // Auto-play videos
      } else if (isImage) {
        setFileType('image');
        setMethod('yolo'); // Default for images
      } else {
        setError('Please select a valid video or image file');
        setFile(null);
      }
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragActive(false);
    
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
      setResult(null);
      
      const isVideo = droppedFile.type.startsWith('video/');
      const isImage = droppedFile.type.startsWith('image/');
      
      if (isVideo) {
        setFileType('video');
        setMethod('ocr');
        setIsPlaying(true); // Auto-play videos
      } else if (isImage) {
        setFileType('image');
        setMethod('yolo');
      } else {
        setError('Please select a valid video or image file');
        setFile(null);
      }
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault();
    setDragActive(false);
  };

  const processFile = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = fileType === 'video' ? '/process-video' : '/process-image';
      const params = new URLSearchParams();
      
      if (fileType === 'video') {
        params.append('method', method);
        params.append('redaction_mode', redactionMode);
      } else {
        params.append('method', method);
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}?${params.toString()}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process file');
      }

      const resultData = await response.json();
      setResult(resultData);
      
      // Refresh the list of processed files
      fetchProcessedFiles();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsProcessing(false);
    }
  };

  const fetchProcessedFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files`);
      if (response.ok) {
        const data = await response.json();
        setProcessedFiles(data.files);
      }
    } catch (error) {
      console.error('Failed to fetch processed files:', error);
    }
  };

  const downloadFile = async (filename: string) => {
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
  };

  const togglePlayPause = () => {
    if (fileType === 'video' && videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (fileType === 'video' && videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

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

  // Fetch processed files on component mount
  useEffect(() => {
    fetchProcessedFiles();
  }, []);

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-white flex">
      {/* Left Sidebar - Navigation */}
      <div className="w-64 bg-[hsl(var(--sidebar-bg))] border-r border-[hsl(var(--border-color))] p-6 fixed left-0 top-0 h-full">
        {/* Logo */}
        <div className="mb-8">
          <div className="flex items-center space-x-2 mb-2">
            <Link href="/" className="flex items-center space-x-1 group">
              <img src="/favicon.ico" alt="PII Pal" className="h-10 w-10 group-hover:scale-110 transition-transform duration-200" />
              <h1 className="text-2xl font-bold text-white group-hover:text-[hsl(var(--tiktok-red))] transition-colors duration-200 cursor-pointer">
                <span className="gradient-text">PII</span>Pal
              </h1>
            </Link>
          </div>
          <p className="text-sm text-gray-400">A Reels Moderation Tool.</p>
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
          <Link href="/" className="flex items-center space-x-3 p-3 rounded-lg bg-[hsl(var(--tiktok-red))]/10 text-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/20 transition-all duration-200 hover-lift">
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

      {/* Main Content Area - Full Screen Upload */}
      <div className="flex-1 ml-64 flex flex-col">
        {/* Top Bar */}
        <div className="flex justify-between items-center p-8 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              <span className="gradient-text">Reels Moderation</span>
            </h1>
            <p className="text-gray-400">
              Automatically detects and blurs sensitive information in your content
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
              href="https://github.com/spencercdz/techjam_catgpt_2025" 
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

        {/* Main Upload Area - Takes Full Remaining Space */}
        <div className="flex-1 p-6 pt-0">
          {/* Upload Content - Full Width */}
          {!file ? (
            <div className="w-full">
              {/* Upload Zone */}
              <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-6 hover-glow transition-all duration-200">
                <h2 className="text-2xl font-semibold mb-4 text-white text-center">
                  <span className="gradient-text">Upload Content</span>
                </h2>
                
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer flex flex-col items-center justify-center min-h-[300px] ${
                    dragActive 
                      ? 'border-[hsl(var(--tiktok-red))] bg-[hsl(var(--tiktok-red))]/5 scale-105' 
                      : 'border-[hsl(var(--border-color))] bg-[hsl(var(--interaction-bg))] hover:border-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--hover-bg))]'
                  }`}
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*,image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  
                  <div className="text-center">
                    <Upload className={`mx-auto h-16 w-16 mb-4 transition-all duration-300 ${
                      dragActive ? 'text-[hsl(var(--tiktok-red))] scale-110' : 'text-gray-400'
                    }`} />
                    <p className="text-xl text-gray-300 mb-2 font-medium">
                      {dragActive ? 'Drop your file here!' : 'Click to upload or drag and drop'}
                    </p>
                    <p className="text-gray-500">
                      Supports videos (MP4, AVI, MOV) and images (JPG, PNG, BMP)
                    </p>
                    {dragActive && (
                      <p className="text-[hsl(var(--tiktok-red))] font-medium mt-3 animate-pulse">
                        Release to upload!
                      </p>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="mt-4 p-3 bg-red-900/20 border border-red-700 rounded-lg flex items-center space-x-3">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    <span className="text-red-300 text-sm">{error}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* File Preview and Processing - Full Width */
            <div className="w-full space-y-4">
              {/* File Preview */}
              <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-4 hover-glow transition-all duration-200">
                <h2 className="text-xl font-semibold mb-3 text-white text-center">
                  <span className="gradient-text">File Preview</span>
                </h2>
                
                <div className="max-w-2xl mx-auto">
                  <div className="relative aspect-video bg-[hsl(var(--interaction-bg))] rounded-lg overflow-hidden mb-3">
                    {fileType === 'video' ? (
                      <>
                        <video
                          ref={videoRef}
                          src={URL.createObjectURL(file)}
                          className="w-full h-full object-cover"
                          autoPlay
                          loop
                          muted={isMuted}
                          onPlay={() => setIsPlaying(true)}
                          onPause={() => setIsPlaying(false)}
                        />
                        
                        {/* Video Controls Overlay */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                          <div className="flex items-center justify-between">
                            <button
                              onClick={togglePlayPause}
                              className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 text-white p-2 rounded-full transition-all duration-200 hover-lift"
                            >
                              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                            </button>
                            
                            <button
                              onClick={toggleMute}
                              className="text-white hover:text-[hsl(var(--tiktok-red))] transition-all duration-200"
                            >
                              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                            </button>
                          </div>
                        </div>
                      </>
                    ) : (
                      <img
                        src={URL.createObjectURL(file)}
                        alt="Preview"
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                  
                  <div className="text-center">
                    <p className="text-white font-medium text-sm">
                      {file.name} • {(file.size / 1024 / 1024).toFixed(2)} MB • {fileType.toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Processing Options */}
              <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-4 hover-glow transition-all duration-200">
                <h3 className="text-lg font-semibold mb-3 text-white text-center">
                  <span className="gradient-text">Processing Options</span>
                </h3>
                
                <div className="max-w-2xl mx-auto">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Detection Method
                      </label>
                      <select
                        value={method}
                        onChange={(e) => setMethod(e.target.value)}
                        className="w-full px-3 py-2 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-white focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200 hover:bg-[hsl(var(--hover-bg))]"
                      >
                        {fileType === 'video' ? (
                          <>
                            <option value="ocr">OCR (Text Detection)</option>
                            <option value="yolo">YOLO (Object Detection)</option>
                            <option value="combined">Combined</option>
                          </>
                        ) : (
                          <option value="yolo">YOLO (Object Detection)</option>
                        )}
                      </select>
                    </div>

                    {fileType === 'video' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Redaction Mode
                        </label>
                        <select
                          value={redactionMode}
                          onChange={(e) => setRedactionMode(e.target.value)}
                          className="w-full px-3 py-2 bg-[hsl(var(--interaction-bg))] border border-[hsl(var(--border-color))] rounded-lg text-white focus:outline-none focus:border-[hsl(var(--tiktok-red))] focus:ring-1 focus:ring-[hsl(var(--tiktok-red))] transition-all duration-200 hover:bg-[hsl(var(--hover-bg))]"
                        >
                          <option value="pixelate">Pixelate</option>
                          <option value="blur">Blur</option>
                          <option value="blackout">Blackout</option>
                        </select>
                      </div>
                    )}
                  </div>

                  <div className="text-center mt-4">
                    <button
                      onClick={processFile}
                      disabled={isProcessing}
                      className="bg-[hsl(var(--tiktok-red))] hover:bg-[hsl(var(--tiktok-red))]/90 disabled:bg-gray-600 text-white py-3 px-6 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-3 disabled:cursor-not-allowed hover-lift hover-glow mx-auto"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <span>Process Content</span>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Results Section */}
              {result && (
                <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-4 hover-glow transition-all duration-200">
                  <h3 className="text-lg font-semibold mb-3 text-white text-center">
                    <span className="gradient-text">Processing Complete</span>
                  </h3>
                  
                  <div className="max-w-2xl mx-auto">
                    <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 flex items-center space-x-3 mb-4">
                      <CheckCircle className="h-6 w-6 text-green-400" />
                      <div>
                        <p className="font-medium text-green-300">{result.message}</p>
                        <p className="text-green-400 text-sm">Output: {result.output_file}</p>
                      </div>
                    </div>

                    <div className="text-center">
                      <button
                        onClick={() => downloadFile(result.output_file)}
                        className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-2 hover-lift hover-glow mx-auto"
                      >
                        <Download className="h-4 w-4" />
                        <span>Download Processed File</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Files */}
              {processedFiles.length > 0 && (
                <div className="bg-[hsl(var(--card-background))] rounded-xl border border-[hsl(var(--border-color))] p-4 hover-glow transition-all duration-200">
                  <h3 className="text-lg font-semibold mb-3 text-white text-center">
                    <span className="gradient-text">Recent Files</span>
                  </h3>
                  
                  <div className="max-w-4xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {processedFiles.slice(0, 6).map((fileInfo, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 border border-[hsl(var(--border-color))] rounded-lg bg-[hsl(var(--interaction-bg))] hover:bg-[hsl(var(--hover-bg))] transition-all duration-200 hover-lift"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-white text-sm truncate">{fileInfo.filename}</p>
                            <p className="text-gray-400 text-xs">
                              {(fileInfo.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                          <button
                            onClick={() => downloadFile(fileInfo.filename)}
                            className="bg-[hsl(var(--tiktok-blue))] hover:bg-[hsl(var(--tiktok-blue))]/90 text-white p-2 rounded-lg text-xs font-medium transition-all duration-200 hover-lift hover-glow flex-shrink-0"
                          >
                            <Download className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                    
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
          )}
        </div>
      </div>
    </div>
  );
}
