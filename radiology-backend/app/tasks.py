from app.celery_app import celery_app
from PIL import Image, ImageFilter, ImageOps
import time
from pathlib import Path
import logging
import pydicom
import numpy as np
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def open_image(file_path: str) -> Image.Image:
    """
    Open an image file, with special handling for DICOM.
    """
    file_path_obj = Path(file_path)
    
    # Use .lower() to catch .dcm, .DCM, etc.
    if file_path_obj.suffix.lower() == '.dcm':
        logger.info(f"Opening DICOM file: {file_path}")
        try:
            # Read DICOM file
            ds = pydicom.dcmread(file_path)
            pixel_array = ds.pixel_array
            
            logger.info(f"Original DICOM array shape: {pixel_array.shape}")

            # If the array is 3D (e.g., (96, 512, 512)), pick the middle slice
            if pixel_array.ndim == 3:
                middle_slice_index = pixel_array.shape[0] // 2
                pixel_array = pixel_array[middle_slice_index, :, :]
                logger.info(f"Picked middle slice {middle_slice_index}, new shape: {pixel_array.shape}")

            # Squeeze the array to remove single-dimensional entries (e.g., from (1, 1, 512) to (512,))
            pixel_array = np.squeeze(pixel_array)
            
            # If the array is 1D (like shape (512,)), reshape it to 2D (1, 512)
            if pixel_array.ndim == 1:
                logger.warning(f"Squeezed array is 1D, reshaping to 2D (1, {pixel_array.shape[0]})")
                pixel_array = pixel_array.reshape((1, pixel_array.shape[0]))
            
            logger.info(f"Final array shape before normalization: {pixel_array.shape}")

            # Normalize pixel data to 0-255
            pixel_array = pixel_array.astype(float)
            
            # Check for max value to avoid division by zero
            max_val = pixel_array.max()
            if max_val == 0:
                max_val = 1 # Avoid division by zero if image is all black
                
            rescaled_array = (np.maximum(pixel_array, 0) / max_val) * 255.0
            final_array = np.uint8(rescaled_array)
            
            # Create PIL Image
            img = Image.fromarray(final_array)
            
            # Handle inverted monochrome images
            if ds.PhotometricInterpretation == "MONOCHROME1":
                img = ImageOps.invert(img)
                
            return img
        except Exception as e:
            error_msg = f"Failed to open DICOM image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    else:
        logger.info(f"Opening standard image file: {file_path}")
        try:
            img = Image.open(file_path)
            # Ensure image is in a mode that supports filters (like RGB)
            if img.mode in ('P', 'RGBA'):
                 img = img.convert('RGB')
            elif img.mode == 'L':
                 # Grayscale is fine
                 pass
            elif img.mode not in ('RGB', 'L'):
                 img = img.convert('RGB')

            logger.info(f"Task: Image opened successfully. Size: {img.size}, Mode: {img.mode}")
            return img
        except Exception as e:
            error_msg = f"Failed to open standard image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)

@celery_app.task(bind=True, name="app.tasks.process_image")
def process_image(self, file_path: str, task_type: str = "blur"):
    """
    Process an image file.
    """
    logger.info(f"Starting task {self.request.id} for file: {file_path} with type: {task_type}")
    
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        file_suffix = file_path_obj.suffix.lower()
        # Handle double extension .nii.gz
        if file_suffix == '.gz' and file_path_obj.stem.endswith('.nii'):
             file_suffix = '.nii.gz'

        if file_suffix in ['.nii', '.nii.gz']:
            logger.info(f"NIfTI file detected ({file_suffix}). Skipping processing, just copying.")
            # Define an "output" path (same directory, similar name pattern)
            # Keep the original extension
            output_path = file_path_obj.parent / f"{file_path_obj.stem.replace('.nii','')}_processed{file_suffix}"

            # Copy the original file to the output path
            try:
                shutil.copy(file_path_obj, output_path)
                logger.info(f"Task {self.request.id}: NIfTI file copied successfully to {output_path}")
                # Update progress quickly
                self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Copying file...'})
                time.sleep(0.5) # Short delay
                self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Copy complete'})

                result = {
                    "status": "SUCCESS",
                    "input_file": file_path,
                    "output_file": str(output_path), # Path to the *copied* NIfTI file
                    "task_type": "copy", # Indicate no processing was done
                    "message": "Successfully copied NIfTI file."
                }
                logger.info(f"Task {self.request.id}: Completed successfully (NIfTI copy)")
                return result

            except Exception as e:
                error_msg = f"Failed to copy NIfTI file: {str(e)}"
                logger.error(error_msg)
                raise IOError(error_msg)

        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Starting processing...'}
        )
        logger.info(f"Task {self.request.id}: State updated to PROGRESS")
        
        time.sleep(1)
        
        logger.info(f"Task {self.request.id}: Opening image {file_path}")
        img = open_image(file_path)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'status': 'Processing image...'}
        )
        
        logger.info(f"Task {self.request.id}: Applying {task_type} filter")
        
        if img.mode == 'I':
            img = img.convert('L') 

        if task_type == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
        elif task_type == "resize":
            if img.height > 1:
                img = img.resize((512, 512))
        elif task_type == "grayscale":
            if img.mode != 'L':
                img = img.convert('L')
        else:
            logger.warning(f"Unknown task type {task_type}, defaulting to blur")
            img = img.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Force the output to be a .png file for web compatibility
        output_path = file_path_obj.parent / f"{file_path_obj.stem}_processed.png"
        logger.info(f"Task {self.request.id}: Saving to {output_path}")
        
        try:
            img.save(output_path, "PNG") 
            logger.info(f"Task {self.request.id}: Image saved successfully as PNG")
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
            "output_file": str(output_path), # Path to the processed .png
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
        
        raise
