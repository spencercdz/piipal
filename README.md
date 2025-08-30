# Team CatGPT Presents: PIIPal - An AI-Powered Content Privacy Tool

## **Track #7: Privacy Meets AI - Building a Safer Digital Future**

As AI technologies rapidly integrate into our daily lives, concerns about privacy and security have become more urgent than ever. With the rise of powerful generative AI models, large-scale data collection, and cloud-based deployment, users face increasing risks: sensitive data leakage, identity theft, and unauthorized exposure of Personally Identifiable Information (PII).

**Our Solution: AI for Privacy**
PIIPal addresses the "AI for Privacy" challenge by leveraging advanced computer vision AI to automatically detect and censor sensitive information in user-generated content. This solution protects user privacy while enabling safe content sharing across digital platforms.

## **Key Features & Functionality**

### **Advanced PII Detection & Censoring**
- **Multi-format Support**: Handles images (JPG, PNG, BMP, TIFF) and videos (MP4, AVI, MOV, MKV, WebM)
- **Comprehensive Detection**: Identifies 22+ PII categories including:
  - **Personal Documents**: ID cards, credit cards, licenses, badges, identity cards
  - **Digital Content**: Computer screens, phones, documents, package labels
  - **Physical Features**: Faces, tattoos, birthmarks
  - **Signage**: Traffic signs, parking signs, billboards, labels
  - **Sensitive Items**: Mirrors, tickets, calendars, planners

### **Modern TikTok-Inspired UI**
- **Dark Theme**: Professional, eye-friendly interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Interactive Elements**: Hover effects, smooth transitions, and intuitive controls
- **Side-by-Side Comparison**: View original vs. censored content simultaneously
- **Real-time Preview**: Instant feedback during processing

### **Performance & Reliability**
- **Fast Processing**: Optimized AI models for quick turnaround
- **Batch Processing**: Handle multiple files efficiently
- **Persistent Storage**: Local storage for processed files
- **Error Handling**: Robust error management and user feedback
- **Background Processing**: Non-blocking file operations

## **Development Tools Used**

### **Frontend Development**
- **Next.js 15**: React framework for production
- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development
- **Tailwind CSS 4**: Utility-first CSS framework
- **ESLint**: Code quality and consistency
- **Node.js 18+**: JavaScript runtime environment

### **Backend Development**
- **Python 3.8+**: Core programming language
- **FastAPI**: High-performance web framework
- **Uvicorn**: ASGI server for FastAPI
- **OpenCV**: Computer vision library
- **PyTorch**: Deep learning framework
- **Ultralytics**: YOLO model implementation

### **Development Environment**
- **VS Code**: Primary code editor
- **Git**: Version control
- **Conda/Pip**: Package management
- **Docker**: Containerization ready
- **Bash Scripts**: Automated deployment

## **APIs Used in the Project**

### **Core API Endpoints**
- **`POST /process`**: Single endpoint for processing images and videos
- **`GET /download/{filename}`**: Download processed files
- **`GET /files`**: List all processed files
- **`GET /health`**: Health check endpoint
- **`GET /`**: API status and information

### **API Features**
- **RESTful Design**: Standard HTTP methods and status codes
- **CORS Support**: Cross-origin resource sharing enabled
- **File Upload**: Multipart form data handling
- **Error Handling**: Comprehensive error responses
- **Background Processing**: Non-blocking file operations

## **Assets Used in the Project**

### **AI Models**
- **YOLOE-11M-SEG**: State-of-the-art object detection model
- **Custom Class Definitions**: 22+ PII categories for detection
- **Pre-trained Weights**: Optimized for privacy detection tasks

### **UI Assets**
- **Custom Icons**: Lucide React icon library
- **Color Scheme**: TikTok-inspired palette with custom CSS variables
- **Typography**: Modern, readable font stack
- **Animations**: Smooth transitions and hover effects

### **Data Assets**
- **Training Data**: Curated dataset for PII detection
- **Test Videos**: Sample content for demonstration
- **Validation Images**: Various formats and scenarios

## **Libraries Used in the Project**

