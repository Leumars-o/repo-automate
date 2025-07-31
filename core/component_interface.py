# Component Interface

from typing import Protocol, Any, Dict

class ComponentInterface(Protocol):
    """Protocol defining the interface for all components"""
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute the component's main functionality"""
        ...
    
    def cleanup(self) -> None:
        """Clean up resources"""
        ...
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status"""
        ...