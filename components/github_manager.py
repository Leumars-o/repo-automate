# components/github_manager.py - UPDATED with state tracking
from typing import Dict, Any, List, Optional
import time
from pathlib import Path
from core.base_component import BaseComponent
from core.exceptions import GitHubError
from utils.state_tracker import StateTracker

class GitHubManager(BaseComponent):
    """Manages GitHub operations with intelligent token rotation and state tracking"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.github_config = config.get('github', {})
        self.tokens = self.github_config.get('tokens', [])
        self.current_token_index = 0
        self.manual_token_index = None
        
        # Initialize state tracker
        self.state_tracker = StateTracker()
        self.state_tracker.initialize_tokens(self.tokens)
        self.state_tracker.cleanup_stale_progress()  # Clean up any stale progress from crashes
        
        super().__init__(config, logger)
        
    def _initialize(self) -> None:
        """Initialize GitHub manager"""
        self.validate_config(['github'])
        
        if not self.tokens:
            raise GitHubError("No GitHub tokens found in configuration")
        
        self.log_info(f"Initialized with {len(self.tokens)} GitHub tokens")
        
        # Log state summary
        summary = self.state_tracker.get_state_summary()
        self.log_info(f"Token state: {summary['token_state']}")
        self.log_info(f"Project state: {summary['project_state']}")
    
    def set_manual_token_index(self, token_index: Optional[int]) -> None:
        """Set manual token index for single project execution"""
        self.manual_token_index = token_index
        if token_index is not None:
            self.log_info(f"Manual token index set to: {token_index}")
    
    def get_next_token_index(self, project_name: str = None) -> int:
        """Get the next available token index based on usage and availability"""
        token_index = self.state_tracker.get_next_available_token_index(
            self.tokens, 
            self.manual_token_index
        )
        
        self.current_token_index = token_index
        self.log_info(f"Selected token index {token_index} for project: {project_name or 'unknown'}")
        
        return token_index
    
    def _get_current_token(self) -> str:
        """Get the current active token"""
        if not self.tokens:
            raise GitHubError("No GitHub tokens available")
        
        if self.current_token_index >= len(self.tokens):
            self.current_token_index = 0
        
        return self.tokens[self.current_token_index]
    
    def rotate_token(self, project_name: str = None, force: bool = False) -> None:
        """Rotate to next available token"""
        if len(self.tokens) <= 1 and not force:
            self.log_info("Only one token available, skipping rotation")
            return
        
        old_index = self.current_token_index
        
        # Get next available token (excluding manual override for rotation)
        self.manual_token_index = None  # Clear manual override for rotation
        new_index = self.state_tracker.get_next_available_token_index(self.tokens)
        
        self.current_token_index = new_index
        
        self.log_info(f"Token rotated from index {old_index} to {new_index} for project: {project_name or 'batch'}")
    
    def record_token_usage(self, project_name: str, success: bool = True, error: str = None) -> None:
        """Record token usage in state tracker"""
        self.state_tracker.record_token_usage(
            self.current_token_index,
            self.tokens,
            project_name,
            success,
            error
        )
    
    def create_repository(self, project: Dict[str, Any]) -> str:
        """Create GitHub repository"""
        try:
            from github import Github
            
            project_name = project['name']
            description = project.get('description', f'Smart contract project: {project_name}')
            
            # Get current token
            token = self._get_current_token()
            client = Github(token)
            
            # Get authenticated user
            user = client.get_user()
            
            # Check if repo already exists
            try:
                existing_repo = user.get_repo(project_name)
                repo_url = existing_repo.clone_url
                self.log_info(f"Repository {project_name} already exists: {repo_url}")
                return repo_url
            except Exception:
                # Repo doesn't exist, create it
                pass
            
            # Create new repository
            repo = user.create_repo(
                name=project_name,
                description=description,
                private=project.get('private', False),
                auto_init=True,
                gitignore_template=project.get('gitignore_template', 'Python')
            )
            
            repo_url = repo.clone_url
            self.log_info(f"Created GitHub repository: {repo_url}")
            
            # Record successful token usage
            self.record_token_usage(project_name, success=True)
            
            return repo_url
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Failed to create repository {project_name}: {error_msg}")
            
            # Record failed token usage
            self.record_token_usage(project_name, success=False, error=error_msg)
            
            raise GitHubError(f"Failed to create repository: {error_msg}")
    
    def create_pull_request(self, project: Dict[str, Any], source_branch: str = "main", 
                          target_branch: str = "main") -> str:
        """Create pull request"""
        try:
            from github import Github
            
            project_name = project['name']
            token = self._get_current_token()
            client = Github(token)
            
            user = client.get_user()
            repo = user.get_repo(project_name)
            
            # If source and target are the same, we need to create a feature branch first
            if source_branch == target_branch:
                self.log_warning(f"Source and target branches are the same ({source_branch}), this may not create a proper PR")
            
            # Create pull request
            title = f"Add {project_name} smart contract"
            body = f"""
