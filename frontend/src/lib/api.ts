// API service layer for backend integration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ProcessingResult {
  message: string;
  output_file: string;
  download_url: string;
  file_type: string;
  processing_time?: number;
  user_id?: string;
  storage_url?: string;
}

export interface FileInfo {
  filename: string;
  size: number;
  download_url: string;
  originalFileUrl?: string; // Store the blob URL of the original uploaded file
  censoredFile?: string; // Store the censored file name
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    // Try to get the current session token
    try {
      const { supabase } = await import('@/lib/supabase');
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session?.access_token) {
        return {
          'Authorization': `Bearer ${session.access_token}`,
        };
      }
    } catch (error) {
      console.warn('Could not get auth token:', error);
    }
    
    return {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const authHeaders = await this.getAuthHeaders();
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  private async uploadFile(
    endpoint: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<ProcessingResult>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          try {
            const data = JSON.parse(xhr.responseText);
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve({
                data,
                status: xhr.status,
              });
            } else {
              resolve({
                error: data.detail || `HTTP ${xhr.status}: ${xhr.statusText}`,
                status: xhr.status,
              });
            }
          } catch (error) {
            resolve({
              error: 'Invalid response format',
              status: xhr.status,
            });
          }
        });

        xhr.addEventListener('error', () => {
          resolve({
            error: 'Network error during upload',
            status: 0,
          });
        });

        xhr.open('POST', `${this.baseUrl}${endpoint}`);
        xhr.send(formData);
      });
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Upload error',
        status: 0,
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request('/health');
  }

  // Process file (upload and process)
  async processFile(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<ProcessingResult>> {
    return this.uploadFile('/process', file, onProgress);
  }

  // Download processed file
  async downloadFile(filename: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${this.baseUrl}/download/${filename}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.blob();
    } catch (error) {
      console.error('Download error:', error);
      return null;
    }
  }

  // List processed files
  async listFiles(): Promise<ApiResponse<{ files: FileInfo[] }>> {
    return this.request('/files');
  }

  // Get download URL for a file
  getDownloadUrl(filename: string): string {
    return `${this.baseUrl}/download/${filename}`;
  }

  // User-specific endpoints
  async getUserProfile(): Promise<ApiResponse<unknown>> {
    return this.request('/user/profile');
  }

  async getUserStats(): Promise<ApiResponse<unknown>> {
    return this.request('/user/stats');
  }

  async getUserFiles(): Promise<ApiResponse<{ files: FileInfo[] }>> {
    return this.request('/user/files');
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Export individual functions for convenience
export const {
  healthCheck,
  processFile,
  downloadFile,
  listFiles,
  getDownloadUrl,
  getUserProfile,
  getUserStats,
  getUserFiles,
} = apiService;
