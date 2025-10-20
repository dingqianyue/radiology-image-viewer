# Radiology Image Viewer

A full-stack medical image processing platform that supports multi-modal medical images (2D PNG/JPG, DICOM, 3D NIfTI) with asynchronous processing, real-time status tracking, and multi-user session isolation.

---

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐
│   Next.js       │◄───────►│   FastAPI       │
│   Frontend      │  REST   │   Backend       │
│   (Port 3000)   │   API   │   (Port 8000)   │
└─────────────────┘         └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │   Celery        │
                            │   Worker        │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │   Redis         │
                            │   (Port 6379)   │
                            └─────────────────┘
```

### Technology Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Axios (HTTP client)
- @niivue/niivue (3D NIfTI visualization)

**Backend:**
- FastAPI (Python web framework)
- Celery (Distributed task queue)
- Redis (Message broker & result backend)
- Pillow (Image processing)
- `pydicom` (DICOM file handling)
- `numpy` (Numerical processing for DICOM)
- Pydantic (Data validation)

---

## Project Structure

```
radiology-image-viewer/
│
├── radiology-backend/                 # Backend service
│   ├── app/
│   │   ├── __init__.py                # Package initializer
│   │   ├── main.py                    # FastAPI application
│   │   ├── celery_app.py              # Celery configuration
│   │   ├── tasks.py                   # Async task definitions
│   │   └── models.py                  # Pydantic models
│   ├── uploads/                       # User-uploaded files (gitignored)
│   ├── venv/                          # Python virtual environment (gitignored)
│   └── requirements.txt               # Python dependencies
│
└── radiology-frontend/                # Frontend application
    ├── app/
    │   ├── components/
    │   │   ├── ImageUploader.tsx      # File upload component
    │   │   ├── JobStatus.tsx          # Status tracking component
    │   │   ├── SimpleImageViewer.tsx  # PNG/JPG viewer
    │   │   └── NiftiViewer.tsx        # 3D NIfTI viewer
    │   ├── layout.tsx                 # Root layout
    │   ├── page.tsx                   # Main page
    │   └── globals.css                # Global styles
    ├── public/                        # Static assets
    ├── next.config.js                 # Next.js configuration
    ├── package.json                   # Node dependencies
    ├── tsconfig.json                  # TypeScript configuration
    └── tailwind.config.ts             # Tailwind configuration
```

---

## Getting Started

### Prerequisites

- **Python 3.11+** (Check: `python3 --version`)
- **Node.js 18+** (Check: `node --version`)
- **Redis** (Install: `brew install redis` on Mac)
- **Git**

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/dingqianyue/radiology-image-viewer.git
cd radiology-image-viewer
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd radiology-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
# Open a new terminal
cd radiology-frontend

# Install dependencies (this will take ~5 minutes, please be patient)
npm install
```

#### 4. Start Redis

```bash
# Option 1: Run as background service (Mac)
brew services start redis

# Option 2: Run in terminal (any OS)
redis-server
```

---

## Running the Application

You need **4 terminal windows** running simultaneously:

### Terminal 1: Redis Server
```bash
redis-server
```
**Expected Output:** `Ready to accept connections`

---

### Terminal 2: Celery Worker
```bash
cd radiology-backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```
**Expected Output:** `celery@hostname ready.`

---

