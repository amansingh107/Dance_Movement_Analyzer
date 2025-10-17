# app/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path
from typing import Optional
import logging
import traceback

from app.video_processor import DanceMovementAnalyzer, VideoProcessingError

# Initialize FastAPI app
app = FastAPI(
    title="Dance Movement Analysis API",
    description="AI ML Server for analyzing body movements in dance videos",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Maximum upload size (100MB)
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Dance Movement Analysis API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "upload": "/api/analyze (POST)",
            "download": "/api/download/{job_id} (GET)",
            "cleanup": "/api/cleanup/{job_id} (DELETE)",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dance-movement-analyzer",
        "upload_dir_writable": os.access(UPLOAD_DIR, os.W_OK),
        "output_dir_writable": os.access(OUTPUT_DIR, os.W_OK)
    }

@app.post("/api/analyze")
async def analyze_dance_video(
    video: UploadFile = File(..., description="Dance video file (mp4, avi, mov)")
):
    """
    Upload and analyze a dance video with comprehensive error handling
    
    Args:
        video: Video file to analyze
    
    Returns:
        Analysis results with job ID for downloading processed video
    """
    job_id = None
    input_path = None
    output_path = None
    
    try:
        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.MP4', '.AVI', '.MOV']
        file_extension = os.path.splitext(video.filename)[1]
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{file_extension}'. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(video.filename)
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('_', '-', '.'))
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Define paths
        input_path = UPLOAD_DIR / f"{job_id}_input{file_extension}"
        output_path = OUTPUT_DIR / f"{job_id}_output.mp4"
        
        logger.info(f"Processing upload: {safe_filename} (Job: {job_id})")
        
        # Save uploaded file with size check
        file_size = 0
        with input_path.open("wb") as buffer:
            while chunk := await video.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)
                if file_size > MAX_UPLOAD_SIZE:
                    buffer.close()
                    input_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024*1024)}MB"
                    )
                buffer.write(chunk)
        
        logger.info(f"File saved: {file_size / (1024*1024):.2f}MB")
        
        # Initialize analyzer and process video
        analyzer = DanceMovementAnalyzer(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        # Process with retry logic
        result = analyzer.process_video_with_retry(
            str(input_path), 
            str(output_path),
            max_retries=2
        )
        
        # Add job information to result
        result['job_id'] = job_id
        result['original_filename'] = safe_filename
        result['download_url'] = f"/api/download/{job_id}"
        result['cleanup_url'] = f"/api/cleanup/{job_id}"
        
        logger.info(f"Processing successful: {job_id}")
        
        return JSONResponse(content=result, status_code=200)
    
    except VideoProcessingError as e:
        logger.error(f"Video processing error for job {job_id}: {str(e)}")
        # Cleanup on error
        if input_path and input_path.exists():
            input_path.unlink()
        if output_path and output_path.exists():
            output_path.unlink()
        
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Video Processing Error",
                "message": str(e),
                "job_id": job_id
            }
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error for job {job_id}: {str(e)}\n{traceback.format_exc()}")
        
        # Cleanup on error
        if input_path and input_path.exists():
            input_path.unlink()
        if output_path and output_path.exists():
            output_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred during processing",
                "job_id": job_id
            }
        )

@app.get("/api/download/{job_id}")
async def download_processed_video(job_id: str):
    """Download processed video by job ID"""
    # Sanitize job_id
    safe_job_id = "".join(c for c in job_id if c.isalnum() or c == '-')
    
    output_path = OUTPUT_DIR / f"{safe_job_id}_output.mp4"
    
    if not output_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Video not found for job ID: {safe_job_id}"
        )
    
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"analyzed_{safe_job_id}.mp4"
    )

@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Delete uploaded and processed files for a job"""
    safe_job_id = "".join(c for c in job_id if c.isalnum() or c == '-')
    
    deleted_files = []
    
    # Find and delete input files
    for input_file in UPLOAD_DIR.glob(f"{safe_job_id}_input.*"):
        try:
            input_file.unlink()
            deleted_files.append(str(input_file))
        except Exception as e:
            logger.warning(f"Could not delete {input_file}: {str(e)}")
    
    # Delete output file
    output_file = OUTPUT_DIR / f"{safe_job_id}_output.mp4"
    if output_file.exists():
        try:
            output_file.unlink()
            deleted_files.append(str(output_file))
        except Exception as e:
            logger.warning(f"Could not delete {output_file}: {str(e)}")
    
    return {
        "job_id": safe_job_id,
        "deleted_files": deleted_files,
        "count": len(deleted_files)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
