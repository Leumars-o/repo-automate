from typing import Dict, Any, Optional, List
from github import Github
from github.Repository import Repository
from core.base_component import BaseComponent
from core.exceptions import GitHubError
import time

class GitHubManager(BaseComponent):
    """Handles all GitHub operations including repository management"""

    def __init__(self, config: Dict[str, Any], logger: Optional[Any] = None):
        # Initialize tokens and clients to None before calling super().__init__
        self.tokens = None
        self.github_clients = None
        self.current_client_index = 0
        
        # Now call parent initialization which will call _initialize()
        super().__init__(config, logger)

    def _initialize(self) -> None:
        """Initialize GitHub clients with tokens"""
        self.validate_config(['github'])
        
        # Get tokens from config
        github_config = self.config['github']
        tokens = github_config.get('tokens', [])
        
        if not tokens:
            raise GitHubError("No GitHub tokens provided in configuration")
        
        if not isinstance(tokens, list):
            tokens = [tokens]  # Convert single token to list
        
        self.tokens = tokens
        self.github_clients = []
        self.current_client_index = 0
        
        # Initialize GitHub clients for each token
        for i, token in enumerate(self.tokens):
            try:
                client = Github(token.strip())
                # Test the token by making a simple API call
                user = client.get_user()
                self.log_info(f"Initialized GitHub client {i+1} for user: {user.login}")
                self.github_clients.append(client)
            except Exception as e:
                self.log_error(f"Failed to initialize GitHub client with token {i+1}: {e}")
                # Continue with other tokens instead of failing completely
                continue
        
        if not self.github_clients:
            raise GitHubError("No valid GitHub clients could be initialized")
        
        self.log_info(f"Successfully initialized {len(self.github_clients)} GitHub client(s)")

    def get_current_client(self) -> Github:
        """Get the current GitHub client with rate limit rotation"""
        if not self.github_clients:
            raise GitHubError("No GitHub clients available")
        
        client = self.github_clients[self.current_client_index]
        
        # Check rate limit
        rate_limit = client.get_rate_limit()
        if rate_limit.core.remaining < 10:  # Switch if less than 10 requests remaining
            self.log_warning(f"Client {self.current_client_index + 1} rate limit low, switching clients")
            self._rotate_client()
            client = self.github_clients[self.current_client_index]
        
        return client

    def _rotate_client(self) -> None:
        """Rotate to the next available client"""
        if len(self.github_clients) > 1:
            self.current_client_index = (self.current_client_index + 1) % len(self.github_clients)
            self.log_info(f"Switched to GitHub client {self.current_client_index + 1}")

    def create_repository(self, repo_data: Dict[str, Any]) -> Repository:
        """Create a new GitHub repository"""
        try:
            client = self.get_current_client()
            user = client.get_user()
            
            repo_name = repo_data['name']
            description = repo_data.get('description', '')
            private = repo_data.get('private', False)
            
            self.log_info(f"Creating repository: {repo_name}")
            
            repo = user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=repo_data.get('auto_init', True),
                has_issues=repo_data.get('has_issues', True),
                has_projects=repo_data.get('has_projects', False),
                has_wiki=repo_data.get('has_wiki', False)
            )
            
            self.log_info(f"Successfully created repository: {repo.full_name}")
            return repo
            
        except Exception as e:
            error_msg = f"Failed to create repository {repo_data.get('name', 'unknown')}: {e}"
            self.log_error(error_msg)
            raise GitHubError(error_msg)

    def get_repository(self, repo_name: str) -> Optional[Repository]:
        """Get an existing repository"""
        try:
            client = self.get_current_client()
            user = client.get_user()
            
            repo = user.get_repo(repo_name)
            self.log_info(f"Retrieved repository: {repo.full_name}")
            return repo
            
        except Exception as e:
            self.log_warning(f"Repository {repo_name} not found or inaccessible: {e}")
            return None

    def delete_repository(self, repo_name: str) -> bool:
        """Delete a repository"""
        try:
            repo = self.get_repository(repo_name)
            if repo:
                repo.delete()
                self.log_info(f"Successfully deleted repository: {repo_name}")
                return True
            else:
                self.log_warning(f"Repository {repo_name} not found for deletion")
                return False
                
        except Exception as e:
            error_msg = f"Failed to delete repository {repo_name}: {e}"
            self.log_error(error_msg)
            raise GitHubError(error_msg)

    def create_file(self, repo_name: str, file_path: str, content: str, commit_message: str) -> bool:
        """Create a file in a repository"""
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                raise GitHubError(f"Repository {repo_name} not found")
            
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content
            )
            
            self.log_info(f"Created file {file_path} in {repo_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create file {file_path} in {repo_name}: {e}"
            self.log_error(error_msg)
            raise GitHubError(error_msg)

    def update_file(self, repo_name: str, file_path: str, content: str, commit_message: str) -> bool:
        """Update an existing file in a repository"""
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                raise GitHubError(f"Repository {repo_name} not found")
            
            # Get the current file to get its SHA
            file_obj = repo.get_contents(file_path)
            
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=file_obj.sha
            )
            
            self.log_info(f"Updated file {file_path} in {repo_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update file {file_path} in {repo_name}: {e}"
            self.log_error(error_msg)
            raise GitHubError(error_msg)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status for all clients"""
        status = {}
        
        for i, client in enumerate(self.github_clients):
            try:
                rate_limit = client.get_rate_limit()
                status[f"client_{i+1}"] = {
                    'remaining': rate_limit.core.remaining,
                    'limit': rate_limit.core.limit,
                    'reset_time': rate_limit.core.reset.isoformat()
                }
            except Exception as e:
                status[f"client_{i+1}"] = {'error': str(e)}
        
        return status

    def get_status(self) -> Dict[str, Any]:
        """Get overall GitHub manager status"""
        try:
            return {
                'clients_count': len(self.github_clients),
                'current_client': self.current_client_index + 1,
                'rate_limits': self.get_rate_limit_status(),
                'tokens_configured': len(self.tokens),
                'status': 'operational'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'clients_count': len(self.github_clients) if self.github_clients else 0
            }

    def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute a GitHub operation"""
        operations = {
            'create_repo': self.create_repository,
            'get_repo': self.get_repository,
            'delete_repo': self.delete_repository,
            'create_file': self.create_file,
            'update_file': self.update_file,
            'get_status': self.get_status,
            'get_rate_limit': self.get_rate_limit_status
        }
        
        if operation not in operations:
            raise GitHubError(f"Unknown operation: {operation}")
        
        return operations[operation](*args, **kwargs)