### **Frontend Libraries**
```json
{
  "next": "15.5.2",
  "react": "19.1.0",
  "react-dom": "19.1.0",
  "lucide-react": "^0.542.0",
  "tailwindcss": "^4",
  "typescript": "^5"
}
```

### **Backend Libraries**
```python
# Core AI/ML
ultralytics>=8.0.0
opencv-python>=4.8.0
torch>=2.0.0
torchvision>=0.15.0

# Web Framework
fastapi
uvicorn
python-multipart

# Computer Vision
numpy>=1.24.0
Pillow>=10.0.0
moviepy

# Additional Tools
transformers
easyocr
```

## **Project Architecture**

### **Frontend (Next.js 15 + React 19)**
```
frontend/
├── src/
│   └── app/
│       ├── page.tsx          # Main application page
│       ├── layout.tsx        # Root layout component
│       └── globals.css       # Global styles and CSS variables
├── public/                   # Static assets
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # Tailwind CSS configuration
├── next.config.ts            # Next.js configuration
└── tsconfig.json             # TypeScript configuration
```

### **Backend (FastAPI + Python)**
```
backend/
├── server.py                 # Main FastAPI server
├── scripts/
│   ├── yolo_e.py            # Core YOLOE AI model
│   └── tracker.py            # Object tracking utilities
├── data/                     # Training and test data
├── uploads/                  # Temporary file storage
├── outputs/                  # Processed file storage
└── models/                   # AI model files
```

## **Quick Start**

### **Prerequisites**
- Python 3.8 or higher
- Node.js 18+ and npm
- Conda (recommended) or pip
- 8GB+ RAM (for AI model loading)
- CUDA-compatible GPU (optional, for faster processing)

### **1. Clone the Repository**
```bash
git clone https://github.com/spencercdz/techjam_catgpt_2025-.git
cd pii-pal
```

### **2. Set Up Python Environment**
```bash
# Using conda (recommended)
conda create -n pii-pal python=3.8
conda activate pii-pal

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart
```

### **3. Set Up Frontend Dependencies**
```bash
cd frontend
npm install
cd ..
```

### **4. Start the Application**
```bash
# Option 1: Use the automated startup script
chmod +x run_app.sh
./run_app.sh

# Option 2: Manual startup
# Terminal 1 - Backend
cd backend
python server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### **5. Access the Application**
- **Frontend**: yourFrontEndURL
- **Backend API**: yourBackEndURL
- **API Documentation**: http://localhost:8000/docs

## **Usage Guide**

### **Uploading Content**
1. **Drag & Drop**: Simply drag files onto the upload area
2. **Browse Files**: Click the upload area to select files manually
3. **Supported Formats**: Images (JPG, PNG, BMP, TIFF) and Videos (MP4, AVI, MOV, MKV, WebM)
4. **File Size**: Recommended under 100MB for optimal performance

### **Processing Content**
1. **Automatic Detection**: The AI automatically identifies PII objects
2. **Real-time Feedback**: See processing progress and status updates
3. **Quality Settings**: Configurable confidence thresholds and pixelation levels
4. **Batch Processing**: Process multiple files sequentially

### **Reviewing Results**
1. **Side-by-Side Comparison**: View original vs. censored content
2. **Interactive Controls**: Play/pause videos, zoom images
3. **Download Options**: Save processed files locally
4. **File Management**: Organize and manage processed content

## **Privacy & Security Features**

### **Data Protection**
- **Local Processing**: No data sent to external services
- **Temporary Storage**: Automatic cleanup of uploaded files
- **Secure Handling**: Safe file processing and storage
- **User Control**: Full control over processed content

### **AI Privacy**
- **On-device Processing**: AI models run locally
- **No Data Collection**: No user data is stored or transmitted
- **Transparent Operations**: Clear visibility into processing steps
- **Configurable Security**: Adjustable detection sensitivity

## **Acknowledgments**

- **TikTok TechJam 2025**: For the amazing hackathon opportunity
- **Ultralytics**: YOLOE model implementation
- **OpenCV**: Computer vision capabilities
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for production
- **Tailwind CSS**: Utility-first CSS framework

**PIIPal** - Making privacy protection accessible, one pixel at a time.

*Built with ❤️ by Team CatGPT for the privacy-conscious digital world*