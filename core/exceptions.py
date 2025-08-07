# Custom Exceptions

class AutomationError(Exception):
    """Base exception for automation errors"""
    pass

class ConfigurationError(AutomationError):
    """Raised when configuration is invalid"""
    pass

class GitHubError(AutomationError):
    """Raised when GitHub operations fail"""
    pass

class ContractError(AutomationError):
    """Raised when smart contract operations fail"""
    pass

class ClaudeError(AutomationError):
    """Raised when Claude Code operations fail"""
    pass

class GitError(Exception):
    """Exception raised for Git operation errors"""
    
    def __init__(self, message: str, command: str = None, returncode: int = None):
        self.message = message
        self.command = command
        self.returncode = returncode
        super().__init__(self.message)
    
    def __str__(self):
        if self.command and self.returncode is not None:
            return f"Git command failed: {self.command} (exit code: {self.returncode}) - {self.message}"
        return f"Git operation failed: {self.message}"