### Terminal 3: FastAPI Backend
```bash
cd radiology-backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
**Expected Output:** `Application startup complete.`

**Verify:** Open http://localhost:8000/docs (Swagger UI)

---

### Terminal 4: Next.js Frontend
```bash
cd radiology-frontend
npm run dev
```
**Expected Output:** `Ready in X.Xs`

**Open:** http://localhost:3000

---

## Scaling for 10× More Users
To handle ten times more users, the system should evolve from basic optimizations to a fully distributed, cloud-native design. In the short term, migrate the in-memory `jobs_db` to PostgreSQL or MongoDB with indexes on `user_id` and `job_id`, and use Redis for caching. Scale horizontally by running multiple Celery workers and FastAPI replicas behind an Nginx load balancer. Move file storage to S3 or similar object storage, serve files through a CDN, and automate cleanup of old data.

For medium-scale growth, switch from polling to WebSockets or Server-Sent Events for real-time communication. Apply Redis-based rate limiting, request queueing, and circuit breakers to manage traffic spikes. Improve database performance with sharding, read replicas, and connection pooling via pgBouncer.

At large scale, transition to a microservices architecture with separate services for API, jobs, processing, and storage, connected through Kafka or RabbitMQ. Use Kubernetes for orchestration and auto-scaling, with multi-region deployments for global reach. Add GPU-powered workers for heavy processing and adopt distributed file systems like GlusterFS or Ceph. Finally, use spot instances for cost-effective scaling and efficient resource utilization.

---
## Testing

### Manual Testing

1. **Single Image Upload**
   ```bash
   curl -X POST http://localhost:8000/jobs \
     -H "X-User-ID: test-user" \
     -F "files=@test-image.png"
   ```

2. **Check Job Status**
   ```bash
   curl http://localhost:8000/jobs/{job_id} \
     -H "X-User-ID: test-user"
   ```

3. **Test Multi-User Isolation**
   - Upload as user "alice"
   - Try to access alice's job as user "bob" (should return 404)

### Automated Testing (Future Enhancement)
```bash
# Backend tests
cd radiology-backend
pytest

# Frontend tests
cd radiology-frontend
npm test
```

---

## Monitoring

### Current Implementation
- Celery logs for task execution
- FastAPI automatic logs
- Browser console for frontend errors

### Production Recommendations

1. **Metrics** (Prometheus + Grafana)
   ```python
   # Metrics to track:
   - queue_depth: Number of pending tasks
   - worker_active_tasks: Currently processing
   - task_latency_seconds: P50, P95, P99
   - api_request_rate: Requests per second
   - error_rate: Failed tasks percentage
   ```

2. **Logging** (ELK Stack or CloudWatch)
   - Centralized log aggregation
   - Structured JSON logging
   - Log levels: DEBUG, INFO, WARNING, ERROR

3. **Tracing** (Jaeger or OpenTelemetry)
   - Distributed request tracing
   - Performance bottleneck identification

4. **Alerting**
   - High error rate (>5%)
   - Queue depth exceeding threshold (>1000)
   - Worker downtime
   - API response time >2s

---

## API Documentation

### Endpoints

#### `POST /jobs`
Submit image processing job(s)

**Headers:**
- `X-User-ID`: string (required) - User identifier for isolation

**Body:**
- `files`: file[] (multipart/form-data)

**Response:**
```json
{
  "job_id": "uuid",
  "user_id": "string",
  "status": "PENDING",
  "task_ids": ["task-id-1", "task-id-2"],
  "created_at": "ISO-8601 timestamp"
}
```

---

#### `GET /jobs/{job_id}`
Query job status and results

**Headers:**
- `X-User-ID`: string (required)

**Response:**
```json
{
  "job_id": "uuid",
  "status": "SUCCESS",
  "progress": 100,
  "task_results": [
    {
      "task_id": "string",
      "status": "SUCCESS",
      "progress": 100,
      "result": {
        "input_file": "path",
        "output_file": "path",
        "task_type": "blur"
      }
    }
  ]
}
```

**Status Values:** `PENDING` → `RUNNING` → `SUCCESS` / `FAILED`

---

#### `GET /files/{user_id}/{job_id}/{filename}`
Download processed file

**Returns:** File stream

---

#### `GET /tasks/{task_id}`
Query individual task status

**Response:**
```json
{
  "task_id": "string",
  "status": "SUCCESS",
  "progress": 100,
  "result": {...}
}
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Must be 3.11+

# Check if port 8000 is in use
lsof -i :8000
```

### Celery worker fails
```bash
# Check Redis connection
redis-cli ping  # Should return PONG

# Use solo pool on Mac
celery -A app.celery_app worker --pool=solo
```

### Frontend can't connect to backend
- Verify backend is running: http://localhost:8000/docs
- Check CORS settings in `app/main.py`
- Disable browser extensions (ad blockers)

### Images not processing
- Check Celery worker logs
- Verify uploads/ directory exists and is writable
- Check file size and format
