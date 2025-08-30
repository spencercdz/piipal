'use client';

import { useState, useRef, useEffect } from 'react';
import { Upload, Video, Image, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

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
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    } catch (err) {
      console.error('Failed to fetch processed files:', err);
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

  // Fetch processed files on component mount
  useEffect(() => {
    fetchProcessedFiles();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            PII Blurring Tool
          </h1>
          <p className="text-lg text-gray-600">
            Upload videos or images to automatically detect and blur sensitive information
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* File Upload Section */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Upload File</h2>
            
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*,image/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {!file ? (
                <div>
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-lg text-gray-600 mb-2">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports videos (MP4, AVI, MOV) and images (JPG, PNG, BMP)
                  </p>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-4">
                  {fileType === 'video' ? (
                    <Video className="h-8 w-8 text-blue-500" />
                  ) : (
                    <Image className="h-8 w-8 text-green-500" />
                  )}
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <span className="text-red-700">{error}</span>
              </div>
            )}
          </div>

          {/* Processing Options */}
          {file && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold mb-4">Processing Options</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Detection Method
                  </label>
                  <select
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Redaction Mode
                    </label>
                    <select
                      value={redactionMode}
                      onChange={(e) => setRedactionMode(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pixelate">Pixelate</option>
                      <option value="blur">Blur</option>
                      <option value="blackout">Blackout</option>
                    </select>
                  </div>
                )}
              </div>

              <button
                onClick={processFile}
                disabled={isProcessing}
                className="mt-6 w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>Process File</span>
                )}
              </button>
            </div>
          )}

          {/* Results Section */}
          {result && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-2xl font-semibold mb-4">Processing Complete</h2>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-3">
                <CheckCircle className="h-6 w-6 text-green-500" />
                <div>
                  <p className="font-medium text-green-800">{result.message}</p>
                  <p className="text-sm text-green-600">Output file: {result.output_file}</p>
                </div>
              </div>

              <button
                onClick={() => downloadFile(result.output_file)}
                className="mt-4 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>Download Processed File</span>
              </button>
            </div>
          )}

          {/* Processed Files History */}
          {processedFiles.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">Processed Files</h2>
              
              <div className="space-y-3">
                {processedFiles.map((fileInfo, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{fileInfo.filename}</p>
                      <p className="text-sm text-gray-500">
                        {(fileInfo.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <button
                      onClick={() => downloadFile(fileInfo.filename)}
                      className="bg-blue-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center space-x-1"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
