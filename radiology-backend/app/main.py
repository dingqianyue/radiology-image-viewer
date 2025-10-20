from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import uuid
from datetime import datetime
from pathlib import Path
import shutil
import logging

from app.models import JobResponse, JobStatusResponse, TaskStatus
from app.tasks import process_image
from app.celery_app import celery_app as celery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Radiology Image Processing API",
    description="API for processing medical images",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
jobs_db = {}

def get_task_status(task_id: str):
    """Get status of a Celery task"""
    try:
        task = celery.AsyncResult(task_id)
        
        logger.info(f"Checking task {task_id}: state={task.state}, ready={task.ready()}")
        
        if task.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "PENDING",
                "progress": 0,
                "result": None
            }
        elif task.state == 'PROGRESS':
            info = task.info or {}
            return {
                "task_id": task_id,
                "status": "RUNNING",
                "progress": info.get('progress', 0),
                "result": None
            }
        elif task.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "progress": 100,
                "result": task.result
            }
        elif task.state == 'FAILURE':
            return {
                "task_id": task_id,
                "status": "FAILED",
                "progress": 0,
                "result": str(task.info) if task.info else "Unknown error"
            }
        else:  # Any other state (RETRY, REVOKED, etc.)
            logger.warning(f"Unknown task state: {task.state}")
            return {
                "task_id": task_id,
                "status": task.state,
                "progress": 0,
                "result": str(task.info) if task.info else None
            }
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "status": "FAILED",
            "progress": 0,
            "result": str(e)
        }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Radiology Image Processing API",
        "status": "running",
        "docs": "/docs"
    }

@app.post("/jobs", response_model=JobResponse)
async def create_job(
    files: List[UploadFile] = File(...),
    task_type: str = Form("blur"),
    x_user_id: str = Header(..., description="User ID for multi-user isolation")
):
    """
    Create a new image processing job
    """
    logger.info(f"Creating job for user {x_user_id} with {len(files)} files")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create user-specific directory
    user_dir = UPLOAD_DIR / x_user_id / job_id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    task_ids = []
    file_paths = []
    
    try:
        # Save files and submit tasks
        for file in files:
            # Save uploaded file
            file_path = user_dir / file.filename
            logger.info(f"Saving file to {file_path}")
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_paths.append(str(file_path))
            logger.info(f"File saved successfully: {file_path}")
            
            # Submit Celery task for processing
            logger.info(f"Submitting task for {file_path} with task_type={task_type}")
            task = process_image.delay(str(file_path), task_type=task_type)
            task_ids.append(task.id)
            logger.info(f"Task submitted with ID: {task.id}")
        
        # Store job metadata
        jobs_db[job_id] = {
            "job_id": job_id,
            "user_id": x_user_id,
            "status": TaskStatus.PENDING,
            "task_ids": task_ids,
            "created_at": datetime.utcnow().isoformat(),
            "files": [f.filename for f in files],
            "file_paths": file_paths
        }
        
        logger.info(f"Job {job_id} created successfully with {len(task_ids)} tasks")
        
        return JobResponse(
            job_id=job_id,
            user_id=x_user_id,
            status=TaskStatus.PENDING,
            task_ids=task_ids,
            created_at=jobs_db[job_id]["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    x_user_id: str = Header(..., description="User ID for multi-user isolation")
):
    """
    Get status of a job
    """
    # Check if job exists
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    # Multi-user isolation: verify user owns this job
    if job["user_id"] != x_user_id:
        raise HTTPException(
            status_code=404,
            detail="Job not found or you don't have permission to access it"
        )
    
    # Get status of all tasks
    task_results = []
    total_progress = 0
    all_success = True
    any_failed = False
    any_running = False
    
    for task_id in job["task_ids"]:
        task_status = get_task_status(task_id)
        task_results.append(task_status)
        total_progress += task_status["progress"]
        
        if task_status["status"] == "RUNNING":
            any_running = True
            all_success = False
        elif task_status["status"] == "FAILED":
            any_failed = True
            all_success = False
            logger.error(f"Task {task_id} failed: {task_status.get('result')}")
        elif task_status["status"] == "PENDING":
            all_success = False
    
    # Calculate overall job status
    if any_failed:
        overall_status = TaskStatus.FAILED
        message = f"Job failed. Error: {task_results[0].get('result', 'Unknown error')}"
    elif any_running:
        overall_status = TaskStatus.RUNNING
        message = "Processing..."
    elif all_success:
        overall_status = TaskStatus.SUCCESS
        message = "All tasks completed successfully"
    else:
        overall_status = TaskStatus.PENDING
        message = "Waiting to start..."
    
    # Update job status in database
    jobs_db[job_id]["status"] = overall_status
    
    # Calculate average progress
    avg_progress = total_progress // len(job["task_ids"]) if job["task_ids"] else 0
    
    return JobStatusResponse(
        job_id=job_id,
        status=overall_status,
        progress=avg_progress,
        task_results=task_results,
        message=message
    )

@app.get("/tasks/{task_id}")
async def get_task_status_endpoint(task_id: str):
    """Get status of a specific task"""
    return get_task_status(task_id)

@app.get("/files/{user_id}/{job_id}/{filename}")
async def get_file(user_id: str, job_id: str, filename: str):
    """
    Download a processed file
    """
    file_path = UPLOAD_DIR / user_id / job_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

# Debug endpoints
@app.get("/debug/jobs")
async def debug_list_jobs():
    """List all jobs (for debugging)"""
    return {"jobs": list(jobs_db.values())}

@app.get("/debug/celery")
async def debug_celery():
    """Check Celery connection"""
    try:
        # Test Celery connection
        result = celery.control.inspect().active()
        return {
            "status": "connected",
            "active_workers": result if result else "No active workers"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
