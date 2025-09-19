from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request
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
from collections import defaultdict
from datetime import datetime, timedelta

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    """Initialize Supabase on startup - non-blocking"""
    logger.info("🚀 FastAPI app starting up...")
    logger.info(f"📡 Port: {os.environ.get('PORT', '8000')}")
    logger.info("✅ App is ready to accept requests!")
    
    global SUPABASE_AVAILABLE
    if SUPABASE_AVAILABLE:
        try:
            # Test Supabase connection with timeout
            supabase_config.test_connection()
            logger.info("Supabase connection test successful")
            
            # Initialize storage bucket in background (non-blocking)
            import asyncio
            asyncio.create_task(initialize_storage_bucket())
            
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {str(e)}")
            logger.warning("Continuing without Supabase integration")
            SUPABASE_AVAILABLE = False
    
    # Load YOLO model after startup (non-blocking)
    import asyncio
    asyncio.create_task(load_model_after_startup())

async def initialize_storage_bucket():
    """Initialize storage bucket in background"""
    try:
        await storage_service.create_bucket()
        logger.info("Supabase storage bucket initialized successfully")
    except Exception as e:
        logger.warning(f"Storage bucket initialization failed: {str(e)}")
        logger.warning("Storage features may not work properly")

async def load_model_after_startup():
    """Load YOLO model after startup to avoid blocking port binding"""
    try:
        logger.info("🤖 Loading YOLO model in background...")
        
        # Import memory optimization modules
        import gc
        import psutil
        
        # Log initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"📊 Initial memory usage: {initial_memory:.1f} MB")
        
        from scripts.yolo_e import get_model
        model = get_model()
        
        # Log memory usage after model loading
        post_model_memory = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"📊 Memory after model load: {post_model_memory:.1f} MB (+{post_model_memory - initial_memory:.1f} MB)")
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"📊 Memory after cleanup: {final_memory:.1f} MB")
        
        logger.info("✅ YOLO model loaded successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to load YOLO model: {str(e)}")
        logger.warning("File processing will fail until model is loaded")

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

# Rate limiting storage
rate_limit_storage = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # Max requests per minute per IP
RATE_LIMIT_WINDOW = 60  # Time window in seconds

# Supported file types
SUPPORTED_VIDEO_TYPES = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".MP4", ".AVI", ".MOV", ".MKV", ".WEBM"}
SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".JPG", ".JPEG", ".PNG", ".BMP", ".TIFF"}

def is_video_file(filename: str) -> bool:
    """Check if file is a video based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_VIDEO_TYPES

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension"""
    return Path(filename).suffix.lower() in SUPPORTED_IMAGE_TYPES

def _check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = datetime.now()
    # Clean old entries
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip]
        if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(now)
    return True

def _validate_file_content(file_path: Path, content_type: str) -> bool:
    """Basic file content validation to prevent malicious uploads"""
    try:
        # Check file size (should already be validated, but double-check)
        if file_path.stat().st_size == 0:
            return False
        
        # Read first few bytes to check file signatures
        with open(file_path, 'rb') as f:
            header = f.read(16)
        
        # Check for common file signatures
        if content_type.startswith('image/'):
            # Check for image file signatures
            if header.startswith(b'\xFF\xD8\xFF'):  # JPEG
                return True
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                return True
            elif header.startswith(b'BM'):  # BMP
                return True
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
                return True
            else:
                logger.warning(f"Unknown image format for file: {file_path}")
                return False
                
        elif content_type.startswith('video/'):
            # Check for video file signatures
            if header.startswith(b'\x00\x00\x00'):  # MP4/MOV
                return True
            elif header.startswith(b'RIFF'):  # AVI/WEBM
                return True
            else:
                logger.warning(f"Unknown video format for file: {file_path}")
                return False
        
        # If we can't validate, be conservative and reject
        logger.warning(f"Could not validate file content for: {file_path}")
        return False
        
    except Exception as e:
        logger.error(f"Error validating file content: {e}")
        return False

