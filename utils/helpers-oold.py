# utils/helpers.py
"""
Helper utilities for the automation system
"""

import time
import hashlib
from typing import Dict, Any, List
from pathlib import Path

def generate_unique_id(project_name: str) -> str:
    """Generate unique ID for a project"""
    timestamp = str(int(time.time()))
    combined = f"{project_name}_{timestamp}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Truncate if too long
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def retry_operation(operation, max_retries: int = 3, delay: float = 1.0):
    """Retry operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))

def validate_project_config(project: Dict[str, Any]) -> bool:
    """Validate project configuration"""
    required_fields = ['name', 'description']
    
    for field in required_fields:
        if field not in project or not project[field]:
            return False
    
    return True

def ensure_directory_exists(path: str) -> Path:
    """Ensure directory exists, create if necessary"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
