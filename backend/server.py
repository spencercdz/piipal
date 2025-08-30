from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid
import tempfile
import shutil
from pathlib import Path
import logging
from typing import Optional
import sys

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detector import process_video_consistent
from detector_yolo import process_image as yolo_process_image, process_video as yolo_process_video
from detector_ocr import process_video_consistent as ocr_process_video

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PII Blurring API", description="API for blurring PII in videos and images")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload and output directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Supported file types
SUPPORTED_VIDEO_TYPES = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

def is_video_file(filename: str) -> bool:
    """Check if file is a video based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_VIDEO_TYPES

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_IMAGE_TYPES

@app.get("/")
async def root():
    return {"message": "PII Blurring API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/process-video")
async def process_video_endpoint(
    file: UploadFile = File(...),
    method: str = "combined",  # "ocr", "yolo", or "combined"
    redaction_mode: str = "pixelate",  # "pixelate", "blur", "blackout"
    background_tasks: BackgroundTasks = None
):
    """
    Process a video file to blur PII
    
    - method: "ocr" (text-based), "yolo" (object detection), or "combined"
    - redaction_mode: "pixelate", "blur", or "blackout"
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_video_file(file.filename):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    output_filename = f"blurred_{file_id}_{file.filename}"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing video: {file.filename} with method: {method}")
        
        # Process based on method
        if method == "ocr":
            process_video_consistent(
                str(input_path),
                str(output_path),
                redaction_mode=redaction_mode,
                pad=8,
                min_prob=0.2,
                max_lost=8,
                iou_thresh=0.3,
                debug=False
            )
        elif method == "yolo":
            yolo_process_video(str(input_path), str(output_path))
        elif method == "combined":
            # For combined, we'll use OCR for now (can be enhanced later)
            process_video_consistent(
                str(input_path),
                str(output_path),
                redaction_mode=redaction_mode,
                pad=8,
                min_prob=0.2,
                max_lost=8,
                iou_thresh=0.3,
                debug=False,
                nlp=False
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid method. Use 'ocr', 'yolo', or 'combined'")
        
        # Clean up input file
        if input_path.exists():
            input_path.unlink()
        
        return {
            "message": "Video processed successfully",
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}"
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        # Clean up files on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.post("/process-image")
async def process_image_endpoint(
    file: UploadFile = File(...),
    method: str = "yolo"  # "yolo" for images (OCR is mainly for videos)
):
    """
    Process an image file to blur PII
    
    - method: "yolo" (object detection)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_image_file(file.filename):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    output_filename = f"blurred_{file_id}_{file.filename}"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing image: {file.filename} with method: {method}")
        
        # Process image (YOLO is best for images)
        if method == "yolo":
            yolo_process_image(str(input_path), str(output_path))
        else:
            raise HTTPException(status_code=400, detail="Invalid method. Use 'yolo' for images")
        
        # Clean up input file
        if input_path.exists():
            input_path.unlink()
        
        return {
            "message": "Image processed successfully",
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}"
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        # Clean up files on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a processed file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/files")
async def list_files():
    """List all processed files"""
    files = []
    for file_path in OUTPUT_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "download_url": f"/download/{file_path.name}"
            })
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
