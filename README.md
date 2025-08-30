# PII Blurring Tool

A comprehensive tool for automatically detecting and blurring Personally Identifiable Information (PII) in videos and images. The application consists of a FastAPI backend with multiple detection methods and a Next.js TypeScript frontend.

## Features

- **Multiple Detection Methods**:
  - **OCR-based**: Uses EasyOCR and ML models to detect sensitive text in videos
  - **YOLO-based**: Uses YOLO object detection for sensitive objects (license plates, IDs, credit cards, etc.)
  - **Combined**: Combines both approaches for comprehensive detection

- **Redaction Options**:
  - **Pixelate**: Pixelates sensitive regions
  - **Blur**: Applies Gaussian blur
  - **Blackout**: Completely blacks out sensitive regions

- **File Support**:
  - **Videos**: MP4, AVI, MOV, MKV, WebM
  - **Images**: JPG, PNG, BMP, TIFF

- **Modern Web Interface**:
  - Drag-and-drop file upload
  - Real-time processing status
  - File history and download management
  - Responsive design

## Architecture

### Backend (FastAPI)
- `detector.py`: Main OCR-based PII detection with tracking
- `detector_yolo.py`: YOLO-based object detection for sensitive objects
- `detector_ocr.py`: OCR-based text detection with regex patterns
- `server.py`: FastAPI server with REST endpoints

### Frontend (Next.js + TypeScript)
- Modern React with TypeScript
- Tailwind CSS for styling
- Lucide React for icons
- File upload with drag-and-drop
- Real-time processing feedback

## Prerequisites

- Python 3.8+
- Node.js 18+
- Conda environment (recommended)

## Installation

### 1. Backend Setup

```bash
# Activate conda environment
conda activate env

# Install Python dependencies
pip install -r requirements.txt

# Install additional FastAPI dependencies
pip install fastapi uvicorn python-multipart
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Install additional packages
npm install lucide-react
```

## Usage

### Quick Start (Recommended)

Use the provided startup script to run both servers automatically:

```bash
# From the project root directory
./run_app.sh
```

This script will:
- Activate the conda environment
- Check and install dependencies if needed
- Start both backend and frontend servers
- Display the URLs for accessing the application

Press `Ctrl+C` to stop all servers.

### Manual Start

If you prefer to start servers manually:

#### 1. Start the Backend Server

```bash
# From the project root directory
conda activate env
cd backend
python server.py
```

The FastAPI server will start on `http://localhost:8000`

#### 2. Start the Frontend Development Server

```bash
# From the frontend directory
cd frontend
npm run dev
```

The Next.js app will start on `http://localhost:3000`

### 3. Using the Application

1. Open your browser and go to `http://localhost:3000`
2. Upload a video or image file by clicking or dragging and dropping
3. Select your preferred detection method and redaction mode
4. Click "Process File" to start the PII detection and blurring
5. Download the processed file when complete

## API Endpoints

### Video Processing
- `POST /process-video` - Process video files
  - Parameters: `method` (ocr/yolo/combined), `redaction_mode` (pixelate/blur/blackout)

### Image Processing
- `POST /process-image` - Process image files
  - Parameters: `method` (yolo)

### File Management
- `GET /files` - List all processed files
- `GET /download/{filename}` - Download a processed file

## Detection Methods

### OCR Method (Recommended for Videos)
- Uses EasyOCR for text detection
- ML model for PII classification
- Regex patterns for additional validation
- Tracking for consistent redaction across frames

### YOLO Method (Recommended for Images)
- Object detection for sensitive items
- Supports license plates, IDs, credit cards, etc.
- High accuracy for object-based PII

### Combined Method
- Combines OCR and YOLO approaches
- Most comprehensive detection

## Configuration

### Backend Configuration
The detection parameters can be adjusted in the respective detector files:

- `detector.py`: OCR confidence thresholds, tracking parameters
- `detector_yolo.py`: YOLO confidence thresholds, blur strength
- `detector_ocr.py`: OCR parameters, regex patterns

### Frontend Configuration
The API base URL can be changed in `frontend/src/app/page.tsx`:

```typescript
const API_BASE_URL = 'http://localhost:8000';
```

## File Structure

```
techjam_catgpt_2025/
├── backend/
│   ├── data/                 # Sample data files
│   ├── detector.py           # Main OCR detector
│   ├── detector_yolo.py      # YOLO object detector
│   ├── detector_ocr.py       # OCR text detector
│   ├── server.py             # FastAPI server
│   ├── uploads/              # Temporary upload directory
│   └── outputs/              # Processed files directory
├── frontend/
│   ├── src/
│   │   └── app/
│   │       └── page.tsx      # Main application page
│   └── package.json
├── run_app.sh               # Startup script for both servers
├── requirements.txt          # Python dependencies
└── README.md
```

## Troubleshooting

### Common Issues

1. **CUDA/GPU Issues**: The models will automatically fall back to CPU if CUDA is not available
2. **Memory Issues**: For large videos, consider processing in smaller chunks
3. **Model Download**: First run may take longer as models are downloaded

### Performance Tips

- Use GPU acceleration when available
- For large files, consider using the YOLO method for faster processing
- Adjust confidence thresholds based on your needs

## Development

### Adding New Detection Methods

1. Create a new detector module in the `backend/` directory
2. Add the import and endpoint in `server.py`
3. Update the frontend to include the new method option

### Customizing Redaction Styles

Modify the redaction functions in the detector files:
- `pixelate()`: Adjust block size for pixelation
- `blur()`: Modify kernel size and sigma for blur strength
- `blackout()`: Change the replacement color/pattern

## License

This project is for educational and research purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
