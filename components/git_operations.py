# components/git_operations.py
from typing import Dict, Any, Optional
from git import Repo, GitCommandError
from pathlib import Path
import subprocess
import os
import shutil
from core.base_component import BaseComponent
from core.exceptions import AutomationError
from core.exceptions import GitError  


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
            
            # Return the relative path string (consistent with _get_workspace_path)
            return str(project_path)
            
        except GitCommandError as e:
            raise AutomationError(f"Failed to clone repository '{repo_url}': {str(e)}")
    
    def setup_git_config(self, project_name: str, user_name: str, user_email: str) -> None:
        """Setup Git configuration for the project"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            # Set local Git config using subprocess for better reliability
            result1 = subprocess.run(['git', 'config', 'user.name', user_name],
                                   cwd=workspace_path,
                                   capture_output=True, text=True)
            
            result2 = subprocess.run(['git', 'config', 'user.email', user_email],
                                   cwd=workspace_path,
                                   capture_output=True, text=True)
            
            if result1.returncode != 0 or result2.returncode != 0:
                raise GitError(f"Failed to set git config: {result1.stderr} {result2.stderr}")
            
            self.log_info(f"Git config set for {project_name}: {user_name} <{user_email}>")
            
        except Exception as e:
            raise GitError(f"Failed to setup Git config for '{project_name}': {str(e)}")
    
    def create_branch(self, project_name: str, branch_name: str) -> str:
        """Create and checkout a new branch"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            # Create and checkout new branch
            result = subprocess.run(['git', 'checkout', '-b', branch_name],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to create branch {branch_name}: {result.stderr}")
            
            self.log_info(f"Created and checked out branch: {branch_name}")
            return branch_name
            
        except Exception as e:
            raise GitError(f"Failed to create branch: {str(e)}")
        
    
    def add_files(self, project_name: str, file_patterns: list = None) -> None:
        """Add files to staging area"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            if file_patterns:
                for pattern in file_patterns:
                    result = subprocess.run(['git', 'add', pattern],
                                          cwd=workspace_path,
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        self.log_warning(f"Failed to add {pattern}: {result.stderr}")
            else:
                # Add all files
                result = subprocess.run(['git', 'add', '.'],
                                      cwd=workspace_path,
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise GitError(f"Failed to add files: {result.stderr}")
            
            self.log_info(f"Added files to staging area")
            
        except Exception as e:
            raise GitError(f"Failed to add files: {str(e)}")
    

    def get_current_branch(self, project_name: str) -> str:
        """Get current branch name"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to get current branch: {result.stderr}")
            
            return result.stdout.strip()
            
        except Exception as e:
            raise GitError(f"Failed to get current branch: {str(e)}")
        
    def switch_branch(self, project_name: str, branch_name: str) -> None:
        """Switch to an existing branch"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            result = subprocess.run(['git', 'checkout', branch_name],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to switch to branch {branch_name}: {result.stderr}")
            
            self.log_info(f"Switched to branch: {branch_name}")
            
        except Exception as e:
            raise GitError(f"Failed to switch branch: {str(e)}")

        
    def commit(self, project_name: str, commit_message: str) -> str:
        """Commit changes with enhanced workflow and better error handling"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            self.log_info(f"Committing changes in: {workspace_path}")
            
            # First, add all changes
            self.add_all_changes(project_name)
            
            # Check if there are changes to commit
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                        cwd=workspace_path,
                                        capture_output=True, text=True)
            
            if not status_result.stdout.strip():
                self.log_info("No changes to commit")
                return "no-changes"
            
            self.log_info(f"Changes detected:\n{status_result.stdout}")
            
            # Commit changes
            result = subprocess.run(['git', 'commit', '-m', commit_message],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to commit: {result.stderr}")
            
            # Get commit hash
            hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                    cwd=workspace_path,
                                    capture_output=True, text=True)
            
            commit_hash = hash_result.stdout.strip()[:8]  # Short hash
            self.log_info(f"Committed changes: {commit_hash}")
            
            return commit_hash
            
        except Exception as e:
            raise GitError(f"Failed to commit changes: {str(e)}")
    
    def push(self, project_name: str, branch_name: str = None) -> None:
        """Push changes to remote repository"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            # If no branch specified, push current branch
            if branch_name is None:
                branch_name = self.get_current_branch(project_name)
            
            self.log_info(f"Pushing branch {branch_name} from: {workspace_path}")
            
            # Push the branch to origin
            result = subprocess.run(['git', 'push', '-u', 'origin', branch_name],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to push branch {branch_name}: {result.stderr}")
            
            self.log_info(f"Pushed branch {branch_name} to origin")
            
        except Exception as e:
            raise GitError(f"Failed to push changes: {str(e)}")
        
    def add_all_changes(self, project_name: str) -> None:
        """Add all changes to git staging area with better error handling"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                raise GitError(f"Workspace path does not exist: {workspace_path}")
            
            # Check what files would be added
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                        cwd=workspace_path,
                                        capture_output=True, text=True)
            
            if status_result.stdout.strip():
                self.log_info(f"Files to be staged:\n{status_result.stdout}")
            
            # Add all changes
            result = subprocess.run(['git', 'add', '.'],
                                cwd=workspace_path,
                                capture_output=True, text=True)
            
            if result.returncode != 0:
                raise GitError(f"Failed to add changes: {result.stderr}")
            
            # Verify files were staged
            staged_result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                                        cwd=workspace_path,
                                        capture_output=True, text=True)
            
            if staged_result.stdout.strip():
                self.log_info(f"Staged files: {staged_result.stdout.strip().replace(chr(10), ', ')}")
            else:
                self.log_warning("No files were staged")
            
        except Exception as e:
            raise GitError(f"Failed to add changes: {str(e)}")
    
    def get_project_path(self, project_name: str) -> str:
        """Get the local path for a project"""
        return str(self.base_workspace / project_name)
    
    def get_repo_status(self, project_name: str) -> Dict[str, Any]:
        """Get repository status with better error handling"""
        try:
            workspace_path = self._get_workspace_path(project_name)
            
            # Verify workspace exists
            if not Path(workspace_path).exists():
                return {"error": f"Workspace path does not exist: {workspace_path}"}
            
            # Get various status information using subprocess
            try:
                # Current branch
                branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                            cwd=workspace_path,
                                            capture_output=True, text=True)
                current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
                
                # Working directory status
                status_result = subprocess.run(['git', 'status', '--porcelain'],
                                            cwd=workspace_path,
                                            capture_output=True, text=True)
                is_dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False
                
                # Untracked files
                untracked_result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'],
                                                cwd=workspace_path,
                                                capture_output=True, text=True)
                untracked_files = len(untracked_result.stdout.strip().splitlines()) if untracked_result.stdout.strip() else 0
                
                return {
                    "current_branch": current_branch,
                    "is_dirty": is_dirty,
                    "untracked_files": untracked_files,
                    "workspace_path": workspace_path,
                    "workspace_exists": True
                }
                
            except Exception as status_e:
                return {
                    "error": f"Failed to get git status: {str(status_e)}",
                    "workspace_path": workspace_path,
                    "workspace_exists": True
                }
            
        except Exception as e:
            return {
                "error": str(e),
                "workspace_path": self._get_workspace_path(project_name),
                "workspace_exists": False
            }
    
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
    
    def verify_workspace_structure(self, project_name: str) -> bool:
        """Verify that the workspace structure is correct"""
        try:
            workspace_path = Path(self._get_workspace_path(project_name))
            
            if not workspace_path.exists():
                self.log_error(f"Workspace does not exist: {workspace_path}")
                return False
            
            # Check if it's a git repository
            git_dir = workspace_path / '.git'
            if not git_dir.exists():
                self.log_error(f"Not a git repository: {workspace_path}")
                return False
            
            # Log structure for debugging
            try:
                files = list(workspace_path.rglob("*"))
                self.log_info(f"Workspace structure for {project_name}:")
                for file in files[:10]:  # Show first 10 files
                    self.log_info(f"  {file.relative_to(workspace_path)}")
                if len(files) > 10:
                    self.log_info(f"  ... and {len(files) - 10} more files")
            except Exception as e:
                self.log_warning(f"Could not list workspace structure: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to verify workspace structure: {str(e)}")
            return False
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute git operation with updated operations list"""
        operations = {
            'clone': self.clone_repository,  
            'setup_config': self.setup_git_config, 
            'commit': self.commit,
            'push': self.push,
            'create_branch': self.create_branch,
            'get_current_branch': self.get_current_branch,
            'switch_branch': self.switch_branch,       
            'add_all': self.add_all_changes,
            'get_status': self.get_repo_status, 
            'cleanup': self.cleanup_project,
            'verify_workspace': self.verify_workspace_structure
        }
        
        if operation not in operations:
            raise GitError(f"Unknown git operation: {operation}")
        
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
    
    def _get_workspace_path(self, project_name: str) -> str:
        """Get the workspace path for a project - ensures consistent path usage"""
        return str(self.base_workspace / project_name)