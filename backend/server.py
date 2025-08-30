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

# Import only from yolo_e.py
from scripts.yolo_e import run_image_pixelate, run_video_censor, model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PII Censor API", description="API for censoring PII in videos and images using YOLOE")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://piipal.vercel.app"],  # In production, specify your frontend URL
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
SUPPORTED_VIDEO_TYPES = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".MP4", ".AVI", ".MOV", ".MKV", ".WEBM"}
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG", ".BMP", ".TIFF"}

def is_video_file(filename: str) -> bool:
    """Check if file is a video based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_VIDEO_TYPES

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_IMAGE_TYPES

@app.get("/")
async def root():
    return {"message": "PII Censor API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/process")
async def process_file_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Single endpoint to process both video and image files for PII censoring
    
    Automatically detects file type and applies appropriate processing:
    - Images: Uses run_image_pixelate() with YOLOE detection
    - Videos: Uses run_video_censor() with YOLOE detection and frame-by-frame processing
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    output_filename = f"censored_{file_id}_{file.filename}"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing file: {file.filename}")
        
        # Process based on file type
        if is_video_file(file.filename):
            logger.info(f"Processing as video: {file.filename}")
            
            # Process video using yolo_e.py
            run_video_censor(
                model=model,
                in_video_path=str(input_path),
                out_video_path=str(output_path),
                imgsz=640,
                conf=0.25,
                pixel_size=14,
                verbose=False
            )
            
            message = "Video processed successfully"
            
        elif is_image_file(file.filename):
            logger.info(f"Processing as image: {file.filename}")
            
            # Process image using yolo_e.py
            processed_img, detections = run_image_pixelate(
                model=model,
                img_path=str(input_path),
                outdir=str(OUTPUT_DIR),
                imgsz=640,
                conf=0.25,
                verbose=False,
                padding_px=2,
                pixel_size=10,
                save=True
            )
            
            # Rename the output file to match our naming convention
            # yolo_e.py saves with "_output" suffix, so we need to find and rename it
            output_files = list(OUTPUT_DIR.glob(f"{file_id}_*_output.*"))
            if output_files:
                # Rename the first output file to our desired name
                old_output_path = output_files[0]
                old_output_path.rename(output_path)
            
            message = f"Image processed successfully. Found {len(detections)} PII objects."
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_VIDEO_TYPES | SUPPORTED_IMAGE_TYPES)}"
            )
        
        # Clean up input file
        if input_path.exists():
            input_path.unlink()
        
        return {
            "message": message,
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}",
            "file_type": "video" if is_video_file(file.filename) else "image"
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        # Clean up files on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

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
