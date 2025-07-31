# components/git_operations.py
from typing import Dict, Any, Optional
from git import Repo, GitCommandError
from pathlib import Path
import os
import shutil
from core.base_component import BaseComponent
from core.exceptions import AutomationError

class GitOperations(BaseComponent):
    """Handles all Git operations including cloning, branching, committing, and pushing"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.repos = {}  # Track active repositories
        self.base_workspace = Path(config.get('automation', {}).get('workspace', 'workspace'))
        super().__init__(config, logger)
        
    def _initialize(self) -> None:
        """Initialize Git operations"""
        self.validate_config(['automation'])
        self.base_workspace.mkdir(exist_ok=True)
        self.log_info(f"Workspace initialized at: {self.base_workspace}")
    
    def clone_repository(self, repo_url: str, project_name: str) -> str:
        """Clone a repository to local workspace"""
        try:
            project_path = self.base_workspace / project_name
            
            # Remove existing directory if it exists
            if project_path.exists():
                shutil.rmtree(project_path)
            
            # Clone repository
            repo = Repo.clone_from(repo_url, project_path)
            self.repos[project_name] = repo
            
            self.log_info(f"Cloned repository to: {project_path}")
            return str(project_path)
            
        except GitCommandError as e:
            raise AutomationError(f"Failed to clone repository '{repo_url}': {str(e)}")
    
    def setup_git_config(self, project_name: str, user_name: str, user_email: str) -> None:
        """Setup Git configuration for the project"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                raise AutomationError(f"Repository '{project_name}' not found")
            
            # Set local Git config
            with repo.config_writer() as git_config:
                git_config.set_value('user', 'name', user_name)
                git_config.set_value('user', 'email', user_email)
            
            self.log_info(f"Git config set for {project_name}: {user_name} <{user_email}>")
            
        except Exception as e:
            raise AutomationError(f"Failed to setup Git config for '{project_name}': {str(e)}")
    
    def create_branch(self, project_name: str, branch_name: str) -> None:
        """Create a new branch"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                raise AutomationError(f"Repository '{project_name}' not found")
            
            # Create new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            self.log_info(f"Created and switched to branch: {branch_name}")
            
        except Exception as e:
            raise AutomationError(f"Failed to create branch '{branch_name}': {str(e)}")
    
    def add_files(self, project_name: str, file_patterns: list = None) -> None:
        """Add files to staging area"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                raise AutomationError(f"Repository '{project_name}' not found")
            
            if file_patterns:
                for pattern in file_patterns:
                    repo.index.add([pattern])
            else:
                repo.git.add(A=True)  # Add all files
            
            self.log_info(f"Added files to staging area")
            
        except Exception as e:
            raise AutomationError(f"Failed to add files: {str(e)}")
    
    def commit_changes(self, project_name: str, commit_message: str) -> str:
        """Commit changes"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                raise AutomationError(f"Repository '{project_name}' not found")
            
            # Check if there are changes to commit
            if not repo.is_dirty() and not repo.untracked_files:
                self.log_info("No changes to commit")
                return None
            
            # Add all changes
            self.add_files(project_name)
            
            # Commit changes
            commit = repo.index.commit(commit_message)
            commit_hash = commit.hexsha[:8]
            
            self.log_info(f"Committed changes: {commit_hash} - {commit_message}")
            return commit_hash
            
        except Exception as e:
            raise AutomationError(f"Failed to commit changes: {str(e)}")
    
    def push_changes(self, project_name: str, branch_name: str = None) -> None:
        """Push changes to remote repository"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                raise AutomationError(f"Repository '{project_name}' not found")
            
            # Get current branch if not specified
            if not branch_name:
                branch_name = repo.active_branch.name
            
            # Push to remote
            origin = repo.remote('origin')
            origin.push(branch_name)
            
            self.log_info(f"Pushed changes to remote branch: {branch_name}")
            
        except Exception as e:
            raise AutomationError(f"Failed to push changes: {str(e)}")
    
    def get_project_path(self, project_name: str) -> str:
        """Get the local path for a project"""
        return str(self.base_workspace / project_name)
    
    def get_repo_status(self, project_name: str) -> Dict[str, Any]:
        """Get repository status"""
        try:
            repo = self.repos.get(project_name)
            if not repo:
                return {"error": f"Repository '{project_name}' not found"}
            
            return {
                "current_branch": repo.active_branch.name,
                "is_dirty": repo.is_dirty(),
                "untracked_files": len(repo.untracked_files),
                "modified_files": len(repo.git.diff('--name-only').splitlines()),
                "commits_ahead": len(list(repo.iter_commits('HEAD..origin/main'))),
                "commits_behind": len(list(repo.iter_commits('origin/main..HEAD')))
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_project(self, project_name: str) -> None:
        """Clean up project workspace"""
        try:
            project_path = self.base_workspace / project_name
            if project_path.exists():
                shutil.rmtree(project_path)
                self.log_info(f"Cleaned up project: {project_name}")
            
            # Remove from tracking
            if project_name in self.repos:
                del self.repos[project_name]
                
        except Exception as e:
            self.log_error(f"Failed to cleanup project '{project_name}': {str(e)}")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Git operation"""
        operations = {
            'clone': self.clone_repository,
            'setup_config': self.setup_git_config,
            'create_branch': self.create_branch,
            'add_files': self.add_files,
            'commit': self.commit_changes,
            'push': self.push_changes,
            'get_status': self.get_repo_status,
            'cleanup': self.cleanup_project
        }
        
        if operation not in operations:
            raise AutomationError(f"Unknown Git operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Git operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up all Git resources"""
        for project_name in list(self.repos.keys()):
            self.cleanup_project(project_name)
    
    def get_status(self) -> Dict[str, Any]:
        """Get Git operations status"""
        return {
            'workspace_path': str(self.base_workspace),
            'active_repos': list(self.repos.keys()),
            'total_repos': len(self.repos)
        }