from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class JobResponse(BaseModel):
    job_id: str
    user_id: str
    status: TaskStatus
    task_ids: List[str]
    created_at: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: TaskStatus
    progress: int  # 0-100
    task_results: List[dict]
    message: Optional[str] = None
