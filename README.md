# Team CatGPT Presents: PIIPal - An AI-Powered Content Privacy Tool

> **Protecting Privacy Through Intelligent Content Censoring**

Built for Track #7 of the TikTok TechJam 2025, PII Pal is a cutting-edge web application that automatically detects and censors Personally Identifiable Information (PII) in images and videos using advanced AI models. Built with modern web technologies and state-of-the-art computer vision, it provides a seamless, user-friendly interface for content creators, businesses, and individuals who need to protect privacy in their media content.

## 🌟 Key Features

### 🔒 **Advanced PII Detection**
- **Multi-format Support**: Handles images (JPG, PNG, BMP, TIFF) and videos (MP4, AVI, MOV, MKV, WebM)
- **Comprehensive Detection**: Identifies 22+ PII categories including:
  - **Personal Documents**: ID cards, credit cards, licenses, badges
  - **Digital Content**: Computer screens, phones, documents
  - **Physical Features**: Faces, tattoos, birthmarks
  - **Signage**: Traffic signs, parking signs, billboards, labels
  - **Sensitive Items**: Mirrors, tickets, calendars, planners

### 🎨 **Modern TikTok-Inspired UI**
- **Dark Theme**: Professional, eye-friendly interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Interactive Elements**: Hover effects, smooth transitions, and intuitive controls
- **Side-by-Side Comparison**: View original vs. censored content simultaneously
- **Real-time Preview**: Instant feedback during processing

### 🚀 **Performance & Reliability**
- **Fast Processing**: Optimized AI models for quick turnaround
- **Batch Processing**: Handle multiple files efficiently
- **Persistent Storage**: Local storage for processed files
- **Error Handling**: Robust error management and user feedback
- **Background Processing**: Non-blocking file operations

## 🏗️ Project Architecture

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

### **Core Technologies**
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.8+, Uvicorn
- **AI/ML**: YOLOE-11M-SEG, Ultralytics, OpenCV, PyTorch
- **Storage**: Local file system with organized directories
- **Deployment**: Docker-ready with comprehensive startup scripts

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8 or higher
- Node.js 18+ and npm
- Conda (recommended) or pip
- 8GB+ RAM (for AI model loading)
- CUDA-compatible GPU (optional, for faster processing)

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/pii-pal.git
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
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

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

### **Managing Files**
1. **Recent Files**: Quick access to recently processed content
2. **File Previews**: Thumbnail previews for easy identification
3. **Delete Functionality**: Remove files from history
4. **Persistent Storage**: Files remain available after page refresh

## 🔧 Configuration

### **Environment Variables**
```bash
# Frontend
NEXT_PUBLIC_API_URL="replaceWithYourAPIKey"

# Backend
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
MODEL_PATH=backend/yoloe-11l-seg.pt
```

### **AI Model Settings**
```python
# Detection confidence threshold
conf = 0.25

# Image processing size
imgsz = 640

# Pixelation settings
padding_px = 2
pixel_size = 14  # for videos, 10 for images
```

### **Performance Tuning**
- **GPU Acceleration**: Enable CUDA for faster processing
- **Memory Management**: Adjust batch sizes based on available RAM
- **File Cleanup**: Configure automatic cleanup of temporary files
- **Caching**: Enable model caching for repeated operations

## 🛠️ Development

### **Frontend Development**
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
```

### **Backend Development**
```bash
cd backend
python server.py     # Start development server
python -m pytest     # Run tests (if configured)
```

### **Code Structure**
- **Components**: Modular React components with TypeScript
- **State Management**: React hooks for local state
- **API Integration**: RESTful API calls with error handling
- **Styling**: Tailwind CSS with custom CSS variables
- **Responsiveness**: Mobile-first design approach

### **Adding New Features**
1. **Frontend**: Create new components in `src/app/`
2. **Backend**: Add new endpoints in `server.py`
3. **AI Models**: Extend detection capabilities in `yolo_e.py`
4. **Styling**: Update CSS variables in `globals.css`

## 📊 API Reference

### **Core Endpoints**

#### **POST /process**
Process images and videos for PII detection and censoring.

**Request:**
```http
POST /process
Content-Type: multipart/form-data

file: [binary file data]
```

**Response:**
```json
{
  "message": "Video processed successfully",
  "output_file": "censored_uuid_filename.mp4",
  "download_url": "/download/censored_uuid_filename.mp4",
  "file_type": "video"
}
```

#### **GET /download/{filename}**
Download processed files.

#### **GET /files**
List all processed files.

#### **GET /health**
Health check endpoint.

### **Error Handling**
```json
{
  "detail": "Error message description"
}
```

**Common Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid file type, missing file)
- `404`: File Not Found
- `500`: Internal Server Error

## 🔒 Security Features

### **Input Validation**
- File type verification
- File size limits
- Malicious file detection
- Secure file handling

### **Data Privacy**
- Local processing (no data sent to external services)
- Temporary file cleanup
- Secure file storage
- Access control mechanisms

### **API Security**
- CORS configuration
- Rate limiting (configurable)
- Input sanitization
- Error message sanitization

## 🚀 Deployment

### **Production Setup**
1. **Environment Configuration**: Set production environment variables
2. **SSL/TLS**: Configure HTTPS for secure communication
3. **Load Balancing**: Set up reverse proxy (nginx/Apache)
4. **Monitoring**: Implement logging and health checks
5. **Backup**: Configure automated backups for processed files

### **Docker Deployment**
```dockerfile
# Example Dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "backend/server.py"]
```

### **Cloud Deployment**
- **AWS**: EC2, S3, CloudFront
- **Google Cloud**: Compute Engine, Cloud Storage
- **Azure**: Virtual Machines, Blob Storage
- **Heroku**: Container deployment

## 🧪 Testing

### **Frontend Testing**
```bash
cd frontend
npm run test        # Run unit tests
npm run test:e2e    # Run end-to-end tests
```

### **Backend Testing**
```bash
cd backend
python -m pytest tests/    # Run API tests
python -m pytest tests/unit/    # Run unit tests
```

### **Integration Testing**
- API endpoint testing
- File processing workflows
- Error handling scenarios
- Performance benchmarks

## 📈 Performance Optimization

### **AI Model Optimization**
- Model quantization
- Batch processing
- GPU acceleration
- Memory management

### **Frontend Optimization**
- Code splitting
- Lazy loading
- Image optimization
- Bundle optimization

### **Backend Optimization**
- Async processing
- Connection pooling
- Caching strategies
- Resource management

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### **Code Standards**
- TypeScript for frontend
- Python type hints
- ESLint configuration
- Pre-commit hooks

### **Documentation**
- Update README for new features
- Add API documentation
- Include code examples
- Maintain changelog

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ultralytics**: YOLOE model implementation
- **OpenCV**: Computer vision capabilities
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for production
- **Tailwind CSS**: Utility-first CSS framework

## 📞 Support

### **Getting Help**
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the comprehensive docs
- **Examples**: Review sample implementations

### **Community**
- **GitHub**: [Repository](https://github.com/yourusername/pii-pal)
- **Discord**: Join our community server
- **Email**: support@piipal.com
- **Twitter**: [@PIIPal](https://twitter.com/PIIPal)

---

**PII Pal** - Making privacy protection accessible, one pixel at a time. 🛡️✨

*Built with ❤️ by Team CatGPT for the privacy-conscious digital world*