# components/__init__.py
"""Automation components"""

from .github_manager import GitHubManager
from .git_operations import GitOperations
from .claude_interface import ClaudeInterface
from .contract_manager import ContractManager
from .result_tracker import ResultTracker

__all__ = [
    'GitHubManager',
    'GitOperations',
    'ClaudeInterface',
    'ContractManager',
    'ResultTracker'
]
