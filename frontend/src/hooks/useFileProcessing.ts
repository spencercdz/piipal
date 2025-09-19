import { useState, useCallback } from 'react';
import { apiService, ProcessingResult, FileInfo } from '@/lib/api';

export interface UseFileProcessingReturn {
  // State
  isProcessing: boolean;
  progress: number;
  result: ProcessingResult | null;
  error: string | null;
  processedFiles: FileInfo[];
  
  // Actions
  processFile: (file: File) => Promise<void>;
  downloadFile: (filename: string) => Promise<void>;
  loadProcessedFiles: () => Promise<void>;
  clearError: () => void;
  clearResult: () => void;
  setError: (error: string) => void;
}

export function useFileProcessing(): UseFileProcessingReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processedFiles, setProcessedFiles] = useState<FileInfo[]>([]);

  const loadProcessedFiles = useCallback(async () => {
    try {
      const response = await apiService.listFiles();
      if (response.error) {
        // Only set error if it's not an authentication issue
        if (!response.error.toLowerCase().includes('authentication') && 
            !response.error.toLowerCase().includes('unauthorized') &&
            !response.error.toLowerCase().includes('401')) {
          setError(response.error);
        }
      } else if (response.data) {
        setProcessedFiles(response.data.files);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load files';
      // Only set error if it's not an authentication issue
      if (!errorMessage.toLowerCase().includes('authentication') && 
          !errorMessage.toLowerCase().includes('unauthorized') &&
          !errorMessage.toLowerCase().includes('401')) {
        setError(errorMessage);
      }
    }
  }, []);

  const processFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      const response = await apiService.processFile(file, (progress) => {
        setProgress(progress);
      });

      if (response.error) {
        // Handle specific error types from backend
        if (response.status === 429) {
          setError('Rate limit exceeded. Please wait a moment before trying again.');
        } else if (response.status === 400 && response.error.includes('Invalid filename')) {
          setError('Invalid filename. Please use a different file name.');
        } else if (response.status === 400 && response.error.includes('file content')) {
          setError('Invalid file content. The file may be corrupted or malicious.');
        } else if (response.status === 413) {
          setError('File too large. Please choose a smaller file.');
        } else {
          setError(response.error);
        }
      } else if (response.data) {
        setResult(response.data);
        // Reload processed files list
        await loadProcessedFiles();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsProcessing(false);
      setProgress(0);
    }
  }, [loadProcessedFiles]);

  const downloadFile = useCallback(async (filename: string) => {
    try {
      // Find the file in processedFiles to get the download URL
      const fileInfo = processedFiles.find(f => f.filename === filename);
      if (!fileInfo || !fileInfo.download_url) {
        setError('File not found or no download URL available');
        return;
      }

      const blob = await apiService.downloadFile(fileInfo.download_url);
      if (blob) {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        setError('Failed to download file');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  }, [processedFiles]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
  }, []);

  const setErrorCallback = useCallback((error: string) => {
    setError(error);
  }, []);

  return {
    isProcessing,
    progress,
    result,
    error,
    processedFiles,
    processFile,
    downloadFile,
    loadProcessedFiles,
    clearError,
    clearResult,
    setError: setErrorCallback,
  };
}
