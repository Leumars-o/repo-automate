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