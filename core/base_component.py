# Base Component Class

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from utils.logger import get_logger

class BaseComponent(ABC):
    """Base class for all automation components"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or get_logger(self.__class__.__name__)
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize component-specific settings"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Main execution method for the component"""
        pass
    
    def validate_config(self, required_keys: list) -> None:
        """Validate that required configuration keys exist"""
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")
    
    def log_info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(f"[{self.__class__.__name__}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(f"[{self.__class__.__name__}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(f"[{self.__class__.__name__}] {message}")