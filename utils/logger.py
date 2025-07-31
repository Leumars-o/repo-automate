# utils/logger.py
"""
Logging utilities for the smart contract automation system
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
import time
import json

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}

class ComponentLogger:
    """Enhanced logger for components with structured logging"""
    
    def __init__(self, name: str, logger: logging.Logger):
        self.name = name
        self.logger = logger
    
    def info(self, message: str, **kwargs):
        self._log_with_context('info', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context('error', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context('warning', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context('debug', message, **kwargs)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with additional context"""
        if kwargs:
            context = json.dumps(kwargs, default=str)
            full_message = f"[{self.name}] {message} | Context: {context}"
        else:
            full_message = f"[{self.name}] {message}"
        
        getattr(self.logger, level)(full_message)

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing and log the duration"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.logger.info(f"Performance: {operation} took {duration:.2f} seconds")
            del self.start_times[operation]
            return duration
        return None

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True,
    json_format: bool = False
) -> None:
    """Setup logging configuration"""
    
    # Create log directory if it doesn't exist
    if file_output:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    if json_format:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handlers = []
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        handlers.append(console_handler)
    
    # File handler
    if file_output:
        log_file = Path(log_dir) / "automation.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)
        
        # Error log file
        error_log_file = Path(log_dir) / "errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        handlers.append(error_handler)
    
    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Log the setup
    logging.info(f"Logging initialized - Level: {log_level}, Console: {console_output}, File: {file_output}")

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance"""
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    
    return _loggers[name]

def get_component_logger(name: str) -> ComponentLogger:
    """Get enhanced component logger"""
    logger = get_logger(name)
    return ComponentLogger(name, logger)

def get_performance_logger(name: str) -> PerformanceLogger:
    """Get performance logger"""
    logger = get_logger(f"{name}.performance")
    return PerformanceLogger(logger)

def log_system_info():
    """Log system information"""
    import platform
    logger = get_logger("system")
    
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Working Directory: {os.getcwd()}")

def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """Log exception with full traceback"""
    import traceback
    
    tb_str = traceback.format_exc()
    message = f"Exception in {context}: {str(exception)}\nTraceback:\n{tb_str}"
    logger.error(message)

def create_audit_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    """Create audit logger for important events"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    audit_logger = logging.getLogger(f"audit.{name}")
    audit_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    audit_logger.handlers.clear()
    
    # Create file handler for audit log
    audit_file = Path(log_dir) / f"audit_{name}.log"
    handler = RotatingFileHandler(
        audit_file,
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    
    # Detailed formatter for audit logs
    formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)
    
    return audit_logger

def silence_noisy_loggers():
    """Silence commonly noisy third-party loggers"""
    noisy_loggers = [
        'github',
        'urllib3',
        'requests',
        'git',
        'paramiko'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def setup_debug_logging():
    """Setup debug logging for troubleshooting"""
    setup_logging(
        log_level="DEBUG",
        console_output=True,
        file_output=True,
        json_format=False
    )
    
    # Don't silence loggers in debug mode
    logging.info("Debug logging enabled")

# Initialize logging with sane defaults
if not logging.getLogger().handlers:
    setup_logging()
    silence_noisy_loggers()