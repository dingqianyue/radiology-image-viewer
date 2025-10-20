from app.celery_app import celery_app
from PIL import Image, ImageFilter
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.process_image")
def process_image(self, file_path: str, task_type: str = "blur"):
    """
    Process an image file
    
    Args:
        file_path: Path to the image file
        task_type: Type of processing (blur, resize, grayscale)
    """
    logger.info(f"Starting task {self.request.id} for file: {file_path}")
    
    try:
        # Check if file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Update status to RUNNING
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Starting processing...'}
        )
        logger.info(f"Task {self.request.id}: State updated to PROGRESS")
        
        # Simulate some processing time
        time.sleep(1)
        
        # Open image
        logger.info(f"Task {self.request.id}: Opening image {file_path}")
        try:
            img = Image.open(file_path)
            logger.info(f"Task {self.request.id}: Image opened successfully. Size: {img.size}, Mode: {img.mode}")
        except Exception as e:
            error_msg = f"Failed to open image: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'status': 'Processing image...'}
        )
        
        # Process based on task type
        logger.info(f"Task {self.request.id}: Applying {task_type} filter")
        if task_type == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
        elif task_type == "resize":
            img = img.resize((512, 512))
        elif task_type == "grayscale":
            img = img.convert('L')
        else:
            logger.warning(f"Unknown task type {task_type}, defaulting to blur")
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Save processed image
        output_path = file_path_obj.parent / f"{file_path_obj.stem}_processed{file_path_obj.suffix}"
        logger.info(f"Task {self.request.id}: Saving to {output_path}")
        
        try:
            img.save(output_path)
            logger.info(f"Task {self.request.id}: Image saved successfully")
        except Exception as e:
            error_msg = f"Failed to save image: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 90, 'status': 'Saving results...'}
        )
        
        time.sleep(1)
        
        result = {
            "status": "SUCCESS",
            "input_file": file_path,
            "output_file": str(output_path),
            "task_type": task_type,
            "message": f"Successfully processed image with {task_type}"
        }
        
        logger.info(f"Task {self.request.id}: Completed successfully")
        return result
        
    except Exception as e:
        error_msg = f"Task failed: {str(e)}"
        logger.error(f"Task {self.request.id}: {error_msg}", exc_info=True)
        
        self.update_state(
            state='FAILURE',
            meta={'progress': 0, 'status': error_msg}
        )
        
        # Re-raise the exception so Celery marks the task as failed
        raise