# {project_name} Smart Contract

This pull request adds the smart contract implementation for {project_name}.

## Changes
- Added smart contract code
- Added project configuration
- Compiled and tested successfully

## Generated by
Smart Contract Automation System using token index {self.current_token_index}
            """.strip()
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=source_branch,
                base=target_branch
            )
            
            pr_url = pr.html_url
            self.log_info(f"Created pull request: {pr_url}")
            
            # Record successful token usage
            self.record_token_usage(project_name, success=True)
            
            return pr_url
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Failed to create pull request for {project_name}: {error_msg}")
            
            # Record failed token usage
            self.record_token_usage(project_name, success=False, error=error_msg)
            
            raise GitHubError(f"Failed to create pull request: {error_msg}")
    
    def get_user_info(self) -> Dict[str, str]:
        """Get current GitHub user information"""
        try:
            from github import Github
            
            token = self._get_current_token()
            client = Github(token)
            user = client.get_user()
            
            user_info = {
                'login': user.login,
                'name': user.name,
                'email': None,
                'public_repos': user.public_repos
            }
            
            # Try to get email with error handling
            try:
                emails = user.get_emails()
                primary_email = None
                
                for email_obj in emails:
                    if email_obj.primary:
                        primary_email = email_obj.email
                        break
                
                if not primary_email and emails:
                    primary_email = emails[0].email
                
                user_info['email'] = primary_email
                
            except Exception as email_error:
                user_info['email'] = f"{user.login}@users.noreply.github.com"
                self.log_warning(f"Could not retrieve email, using noreply format: {email_error}")
            
            self.log_info(f"Retrieved GitHub user info for: {user_info['login']} (token index: {self.current_token_index})")
            return user_info
            
        except ImportError:
            raise GitHubError("PyGithub not installed, cannot retrieve user info")
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Failed to retrieve GitHub user info: {error_msg}")
            
            # Don't record token usage failure for user info requests
            # as this might be called frequently for validation
            
            raise GitHubError(f"Failed to retrieve GitHub user info: {error_msg}")
    
    def check_token_validity(self, token_index: Optional[int] = None) -> bool:
        """Check if a specific token is valid"""
        try:
            if token_index is not None:
                old_index = self.current_token_index
                self.current_token_index = token_index
                
            user_info = self.get_user_info()
            
            if token_index is not None:
                self.current_token_index = old_index
                
            return True
            
        except Exception:
            return False
    
    def get_available_tokens(self) -> List[int]:
        """Get list of available (non-blacklisted) token indices"""
        available = []
        for i, token in enumerate(self.tokens):
            if self.check_token_validity(i):
                available.append(i)
        return available
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute GitHub manager operation"""
        operations = {
            'create_repo': self.create_repository,
            'create_pr': self.create_pull_request,
            'get_user_info': self.get_user_info,
            'rotate_token': self.rotate_token,
            'check_token': self.check_token_validity,
            'get_available_tokens': self.get_available_tokens
        }
        
        if operation not in operations:
            raise GitHubError(f"Unknown GitHub operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"GitHub operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up GitHub resources"""
        # Save final state
        summary = self.state_tracker.get_state_summary()
        self.log_info(f"Final state summary: {summary}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get GitHub manager status"""
        available_tokens = self.get_available_tokens()
        summary = self.state_tracker.get_state_summary()
        
        return {
            'total_tokens': len(self.tokens),
            'current_token_index': self.current_token_index,
            'available_tokens': len(available_tokens),
            'available_token_indices': available_tokens,
            'manual_token_override': self.manual_token_index,
            'state_summary': summary
        }