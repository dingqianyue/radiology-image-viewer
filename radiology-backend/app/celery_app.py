from celery import Celery

# Initialize Celery
celery_app = Celery(
    "radiology_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
)

from app import tasks
