"""
Shared Helper Functions
Common utilities used across multiple modules
"""
import os
import logging
from typing import Dict, Any
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)

# Import constants
from app.constants import (
    IMAGE_FORMAT_RGB,
    TEMP_IMAGE_SUFFIX,
    TEMP_IMAGE_FORMAT
)


def create_error_response(filename: str, error_message: str) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        filename: Name of the file being processed
        error_message: Error description
        
    Returns:
        Standardized error response dictionary
    """
    return {
        'success': False,
        'error': error_message,
        'filename': filename
    }


def create_success_response(
    text: str,
    filename: str,
    file_type: str,
    extraction_method: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        text: Extracted text content
        filename: Name of the file being processed
        file_type: Type of file (image, pdf, docx, text)
        extraction_method: Method used for extraction
        metadata: Additional metadata about the extraction
        
    Returns:
        Standardized success response dictionary
    """
    return {
        'success': True,
        'text': text,
        'filename': filename,
        'file_type': file_type,
        'extraction_method': extraction_method,
        'metadata': metadata
    }


def ensure_rgb_image(image: Image.Image) -> Image.Image:
    """
    Ensure image is in RGB format (required by vision model)
    
    Args:
        image: PIL Image object
        
    Returns:
        Image converted to RGB if necessary
    """
    if image.mode != IMAGE_FORMAT_RGB:
        return image.convert(IMAGE_FORMAT_RGB)
    return image


def save_temp_image(image: Image.Image) -> str:
    """
    Save image to temporary file for Ollama processing
    
    Args:
        image: PIL Image to save
        
    Returns:
        Path to temporary file
    """
    tmp = tempfile.NamedTemporaryFile(suffix=TEMP_IMAGE_SUFFIX, delete=False)
    image.save(tmp.name, format=TEMP_IMAGE_FORMAT)
    return tmp.name


def cleanup_temp_file(file_path: str) -> None:
    """
    Safely remove temporary file
    
    Args:
        file_path: Path to file to remove
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")


def extract_model_name(model: Any) -> str:
    """
    Extract model name from various Ollama response formats
    
    Handles dicts, objects with attributes, tuples, and string conversion.
    This is necessary because Ollama's API response format varies by version.
    
    Args:
        model: Model object from Ollama response
        
    Returns:
        Model name as string
    """
    if isinstance(model, dict):
        return model.get('model', model.get('name', ''))
    elif hasattr(model, 'model'):
        return model.model
    elif hasattr(model, 'name'):
        return model.name
    else:
        return str(model)
