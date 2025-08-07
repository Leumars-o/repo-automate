# components/github_manager.py
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
        self.forced_token_index = None  # NEW: For forcing specific token usage
        
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
            # Validate token index
            if token_index < 0 or token_index >= len(self.tokens):
                raise GitHubError(f"Invalid token index {token_index}. Available indices: 0-{len(self.tokens)-1}")
            
            self.log_info(f"Manual token index set to: {token_index}")
    
    def force_token_index(self, token_index: int) -> None:
        """Force a specific token index to be used immediately"""
        if token_index < 0 or token_index >= len(self.tokens):
            raise GitHubError(f"Invalid token index {token_index}. Available indices: 0-{len(self.tokens)-1}")
        
        self.forced_token_index = token_index
        self.current_token_index = token_index
        self.log_info(f"Forced token index to: {token_index}")
    
    def get_next_token_index(self, project_name: str = None) -> int:
        """Get the next available token index based on usage and availability"""
        # If forced_token_index is set, always use it
        if self.forced_token_index is not None:
            self.current_token_index = self.forced_token_index
            self.log_info(f"Using forced token index {self.forced_token_index} for project: {project_name or 'unknown'}")
            return self.forced_token_index
        
        # Use manual token index if set
        if self.manual_token_index is not None:
            self.current_token_index = self.manual_token_index
            self.log_info(f"Using manual token index {self.manual_token_index} for project: {project_name or 'unknown'}")
            return self.manual_token_index
        
        # Otherwise, use state tracker for intelligent selection
        token_index = self.state_tracker.get_next_available_token_index(
            self.tokens, 
            None  # No manual override in this case
        )
        
        self.current_token_index = token_index
        self.log_info(f"Selected token index {token_index} for project: {project_name or 'unknown'}")
        
        return token_index
    
    def _get_current_token(self) -> str:
        """Get the current active token"""
        if not self.tokens:
            raise GitHubError("No GitHub tokens available")
        
        # Use forced token index if set
        if self.forced_token_index is not None:
            if self.forced_token_index >= len(self.tokens):
                raise GitHubError(f"Forced token index {self.forced_token_index} out of range")
            return self.tokens[self.forced_token_index]
        
        # Use manual token index if set
        if self.manual_token_index is not None:
            if self.manual_token_index >= len(self.tokens):
                raise GitHubError(f"Manual token index {self.manual_token_index} out of range")
            return self.tokens[self.manual_token_index]
        
        # Use current token index
        if self.current_token_index >= len(self.tokens):
            self.current_token_index = 0
        
        return self.tokens[self.current_token_index]
    
    def _get_effective_token_index(self) -> int:
        """Get the effective token index being used"""
        if self.forced_token_index is not None:
            return self.forced_token_index
        if self.manual_token_index is not None:
            return self.manual_token_index
        return self.current_token_index
    
    def _create_authenticated_url(self, repo_url: str) -> str:
        """Convert clone URL to authenticated URL with token"""
        try:
            token = self._get_current_token()
            
            # Extract repo info from clone URL
            # From: https://github.com/user/repo.git
            # To: https://TOKEN@github.com/user/repo.git
            
            if repo_url.startswith('https://github.com/'):
                # Remove the https:// prefix
                repo_path = repo_url[8:]  # Remove 'https://'
                # Create authenticated URL
                authenticated_url = f"https://{token}@{repo_path}"
                
                self.log_info(f"Created authenticated URL for push operations")
                return authenticated_url
            else:
                self.log_warning(f"Unexpected repo URL format: {repo_url}")
                return repo_url
                
        except Exception as e:
            self.log_error(f"Failed to create authenticated URL: {str(e)}")
            return repo_url
    
    def rotate_token(self, project_name: str = None, force: bool = False) -> None:
        """Rotate to next available token"""
        # Don't rotate if forced_token_index is set unless forced
        if self.forced_token_index is not None and not force:
            self.log_info("Forced token index set - rotation disabled")
            return
            
        if len(self.tokens) <= 1 and not force:
            self.log_info("Only one token available, skipping rotation")
            return
        
        old_index = self.current_token_index
        
        # Get next available token (excluding manual override for rotation)
        temp_manual = self.manual_token_index
        temp_forced = self.forced_token_index
        self.manual_token_index = None  # Clear manual override for rotation
        self.forced_token_index = None   # Clear forced override for rotation
        
        new_index = self.state_tracker.get_next_available_token_index(self.tokens)
        
        # Restore overrides
        self.manual_token_index = temp_manual
        self.forced_token_index = temp_forced
        
        self.current_token_index = new_index
        
        self.log_info(f"Token rotated from index {old_index} to {new_index} for project: {project_name or 'batch'}")
    
    def record_token_usage(self, project_name: str, success: bool = True, error: str = None) -> None:
        """Record token usage in state tracker"""
        effective_index = self._get_effective_token_index()
        self.state_tracker.record_token_usage(
            effective_index,
            self.tokens,
            project_name,
            success,
            error
        )
    
    def create_repository(self, project: Dict[str, Any]) -> str:
        """Create GitHub repository and return authenticated clone URL"""
        try:
            from github import Github
            
            project_name = project['name']
            description = project.get('description', f'Smart contract project: {project_name}')
            
            # Get current token and log which index is being used
            token = self._get_current_token()
            effective_index = self._get_effective_token_index()
            self.log_info(f"Using token index {effective_index} for repository creation")
            
            client = Github(token)
            
            # Get authenticated user
            user = client.get_user()
            
            # Check if repo already exists
            try:
                existing_repo = user.get_repo(project_name)
                repo_url = existing_repo.clone_url
                self.log_info(f"Repository {project_name} already exists: {repo_url}")
                
                # Return authenticated URL for existing repo
                return self._create_authenticated_url(repo_url)
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
            
            # Return authenticated URL for new repo
            return self._create_authenticated_url(repo_url)
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Failed to create repository {project_name}: {error_msg}")
            
            # Record failed token usage
            self.record_token_usage(project_name, success=False, error=error_msg)
            
            raise GitHubError(f"Failed to create repository: {error_msg}")
    
    def create_pull_request(self, project: Dict[str, Any], branch_name: str = None, 
                          source_branch: str = None, base_branch: str = "main") -> str:
        """Create pull request - supports both branch_name and source_branch parameters"""
        try:
            from github import Github
            
            project_name = project['name']
            token = self._get_current_token()
            effective_index = self._get_effective_token_index()
            self.log_info(f"Using token index {effective_index} for pull request creation")
            
            client = Github(token)
            
            user = client.get_user()
            repo = user.get_repo(project_name)
            
            # Handle parameter compatibility - branch_name or source_branch
            if branch_name is not None:
                source_branch = branch_name
            elif source_branch is None:
                source_branch = "main"
            
            # If source and target are the same, we need to create a feature branch first
            if source_branch == base_branch:
                self.log_warning(f"Source and target branches are the same ({source_branch}), this may not create a proper PR")
            
            # Create pull request
            title = f"Add {project_name} smart contract"
            body = f"""# {project_name} Smart Contract

This pull request adds the smart contract implementation for {project_name}.

## Changes
- Added smart contract code
- Added project configuration
- Compiled and tested successfully

## Generated by
Smart Contract Automation System using token index {effective_index}
"""
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=source_branch,
                base=base_branch
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
    
    def get_user_info(self, token_index: Optional[int] = None) -> Dict[str, str]:
        """Get current GitHub user information"""
        try:
            from github import Github
            
            # Use specified token index, or current effective token
            if token_index is not None:
                if token_index < 0 or token_index >= len(self.tokens):
                    raise GitHubError(f"Invalid token index {token_index}")
                token = self.tokens[token_index]
                effective_index = token_index
            else:
                token = self._get_current_token()
                effective_index = self._get_effective_token_index()
            
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
            
            self.log_info(f"Retrieved GitHub user info for: {user_info['login']} (token index: {effective_index})")
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
                self.get_user_info(token_index)
            else:
                self.get_user_info()
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
            'get_available_tokens': self.get_available_tokens,
            'set_manual_token': self.set_manual_token_index,
            'force_token': self.force_token_index  # NEW operation
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
        effective_index = self._get_effective_token_index()
        
        return {
            'total_tokens': len(self.tokens),
            'current_token_index': self.current_token_index,
            'effective_token_index': effective_index,
            'available_tokens': len(available_tokens),
            'available_token_indices': available_tokens,
            'manual_token_override': self.manual_token_index,
            'forced_token_override': self.forced_token_index,
            'state_summary': summary
        }