@app.get("/")
async def root():
    """Root endpoint - ensures port binding works immediately"""
    return {"message": "PII Censor API is running", "status": "ready"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Render deployment"""
    return {
        "status": "healthy",
        "supabase_available": SUPABASE_AVAILABLE,
        "timestamp": time.time()
    }

@app.get("/ready")
async def ready_check():
    """Simple readiness check for Render port detection"""
    return {"status": "ready", "port": os.environ.get("PORT", "unknown")}

@app.get("/status")
async def status_check():
    """Comprehensive status check for monitoring"""
    try:
        # Check if YOLO model is loaded
        model_loaded = False
        try:
            from scripts.yolo_e import _model
            model_loaded = _model is not None
        except ImportError as e:
            logger.warning(f"Could not import YOLO model for status check: {e}")
        except Exception as e:
            logger.warning(f"Error checking model status: {e}")
        
        # Get memory usage
        memory_info = {}
        try:
            import psutil
            process = psutil.Process()
            memory_info = {
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                "memory_percent": round(process.memory_percent(), 1),
                "cpu_percent": round(process.cpu_percent(), 1)
            }
        except ImportError:
            memory_info = {"error": "psutil not available"}
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "port": os.environ.get("PORT", "unknown"),
            "supabase_available": SUPABASE_AVAILABLE,
            "model_loaded": model_loaded,
            "uptime": "running",
            "system": memory_info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for health checks"""
    return {"pong": True, "timestamp": time.time()}


@app.post("/process")
async def process_file_endpoint(
    request: Request,
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
    # Rate limiting check
    client_ip = request.client.host
    if not _check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
        )
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Log file information for debugging
    logger.info(f"Processing file: {file.filename}")
    logger.info(f"File size: {file.size} bytes ({file.size / (1024 * 1024):.2f} MB)")
    logger.info(f"File content type: {file.content_type}")
    
    # Check file size limit (reduced to 25MB for memory constraints)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes (reduced from 50MB)
    if file.size and file.size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file.size} bytes > {MAX_FILE_SIZE} bytes")
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Generate unique filename with security validation
    file_id = str(uuid.uuid4())
    
    # Sanitize filename to prevent path traversal attacks
    import re
    safe_filename = re.sub(r'[^\w\-_\.]', '_', file.filename)
    safe_filename = safe_filename[:100]  # Limit filename length
    
    # Ensure filename doesn't contain path traversal attempts
    if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename - path traversal not allowed")
    
    input_path = UPLOAD_DIR / f"{file_id}_{safe_filename}"
    # output_filename will be set later based on actual saved file
    output_filename = None
    output_path = None
    
    try:
        # Save uploaded file with content validation
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Basic file content validation
        if not _validate_file_content(input_path, file.content_type):
            input_path.unlink()  # Remove the file
            raise HTTPException(status_code=400, detail="Invalid file content - file may be corrupted or malicious")
        
        logger.info(f"Processing file: {file.filename}")
        
        # Start processing timer
        start_time = time.time()
        
        # Log memory usage before processing
        try:
            import psutil
            process = psutil.Process()
            pre_processing_memory = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"📊 Memory before processing: {pre_processing_memory:.1f} MB")
            
            # Check if we're approaching memory limit (400MB out of 512MB)
            if pre_processing_memory > 400:
                logger.warning(f"⚠️ High memory usage detected: {pre_processing_memory:.1f} MB")
                # Force garbage collection
                import gc
                gc.collect()
                post_gc_memory = process.memory_info().rss / 1024 / 1024  # MB
                logger.info(f"📊 Memory after cleanup: {post_gc_memory:.1f} MB")
        except ImportError:
            pass
        
        # Process based on file type
        if is_video_file(file.filename):
            logger.info(f"Processing as video: {file.filename}")
            
            # Set output filename for video
            output_filename = f"censored_{file_id}_{file.filename}"
            output_path = UPLOAD_DIR / output_filename
            
            # Process video using yolo_e.py - import only when needed
            from scripts.yolo_e import run_video_censor, get_model
            model = get_model()  # Load model lazily
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
            
            # Process image using yolo_e.py - import only when needed
            from scripts.yolo_e import run_image_pixelate, get_model
            model = get_model()  # Load model lazily
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
        
        # Log memory usage after processing and cleanup
        try:
            import gc
            import psutil
            gc.collect()  # Force garbage collection
            process = psutil.Process()
            post_processing_memory = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"📊 Memory after processing: {post_processing_memory:.1f} MB")
        except ImportError:
            pass
        
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
        try:
            if input_path and input_path.exists():
                input_path.unlink()
                logger.info(f"Cleaned up input file: {input_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup input file: {cleanup_error}")
        
        try:
            if output_path and output_path.exists():
                output_path.unlink()
                logger.info(f"Cleaned up output file: {output_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup output file: {cleanup_error}")
        
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
        
        # Delete the user from Supabase Auth (this requires service role key)
        try:
            # Use the admin client to delete the user from auth
            auth_response = supabase_config.client.auth.admin.delete_user(user_id)
            logger.info(f"Deleted user from Supabase Auth: {user_id}")
        except Exception as e:
            logger.warning(f"Error deleting user from Supabase Auth: {str(e)}")
            # Continue anyway - the data cleanup is more important
        
        logger.info(f"Successfully deleted account data for user {user_id}")
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting account")

# For local development only
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        # Increase limits for file uploads
        limit_max_requests=1000,
        limit_concurrency=1000,
        timeout_keep_alive=30
    )
