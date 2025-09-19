# Backend Integration Guide

## Overview
The frontend has been integrated with the FastAPI backend for file processing. The integration includes:

- **API Service Layer**: Centralized API communication
- **File Processing Hook**: React hook for managing file uploads and processing
- **Progress Tracking**: Real-time upload progress
- **Error Handling**: Comprehensive error management
- **File Management**: Download and list processed files

## Environment Configuration

Add these variables to your `.env.local` file:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, update `NEXT_PUBLIC_API_URL` to your deployed backend URL.

## Backend Setup

1. **Start the backend server**:
   ```bash
   cd backend
   python server.py
   ```
   The server will run on `http://localhost:8000`

2. **Verify backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

## API Endpoints

The backend provides these endpoints:

- `GET /health` - Health check
- `POST /process` - Upload and process files (images/videos)
- `GET /download/{filename}` - Download processed files
- `GET /files` - List all processed files

## Features

### File Processing
- **Automatic Detection**: Automatically detects image vs video files
- **Progress Tracking**: Shows upload progress with progress bar
- **Error Handling**: Displays detailed error messages
- **File Persistence**: Maintains processed files list

### Supported Formats
- **Images**: JPG, JPEG, PNG, BMP, TIFF
- **Videos**: MP4, AVI, MOV, MKV, WEBM

### UI Integration
- **Progress Indicator**: Real-time upload progress
- **Error Display**: Clear error messages
- **File Management**: Download and view processed files
- **Recent Files**: Maintains list of recent processed files

## Usage

1. **Upload File**: Select a file using the file input or drag & drop
2. **Process**: Click "Censor" to start processing
3. **Monitor Progress**: Watch the progress bar during upload
4. **Download**: Click download button to get the processed file
5. **View Results**: Processed files appear in the recent files list

## Error Handling

The integration includes comprehensive error handling:

- **Network Errors**: Connection issues with backend
- **File Format Errors**: Unsupported file types
- **Processing Errors**: Backend processing failures
- **Download Errors**: File download issues

## Development

### API Service (`src/lib/api.ts`)
- Centralized API communication
- Progress tracking for uploads
- Error handling and response parsing

### File Processing Hook (`src/hooks/useFileProcessing.ts`)
- React hook for file processing
- State management for processing status
- Progress tracking and error handling

### Integration Points
- **Main Page**: Uses the file processing hook
- **Progress Display**: Shows real-time upload progress
- **Error Display**: Displays processing errors
- **File Management**: Handles downloads and file listing

## Troubleshooting

### Backend Not Running
- Ensure backend server is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in environment variables
- Verify backend health endpoint: `http://localhost:8000/health`

### File Processing Issues
- Check file format is supported
- Verify file size limits
- Check backend logs for processing errors

### Download Issues
- Ensure processed file exists in backend outputs
- Check network connectivity
- Verify file permissions

## Production Deployment

1. **Update API URL**: Set `NEXT_PUBLIC_API_URL` to production backend URL
2. **CORS Configuration**: Update backend CORS settings for production domain
3. **File Storage**: Configure persistent file storage for production
4. **Error Monitoring**: Set up error monitoring and logging
