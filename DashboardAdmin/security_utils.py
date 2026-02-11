
"""
Security utilities for file upload validation and other security checks
"""
import os
import mimetypes
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_size(file):
    """
    Validate uploaded file size
    """
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5242880)  # 5MB default
    
    if file.size > max_size:
        raise ValidationError(f'File size cannot exceed {max_size / (1024 * 1024):.1f}MB')
    return file


def validate_image_file(file):
    """
    Validate uploaded image file for security
    - Check file extension
    - Check MIME type
    - Check file size
    """
    # Get allowed extensions from settings
    allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', 
                                 ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'])
    
    # Check file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
        )
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(file.name)
    if mime_type and not mime_type.startswith('image/'):
        raise ValidationError('File must be an image')
    
    # Validate file size
    validate_file_size(file)
    
    return file


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other attacks
    """
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Remove any null bytes
    filename = filename.replace('\x00', '')
    
    # Replace spaces and special characters
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def validate_content_type(file, allowed_types):
    """
    Validate file content type
    """
    if hasattr(file, 'content_type'):
        if file.content_type not in allowed_types:
            raise ValidationError(f'Invalid content type: {file.content_type}')
    return file
