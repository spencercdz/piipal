from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid
import tempfile
import shutil
from pathlib import Path
import logging
from typing import Optional, Dict, Any
import sys
import time

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only from yolo_e.py
from scripts.yolo_e import run_image_pixelate, run_video_censor, model

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Supabase integration (optional)
try:
    from auth_middleware import get_current_user_optional
    from database_service import db_service
    from supabase_config import supabase_config
    from supabase_storage import storage_service
    SUPABASE_AVAILABLE = True
    logger.info("Supabase integration loaded successfully")
except ImportError as e:
    logger.warning(f"Supabase integration not available: {e}")
    SUPABASE_AVAILABLE = False
    # Create dummy functions for when Supabase is not available
    def get_current_user_optional(request):
        return None

app = FastAPI(
    title="PII Censor API", 
    description="API for censoring PII in videos and images using YOLOE",
    # Increase file upload limits to 50MB
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize Supabase connection (if available)
# Initialize Supabase if available (will be done in startup event)
if SUPABASE_AVAILABLE:
    logger.info("Supabase integration will be initialized on startup")
else:
    logger.info("Running without Supabase integration")

# Add startup event handler for Supabase initialization
@app.on_event("startup")
async def startup_event():
    """Initialize Supabase on startup"""
    global SUPABASE_AVAILABLE
    if SUPABASE_AVAILABLE:
        try:
            # Test Supabase connection
            supabase_config.test_connection()
            # Initialize storage bucket
            await storage_service.create_bucket()
            logger.info("Supabase integration initialized successfully")
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {str(e)}")
            logger.warning("Continuing without Supabase integration")
            SUPABASE_AVAILABLE = False

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://piipal.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create upload directory (outputs now handled by Supabase Storage)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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
    background_tasks: BackgroundTasks = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Single endpoint to process both video and image files for PII censoring
    
    Automatically detects file type and applies appropriate processing:
    - Images: Uses run_image_pixelate() with YOLOE detection
    - Videos: Uses run_video_censor() with YOLOE detection and frame-by-frame processing
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Log file information for debugging
    logger.info(f"Processing file: {file.filename}")
    logger.info(f"File size: {file.size} bytes ({file.size / (1024 * 1024):.2f} MB)")
    logger.info(f"File content type: {file.content_type}")
    
    # Check file size limit (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    if file.size and file.size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file.size} bytes > {MAX_FILE_SIZE} bytes")
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    # output_filename will be set later based on actual saved file
    output_filename = None
    output_path = None
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Processing file: {file.filename}")
        
        # Start processing timer
        start_time = time.time()
        
        # Process based on file type
        if is_video_file(file.filename):
            logger.info(f"Processing as video: {file.filename}")
            
            # Set output filename for video
            output_filename = f"censored_{file_id}_{file.filename}"
            output_path = UPLOAD_DIR / output_filename
            
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
                outdir=str(UPLOAD_DIR),
                imgsz=640,
                conf=0.25,
                verbose=False,
                padding_px=2,
                pixel_size=10,
                save=True
            )
            
            # Rename the output file to match our naming convention
            # yolo_e.py saves with "_output" suffix, so we need to find and rename it
            # The actual pattern is: {original_filename_without_ext}_output{ext}
            original_name = Path(file.filename).stem
            original_ext = Path(file.filename).suffix
            expected_output_pattern = f"{original_name}_output{original_ext}"
            output_files = list(UPLOAD_DIR.glob(expected_output_pattern))
            
            if output_files:
                # Use the actual output file name instead of trying to rename
                output_filename = output_files[0].name
                output_path = output_files[0]
                logger.info(f"Using output file: {output_filename}")
            else:
                logger.warning(f"Could not find output file with pattern: {expected_output_pattern}")
                # List all files in upload directory for debugging
                all_files = list(UPLOAD_DIR.glob("*"))
                logger.info(f"Available files in upload directory: {[f.name for f in all_files]}")
                # Fallback: use the expected output pattern as the filename
                output_filename = expected_output_pattern
                output_path = UPLOAD_DIR / expected_output_pattern
            
            message = f"Image processed successfully. Found {len(detections)} PII objects."
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_VIDEO_TYPES | SUPPORTED_IMAGE_TYPES)}"
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Upload to Supabase Storage (required for authenticated users)
        storage_info = None
        if current_user:
            if not SUPABASE_AVAILABLE:
                raise HTTPException(status_code=503, detail="Supabase Storage not available - authentication required")
            
            if not output_path or not output_path.exists():
                raise HTTPException(status_code=500, detail="Processing failed - no output file generated")
            
            try:
                # Upload to Supabase Storage
                storage_info = await storage_service.upload_file(
                    str(output_path), 
                    current_user["user_id"], 
                    "video" if is_video_file(file.filename) else "image"
                )
                
                if storage_info:
                    logger.info(f"Successfully uploaded file to Supabase Storage for user {current_user['user_id']}")
                    logger.info(f"Public URL: {storage_info['public_url']}")
                    
                    # Clean up local file after successful upload
                    output_path.unlink()
                    logger.info(f"Cleaned up local file: {output_path}")
                else:
                    raise HTTPException(status_code=500, detail="Failed to upload file to Supabase Storage")
            except Exception as e:
                logger.error(f"Failed to upload to Supabase Storage: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")
        else:
            # Unauthenticated users cannot process files
            raise HTTPException(status_code=401, detail="Authentication required to process files")
        
        # Clean up input file
        if input_path.exists():
            input_path.unlink()
        
        # Use Supabase Storage URL (required)
        if not storage_info or not storage_info.get("public_url"):
            raise HTTPException(status_code=500, detail="No storage information available")
        
        download_url = storage_info["public_url"]
        output_file = storage_info["filename"]
        
        return {
            "message": message,
            "output_file": output_file,
            "download_url": download_url,
            "file_type": "video" if is_video_file(file.filename) else "image",
            "processing_time": processing_time,
            "user_id": current_user["user_id"] if current_user else None,
            "storage_url": storage_info["public_url"] if storage_info else None
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        # Clean up files on error
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Note: Download endpoint removed - files are served directly from Supabase Storage

@app.get("/files")
async def list_files(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """List processed files - requires authentication and Supabase Storage"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase Storage not available")
    
    try:
        user_files = await storage_service.list_user_files(current_user["user_id"])
        return {"files": user_files}
    except Exception as e:
        logger.error(f"Error fetching user files from Supabase Storage: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user files")

@app.get("/user/profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Get user profile - requires authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        profile = await db_service.get_user_profile(current_user["user_id"])
        if not profile:
            # Create profile if it doesn't exist
            profile = await db_service.create_user_profile(
                current_user["user_id"], 
                current_user["email"]
            )
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user profile")

@app.get("/user/stats")
async def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Get user statistics - requires authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase Storage not available")
    
    try:
        # Get user files from Supabase Storage
        user_files = await storage_service.list_user_files(current_user["user_id"])
        
        # Calculate stats from storage files
        total_files = len(user_files)
        images_processed = len([f for f in user_files if f.get('filename', '').lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))])
        videos_processed = len([f for f in user_files if f.get('filename', '').lower().endswith(('.mp4', '.avi', '.mov', '.webm'))])
        
        stats = {
            "total_files": total_files,
            "completed_files": total_files,  # All files in storage are completed
            "images_processed": images_processed,
            "videos_processed": videos_processed,
            "this_month": 0  # TODO: Implement monthly stats from file timestamps
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user statistics")

@app.get("/user/files")
async def get_user_files(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Get user's processed files - requires authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase Storage not available")
    
    try:
        files = await storage_service.list_user_files(current_user["user_id"])
        return {"files": files}
    except Exception as e:
        logger.error(f"Error getting user files: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user files")

@app.delete("/user/delete")
async def delete_user_account(current_user: Dict[str, Any] = Depends(get_current_user_optional)):
    """Delete user account and all associated data - requires authentication"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase Storage not available")
    
    try:
        user_id = current_user["user_id"]
        
        # Delete all user files from Supabase Storage
        try:
            user_files = await storage_service.list_user_files(user_id)
            for file_info in user_files:
                file_path = file_info.get('path')
                if file_path:
                    await storage_service.delete_file(file_path)
            logger.info(f"Deleted {len(user_files)} files for user {user_id}")
        except Exception as e:
            logger.warning(f"Error deleting user files: {str(e)}")
        
        # Delete user profile and preferences from database
        try:
            if db_service:
                # Delete user preferences
                db_service.supabase.table("user_preferences").delete().eq("user_id", user_id).execute()
                # Delete user profile
                db_service.supabase.table("user_profiles").delete().eq("user_id", user_id).execute()
                logger.info(f"Deleted user profile and preferences for user {user_id}")
        except Exception as e:
            logger.warning(f"Error deleting user database records: {str(e)}")
        
        # Note: We don't delete the user from Supabase Auth here as that should be handled
        # by the frontend calling supabase.auth.admin.deleteUser() or the user can delete
        # their account through Supabase dashboard
        
        logger.info(f"Successfully deleted account data for user {user_id}")
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting account")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        # Increase limits for file uploads
        limit_max_requests=1000,
        limit_concurrency=1000,
        timeout_keep_alive=30
    )
