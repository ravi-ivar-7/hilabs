import os
import hashlib
from typing import Optional, Tuple
from fastapi import UploadFile
from ..core.config import settings


def validate_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """Validate uploaded file"""
    
    # Check file type
    if file.content_type not in settings.allowed_file_types:
        return False, f"Invalid file type. Allowed types: {', '.join(settings.allowed_file_types)}"
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        return False, "File must have .pdf extension"
    
    return True, None


def validate_file_size(file_size: int) -> Tuple[bool, Optional[str]]:
    """Validate file size"""
    if file_size > settings.max_file_size:
        max_mb = settings.max_file_size / (1024 * 1024)
        return False, f"File size exceeds maximum limit of {max_mb}MB"
    
    return True, None


def validate_state(state: str) -> Tuple[bool, Optional[str]]:
    """Validate contract state"""
    if state.upper() not in settings.allowed_states:
        return False, f"Invalid state. Allowed states: {', '.join(settings.allowed_states)}"
    
    return True, None


def generate_file_hash(content: bytes) -> str:
    """Generate SHA256 hash of file content"""
    return hashlib.sha256(content).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    return filename


def get_bucket_name(state: str) -> str:
    """Get storage bucket name based on state"""
    return f"contracts-{state.lower()}"


def generate_storage_path(contract_id: str, filename: str) -> str:
    """Generate storage object path"""
    sanitized_filename = sanitize_filename(filename)
    return f"{contract_id}_{sanitized_filename}"
