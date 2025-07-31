# utils/helpers.py
"""
Helper functions and utilities for the smart contract automation system
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

def ensure_directory_exists(directory_path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_file_write(file_path: Union[str, Path], content: str, backup: bool = True) -> None:
    """Safely write content to file with optional backup"""
    path = Path(file_path)
    
    # Create backup if file exists and backup is requested
    if backup and path.exists():
        backup_path = path.with_suffix(f"{path.suffix}.backup.{int(time.time())}")
        backup_path.write_text(path.read_text())
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    path.write_text(content)

def safe_file_read(file_path: Union[str, Path], default: str = "") -> str:
    """Safely read file content with default fallback"""
    path = Path(file_path)
    try:
        return path.read_text() if path.exists() else default
    except Exception:
        return default

def get_file_hash(file_path: Union[str, Path]) -> str:
    """Get SHA256 hash of file content"""
    path = Path(file_path)
    if not path.exists():
        return ""
    
    hash_sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()

def get_timestamp(utc: bool = True) -> str:
    """Get formatted timestamp"""
    if utc:
        return datetime.now(timezone.utc).isoformat()
    else:
        return datetime.now().isoformat()

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"

def run_command(
    command: List[str], 
    cwd: Optional[str] = None, 
    timeout: int = 30,
    capture_output: bool = True
) -> Dict[str, Any]:
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=False
        )
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout if capture_output else "",
            'stderr': result.stderr if capture_output else "",
            'command': ' '.join(command)
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': "",
            'stderr': "Command timed out",
            'command': ' '.join(command)
        }
    
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': "",
            'stderr': str(e),
            'command': ' '.join(command)
        }

def check_tool_availability(tool_name: str) -> bool:
    """Check if a command-line tool is available"""
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    import platform
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'python_executable': sys.executable,
        'working_directory': os.getcwd(),
        'timestamp': get_timestamp()
    }

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext
    
    return filename

def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator to retry function on exception"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff_multiplier
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator

def is_valid_json(json_string: str) -> bool:
    """Check if string is valid JSON"""
    try:
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False

def load_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON file with error handling"""
    path = Path(file_path)
    
    if not path.exists():
        return default
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save_json_file(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """Save data to JSON file"""
    path = Path(file_path)
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=indent, default=str)
        return True
    except (TypeError, IOError):
        return False

def get_project_root() -> Path:
    """Get project root directory"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / 'main.py').exists() or (current / 'setup.py').exists():
            return current
        current = current.parent
    return Path.cwd()

def setup_project_structure(base_path: Union[str, Path]) -> Dict[str, Path]:
    """Setup standard project directory structure"""
    base = Path(base_path)
    
    directories = {
        'workspace': base / 'workspace',
        'results': base / 'results',
        'logs': base / 'logs',
        'config': base / 'config',
        'tests': base / 'tests'
    }
    
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
    
    return directories

def cleanup_old_files(directory: Union[str, Path], max_age_days: int = 7) -> int:
    """Clean up old files in directory"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return 0
    
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    cleaned_count = 0
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            except OSError:
                pass  # Skip files that can't be accessed
    
    return cleaned_count

def get_available_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    """Find an available port starting from start_port"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    return None

def generate_unique_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}" if prefix else unique_id

def validate_url(url: str) -> bool:
    """Validate URL format"""
    from urllib.parse import urlparse
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def rate_limit(calls_per_second: float):
    """Decorator to rate limit function calls"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def filter_dict_keys(d: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
    """Filter dictionary to only include allowed keys"""
    return {k: v for k, v in d.items() if k in allowed_keys}

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage information"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    except ImportError:
        return {'error': 'psutil not available'}

def print_progress_bar(
    iteration: int, 
    total: int, 
    prefix: str = '', 
    suffix: str = '', 
    length: int = 50,
    fill: str = '█'
) -> None:
    """Print progress bar to console"""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    if iteration == total:
        print()

class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"{self.description} took {format_duration(duration)}")
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class ConfigCache:
    """Simple configuration cache"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        self._cache.clear()
        self._timestamps.clear()
    
    def is_expired(self, key: str, max_age: float) -> bool:
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > max_age

# Create global instances
config_cache = ConfigCache()

# Export commonly used functions
__all__ = [
    'ensure_directory_exists',
    'safe_file_write',
    'safe_file_read',
    'get_file_hash',
    'get_timestamp',
    'format_duration',
    'format_file_size',
    'run_command',
    'check_tool_availability',
    'get_system_info',
    'merge_dicts',
    'flatten_dict',
    'sanitize_filename',
    'retry_on_exception',
    'is_valid_json',
    'load_json_file',
    'save_json_file',
    'get_project_root',
    'setup_project_structure',
    'cleanup_old_files',
    'get_available_port',
    'generate_unique_id',
    'validate_url',
    'rate_limit',
    'chunk_list',
    'filter_dict_keys',
    'get_memory_usage',
    'print_progress_bar',
    'Timer',
    'ConfigCache',
    'config_cache'
]