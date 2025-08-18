# core/orchestrator.py
from typing import Dict, Any, List, Optional
import time
import random
import json
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.base_component import BaseComponent
from core.exceptions import AutomationError
from components.github_manager import GitHubManager
from components.git_operations import GitOperations
from components.claude_interface import ClaudeInterface
from components.contract_manager import ContractManager
from components.result_tracker import ResultTracker
from components.summary_tracker import SummaryTracker
from utils.state_tracker import StateTracker
from utils.commit_messages import CommitMessageGenerator


class SmartContractOrchestrator(BaseComponent):
    """Main orchestrator that coordinates all components with state tracking"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.components = {}
        self.results = []
        self.automation_config = config.get('automation', {})
        self.max_workers = self.automation_config.get('parallel_workers', 3)
        self._github_user_info = None  # Cache for GitHub user info
        
        # Initialize state tracker
        self.state_tracker = StateTracker()

        # Call parent constructor
        super().__init__(config, logger)
        
    def _initialize(self) -> None:
        """Initialize all components"""
        self.validate_config(['automation', 'github', 'projects'])
        
        # Initialize components
        self.components['github'] = GitHubManager(self.config, self.logger)
        self.components['git'] = GitOperations(self.config, self.logger)
        self.components['claude'] = ClaudeInterface(self.config, self.logger)
        self.components['contract'] = ContractManager(self.config, self.logger)
        self.components['tracker'] = ResultTracker(self.config, self.logger)
        self.components['summary'] = SummaryTracker(self.config, self.logger)
        
        self.log_info("All components initialized successfully")
    
    def _get_github_user_info(self) -> Dict[str, str]:
        """Get GitHub user information from current token"""
        # Don't cache user info when using different tokens
        # Always get fresh info for the currently active token
        
        try:
            # Get GitHub user info through the GitHubManager component
            # This will use the currently active/forced token
            user_info = self.components['github'].execute('get_user_info')
            
            # Extract user_name and user_email with fallbacks
            user_name = user_info.get('name') or user_info.get('login', 'Smart-dev')
            user_email = user_info.get('email') or f"{user_info.get('login', 'dev')}@users.noreply.github.com"
            
            result_info = {
                'user_name': user_name,
                'user_email': user_email,
                'username': user_info.get('login', 'unknown')
            }
            
            effective_token_index = self.components['github']._get_effective_token_index()
            self.log_info(f"Retrieved GitHub user info for token {effective_token_index} - Name: {user_name}, Email: {user_email}")
            return result_info
            
        except Exception as e:
            self.log_warning(f"Failed to retrieve GitHub user info: {str(e)}")
            
            # Fallback to configuration or hardcoded values
            git_config = self.config.get('automation', {}).get('git_config', {})
            fallback_info = {
                'user_name': git_config.get('user_name', 'Smart-dev'),
                'user_email': git_config.get('user_email', 'bob@smartcontract.dev'),
                'username': 'unknown'
            }
            
            self.log_info(f"Using fallback Git config - Name: {fallback_info['user_name']}, Email: {fallback_info['user_email']}")
            return fallback_info

    
    def _process_projects_parallel_1to1(self, projects: List[Dict[str, Any]], available_tokens: List[int]) -> List[Dict[str, Any]]:
        """Process projects in parallel with 1:1 token assignment"""
        results = []
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(available_tokens))) as executor:
            # Submit projects with specific token assignments
            future_to_project = {}
            for i, project in enumerate(projects):
                if i >= len(available_tokens):
                    break  # Stop when we run out of tokens
                
                token_index = available_tokens[i]
                self.log_info(f"Assigning token {token_index} to project {project['name']}")
                
                # Mark project as started
                self.state_tracker.mark_project_started(project['name'], token_index)
                
                future = executor.submit(self._process_single_project, project, token_index)
                future_to_project[future] = (project, token_index)
            
            # Collect results as they complete
            for future in as_completed(future_to_project):
                project, token_index = future_to_project[future]
                project_name = project['name']
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Record completion in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        token_index,
                        success=(result.get('status') == 'completed'),
                        duration=result.get('duration', 0),
                        error=result.get('error'),
                        pr_url=result.get('pr_url')
                    )
                    
                    self.log_info(f"Completed project: {project_name} using assigned token {token_index}")
                    
                except Exception as e:
                    error_result = {
                        'project_name': project_name,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.time(),
                        'token_index': token_index
                    }
                    results.append(error_result)
                    
                    # Record failure in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        token_index,
                        success=False,
                        error=str(e)
                    )
                    
                    self.log_error(f"Project {project_name} failed with token {token_index}: {str(e)}")
        
        return results

    
    def process_all_projects(self, skip_completed: bool = True) -> List[Dict[str, Any]]:
        """Process all projects with 1:1 token mapping, stopping when no more tokens available"""
        all_projects = self.config.get('projects', [])
        
        if not all_projects:
            self.log_warning("No projects found in configuration")
            return []
        
        # Filter out completed projects if requested
        if skip_completed:
            projects = self.state_tracker.get_incomplete_projects(all_projects)
            completed_count = len(all_projects) - len(projects)
            if completed_count > 0:
                self.log_info(f"Skipping {completed_count} already completed projects")
        else:
            projects = all_projects
            self.log_info("Processing all projects (including completed ones)")
        
        if not projects:
            self.log_info("All projects have been completed successfully!")
            return []
        
        # Get available tokens and limit projects to token count
        github_manager = self.components['github']
        available_tokens = github_manager.get_available_tokens()
        
        if len(projects) > len(available_tokens):
            projects = projects[:len(available_tokens)]
            self.log_info(f"Limited to {len(available_tokens)} projects to match available tokens (1:1 mapping)")
        
        self.log_info(f"Starting automation for {len(projects)} projects with 1:1 token mapping")
        
        # Enable batch mode before processing
        self.components['github'].execute('set_batch_mode', batch_mode=True)
        self.log_info("Enabled batch mode for 1:1 token mapping")
        
        try:
            # CRITICAL FIX: Always use safe sequential processing to prevent file conflicts
            # Force sequential mode regardless of max_workers setting for workspace safety
            self.log_info("Using safe sequential processing to prevent workspace conflicts")
            return self._process_projects_sequential_1to1_safe(projects, available_tokens)
            
        finally:
            # Always disable batch mode after processing
            self.components['github'].execute('set_batch_mode', batch_mode=False)
            self.log_info("Disabled batch mode after processing")

    
    def _process_projects_parallel(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects in parallel with proper token rotation"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all projects
            future_to_project = {}
            for project in projects:
                # CRITICAL FIX: Don't manually set token index - let batch mode handle it
                # The token will be selected automatically in _process_single_project
                
                # Mark project as started (token will be assigned in the worker)
                future = executor.submit(self._process_single_project, project)
                future_to_project[future] = project
            
            # Collect results as they complete
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                project_name = project['name']
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Record completion in state tracker
                    token_index = result.get('token_index', 0)
                    self.state_tracker.mark_project_completed(
                        project_name,
                        token_index,
                        success=(result.get('status') == 'completed'),
                        duration=result.get('duration', 0),
                        error=result.get('error'),
                        pr_url=result.get('pr_url')
                    )
                    
                    self.log_info(f"Completed project: {project_name} using token {token_index}")
                    
                except Exception as e:
                    error_result = {
                        'project_name': project_name,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.time(),
                        'token_index': 0  # Default if no token was selected
                    }
                    results.append(error_result)
                    
                    # Record failure in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        0,  # Default token index
                        success=False,
                        error=str(e)
                    )
                    
                    self.log_error(f"Project {project_name} failed: {str(e)}")
        
        return results
    
    
    def _process_projects_sequential(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects sequentially with proper token rotation"""
        results = []
        
        for project in projects:
            project_name = project['name']
            
            try:
                # CRITICAL FIX: Don't manually set token index - let batch mode handle it
                # The token will be selected automatically in _process_single_project
                
                result = self._process_single_project(project)
                results.append(result)
                
                # Record completion in state tracker
                token_index = result.get('token_index', 0)
                self.state_tracker.mark_project_completed(
                    project_name,
                    token_index,
                    success=(result.get('status') == 'completed'),
                    duration=result.get('duration', 0),
                    error=result.get('error'),
                    pr_url=result.get('pr_url')
                )
                
                self.log_info(f"Completed project: {project_name} using token {token_index}")
                
                # CRITICAL FIX: Force rotation after each project in sequential mode
                # This ensures we move to the next token for the next project
                self.components['github'].rotate_token(project_name, force=True)
                self.log_info(f"Rotated token after {project_name}")
                
                # Clear cached user info so it gets refreshed with new token
                self._github_user_info = None
                
            except Exception as e:
                error_result = {
                    'project_name': project_name,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.time(),
                    'token_index': self.components['github']._get_effective_token_index()
                }
                results.append(error_result)
                
                # Record failure in state tracker
                self.state_tracker.mark_project_completed(
                    project_name,
                    self.components['github']._get_effective_token_index(),
                    success=False,
                    error=str(e)
                )
                
                self.log_error(f"Project {project_name} failed: {str(e)}")
                
                # Still rotate token even on failure to try a different token for next project
                try:
                    self.components['github'].rotate_token(project_name, force=True)
                    self.log_info(f"Rotated token after failed {project_name}")
                except Exception as rotate_error:
                    self.log_warning(f"Failed to rotate token after {project_name}: {rotate_error}")
        
        return results
    
    def _process_single_project(self, project: Dict[str, Any], manual_token_index: Optional[int] = None) -> Dict[str, Any]:
        """Process a single project through the complete workflow"""
        project_name = project['name']
        start_time = time.time()
        branch_name = f"feature/{project_name.lower().replace(' ', '-').replace('_', '-')}"
        
        result = {
            'project_name': project_name,
            'status': 'in_progress',
            'start_time': start_time,
            'branch_name': branch_name,
            'steps': {}
        }
        
        try:
            # CRITICAL FIX: Token should already be set by _process_single_project_with_token
            github_manager = self.components['github']
            
            if manual_token_index is not None:
                # Single project mode with specific token
                github_manager.execute('force_token', token_index=manual_token_index)
                token_index = manual_token_index
                self.log_info(f"Forcing token index {manual_token_index} for project {project_name}")
            else:
                # Use the currently assigned token (should be set by wrapper method)
                token_index = github_manager._get_effective_token_index()
                self.log_info(f"Using pre-assigned token index {token_index} for project {project_name}")
            
            # Mark project as started in state tracker (if not already marked)
            if not self.state_tracker.is_project_completed(project_name):
                self.state_tracker.mark_project_started(project_name, token_index)
            
            # Rest of the processing remains the same...
            # Step 1: Create GitHub repository
            self.log_info(f"Creating GitHub repository for {project_name}")
            repo_url = self.components['github'].execute('create_repo', project=project)
            result['steps']['github_repo'] = {
                'status': 'success',
                'repo_url': repo_url,
                'token_index': token_index,
                'timestamp': time.time()
            }
            
            # Step 2: Clone repository locally
            self.log_info(f"Cloning repository for {project_name}")
            workspace_path = self.components['git'].execute('clone', 
                                                        repo_url=repo_url, 
                                                        project_name=project_name)
            result['steps']['git_clone'] = {
                'status': 'success',
                'workspace_path': workspace_path,
                'timestamp': time.time()
            }
            
            # Verify workspace after cloning
            if not self.components['git'].execute('verify_workspace', project_name=project_name):
                raise AutomationError(f"Workspace verification failed after cloning: {workspace_path}")
            
            # Step 3: Create and checkout feature branch
            self.log_info(f"Creating feature branch: {branch_name}")
            self.components['git'].execute('create_branch',
                                        project_name=project_name,
                                        branch_name=branch_name)
            result['steps']['branch_creation'] = {
                'status': 'success',
                'branch_name': branch_name,
                'timestamp': time.time()
            }
            
            # Step 4: Setup Git configuration with dynamic user info
            self.log_info(f"Setting up Git configuration for {project_name}")
            github_user_info = self._get_github_user_info()
            self.log_info(f"Retrieved GitHub user info - Name: {github_user_info['user_name']}, Email: {github_user_info['user_email']}")
            
            self.components['git'].execute('setup_config',
                                         project_name=project_name,
                                         user_name=github_user_info['user_name'],
                                         user_email=github_user_info['user_email'])
            result['steps']['git_config'] = {
                'status': 'success',
                'user_name': github_user_info['user_name'],
                'user_email': github_user_info['user_email'],
                'github_username': github_user_info['username'],
                'timestamp': time.time()
            }
            
            # Step 5: Initialize smart contract environment
            self.log_info(f"Initializing smart contract environment for {project_name}")
            self.components['contract'].execute('initialize',
                                            workspace_path=workspace_path,
                                            project=project)
            
            contract_dir = self.components['contract'].get_contract_directory(project)
            result['steps']['contract_init'] = {
                'status': 'success',
                'contract_directory': contract_dir,
                'timestamp': time.time()
            }
            
            # Step 6: Generate smart contract with Claude
            self.log_info(f"Generating smart contract for {project_name}")
            contract_file = self.components['claude'].execute('generate_contract',
                                                            project=project,
                                                            workspace_path=workspace_path)
            result['steps']['contract_generation'] = {
                'status': 'success',
                'contract_file': contract_file,
                'contract_directory': contract_dir,
                'timestamp': time.time()
            }
            
            # Step 7: Compile contract (with error fixing loop)
            self.log_info(f"Compiling contract for {project_name}")
            contract_result = self._compile_loop(project, workspace_path)
            result['steps']['contract_compilation'] = contract_result

            # NEW Step 7.5: First Commit - Smart Contract Implementation
            self.log_info(f"Making first commit: Smart contract implementation for {project_name}")
            first_commit_message = CommitMessageGenerator.generate_smart_contract_commit(project_name)
            try:
                first_commit_hash = self.components['git'].execute('commit',
                                                                project_name=project_name,
                                                                commit_message=first_commit_message)
                
                if first_commit_hash == "no-changes":
                    self.log_warning("No changes detected for first commit, but continuing...")
                    first_commit_hash = "no-changes"
                
                result['steps']['first_commit'] = {
                    'status': 'success',
                    'commit_hash': first_commit_hash,
                    'commit_message': first_commit_message,
                    'commit_type': 'smart_contract_implementation',
                    'timestamp': time.time()
                }
                
                self.log_info(f"First commit completed: {first_commit_hash}")
                
            except Exception as commit_e:
                self.log_error(f"First commit failed for {project_name}: {str(commit_e)}")
                # Don't fail the entire process for commit issues
                result['steps']['first_commit'] = {
                    'status': 'failed',
                    'error': str(commit_e),
                    'commit_type': 'smart_contract_implementation',
                    'timestamp': time.time()
                }
            
            # Step 8: Create project README at root level
            self.log_info(f"Generating comprehensive README for {project_name}")
            readme_file = self.components['claude'].execute('generate_readme',
                                                          project=project,
                                                          workspace_path=workspace_path,
                                                          contract_file=contract_file)
            result['steps']['readme_generation'] = {
                'status': 'success',
                'readme_file': readme_file,
                'timestamp': time.time()
            }
            
            # Verify workspace before git operations
            self.log_info(f"Verifying workspace before git operations for {project_name}")
            if not self.components['git'].execute('verify_workspace', project_name=project_name):
                raise AutomationError(f"Workspace verification failed before git operations")
            
            # Get workspace status for debugging
            git_status = self.components['git'].execute('get_status', project_name=project_name)
            self.log_info(f"Git status before commit: {git_status}")

            # NEW Step 8.5: Second Commit - Documentation
            self.log_info(f"Making second commit: Documentation for {project_name}")
            second_commit_message = CommitMessageGenerator.generate_documentation_commit(project_name)
            
            try:
                second_commit_hash = self.components['git'].execute('commit',
                                                                project_name=project_name,
                                                                commit_message=second_commit_message)
                
                if second_commit_hash == "no-changes":
                    self.log_warning("No changes detected for second commit")
                    second_commit_hash = "no-changes"
                
                result['steps']['second_commit'] = {
                    'status': 'success',
                    'commit_hash': second_commit_hash,
                    'commit_message': second_commit_message,
                    'commit_type': 'documentation',
                    'timestamp': time.time()
                }
                
                self.log_info(f"Second commit completed: {second_commit_hash}")
                
            except Exception as commit_e:
                self.log_error(f"Second commit failed for {project_name}: {str(commit_e)}")
                result['steps']['second_commit'] = {
                    'status': 'failed',
                    'error': str(commit_e),
                    'commit_type': 'documentation',
                    'timestamp': time.time()
                }
            
            # Verify workspace before final operations
            self.log_info(f"Verifying workspace before final operations for {project_name}")
            if not self.components['git'].execute('verify_workspace', project_name=project_name):
                raise AutomationError(f"Workspace verification failed before final operations")
            
           # Step 9: Push all commits to feature branch
            self.log_info(f"Pushing all commits for {project_name}")
            try:
                self.components['git'].execute('push',
                                            project_name=project_name,
                                            branch_name=branch_name)
                
                result['steps']['git_push'] = {
                    'status': 'success',
                    'branch_name': branch_name,
                    'commits_pushed': 2,  # Two commits pushed
                    'timestamp': time.time()
                }
                
            except Exception as push_e:
                self.log_error(f"Git push failed for {project_name}: {str(push_e)}")
                raise AutomationError(f"Git push operations failed: {str(push_e)}")
            
            # Step 10: Create pull request from feature branch to main (with retry logic)
            self.log_info(f"Creating pull request for {project_name}")
            try:
                pr_url = self.components['github'].execute('create_pr',
                                                        project=project,
                                                        branch_name=branch_name,
                                                        base_branch="main")
                
                if pr_url:
                    result['steps']['pull_request'] = {
                        'status': 'success',
                        'pr_url': pr_url,
                        'branch_name': branch_name,
                        'base_branch': 'main',
                        'timestamp': time.time()
                    }
                    result['pr_url'] = pr_url
                else:
                    # PR creation failed but project is still successful
                    result['steps']['pull_request'] = {
                        'status': 'failed_but_not_critical',
                        'branch_name': branch_name,
                        'base_branch': 'main',
                        'timestamp': time.time(),
                        'note': 'PR creation failed but code was successfully pushed'
                    }
                    result['pr_url'] = None
                    self.log_warning(f"PR creation failed for {project_name}, but project considered successful since code was pushed")

            except Exception as e:
                # PR creation failed but project is still successful since code was pushed
                result['steps']['pull_request'] = {
                    'status': 'failed_but_not_critical',
                    'error': str(e),
                    'branch_name': branch_name,
                    'base_branch': 'main',
                    'timestamp': time.time(),
                    'note': 'PR creation failed but code was successfully pushed'
                }
                result['pr_url'] = None
                self.log_warning(f"PR creation failed for {project_name}, but project considered successful since code was pushed: {str(e)}")

            # Step 11: Record results (PROJECT IS ALWAYS SUCCESSFUL IF WE REACH HERE)
            result['status'] = 'completed'
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            result['token_index'] = token_index
            result['github_username'] = github_user_info['username']
            result['contract_directory'] = contract_dir

            if 'second_commit' in result['steps'] and result['steps']['second_commit'].get('status') == 'success':
                result['commit_message'] = result['steps']['second_commit']['commit_message']
            elif 'first_commit' in result['steps'] and result['steps']['first_commit'].get('status') == 'success':
                result['commit_message'] = result['steps']['first_commit']['commit_message']
            else:
                # Fallback
                result['commit_message'] = f"Implemented {project_name} smart contract with documentation"
                
            # Record in detailed tracker
            self.components['tracker'].execute('record_result', result=result)
            
            # Record clean summary for personal use
            self.components['summary'].execute('record_summary', result=result)

            # New Record summary implementation
            self.components['summary'].save_immediately()

            self.log_info(f"Saved summary for completed project: {project_name}")
            
            # CHECK CLEANUP CONFIGURATION
            cleanup_on_success = self.automation_config.get('cleanup_on_success', False)
            if cleanup_on_success:
                self._cleanup_successful_project(project_name)
                self.log_info(f"Cleaned up successful project: {project_name}")
            else:
                self.log_info(f"Project {project_name} completed successfully - workspace preserved at {workspace_path}")
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            
            # Use the actual token index that was attempted
            result['token_index'] = token_index if 'token_index' in locals() else github_manager._get_effective_token_index()

            try:    
                github_user_info = self._get_github_user_info()
                result['github_username'] = github_user_info['username']
            except:
                result['github_username'] = 'unknown'
            
            # CRITICAL FIX: NO AUTO-CLEANUP unless specifically configured
            cleanup_on_failure = self.automation_config.get('cleanup_on_failure', False)
            if cleanup_on_failure:
                self._cleanup_failed_project(project_name)
                self.log_info(f"Cleaned up failed project: {project_name}")
            else:
                self.log_info(f"Project {project_name} failed - workspace preserved for debugging at workspace/{project_name}")
            
            raise AutomationError(f"Project {project_name} failed: {str(e)}")
        
        return result


    def _process_projects_parallel_1to1(self, projects: List[Dict[str, Any]], available_tokens: List[int]) -> List[Dict[str, Any]]:
        """Process projects in parallel with 1:1 token assignment"""
        results = []
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(available_tokens))) as executor:
            # Submit projects with specific token assignments
            future_to_project = {}
            for i, project in enumerate(projects):
                if i >= len(available_tokens):
                    break  # Stop when we run out of tokens
                
                token_index = available_tokens[i]
                self.log_info(f"Assigning token {token_index} to project {project['name']}")
                
                # Mark project as started
                self.state_tracker.mark_project_started(project['name'], token_index)
                
                # CRITICAL FIX: Pass the specific token assignment to the worker
                future = executor.submit(self._process_single_project_with_token, project, token_index)
                future_to_project[future] = (project, token_index)
            
            # Collect results as they complete
            for future in as_completed(future_to_project):
                project, token_index = future_to_project[future]
                project_name = project['name']
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Record completion in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        token_index,
                        success=(result.get('status') == 'completed'),
                        duration=result.get('duration', 0),
                        error=result.get('error'),
                        pr_url=result.get('pr_url')
                    )
                    
                    self.log_info(f"Completed project: {project_name} using assigned token {token_index}")
                    
                except Exception as e:
                    error_result = {
                        'project_name': project_name,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.time(),
                        'token_index': token_index
                    }
                    results.append(error_result)
                    
                    # Record failure in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        token_index,
                        success=False,
                        error=str(e)
                    )
                    
                    self.log_error(f"Project {project_name} failed with token {token_index}: {str(e)}")
        
        return results

    def _process_single_project_with_token(self, project: Dict[str, Any], assigned_token_index: int) -> Dict[str, Any]:
        """Process a single project with a specific token assignment (for 1:1 mapping)"""
        project_name = project['name']
        
        # CRITICAL FIX: Force the specific token assignment BEFORE any GitHub operations
        github_manager = self.components['github']
        
        # Force the GitHub manager to use the assigned token for this entire project
        github_manager.execute('force_token', token_index=assigned_token_index)
        self.log_info(f"Locked token {assigned_token_index} for project {project_name}")
        
        try:
            # Process the project with the locked token
            result = self._process_single_project(project, assigned_token_index)
            return result
        except Exception as e:
            # ONLY cleanup the failed project, not successful ones
            cleanup_on_failure = self.automation_config.get('cleanup_on_failure', False)
            if cleanup_on_failure:
                self._cleanup_failed_project(project_name)
                self.log_info(f"Cleaned up failed project: {project_name}")
            else:
                self.log_info(f"Project {project_name} failed - workspace preserved for debugging")
            
            # Re-raise the exception after cleanup
            raise e
        finally:
            # Clear the forced token after the project completes (for parallel processing)
            github_manager.forced_token_index = None
            self.log_info(f"Released token {assigned_token_index} after {project_name}")

    def _process_single_project_with_token_safe(self, project: Dict[str, Any], assigned_token_index: int) -> Dict[str, Any]:
        """Process a single project with workspace safety - ensures complete lifecycle before next project"""
        project_name = project['name']
        
        # CRITICAL FIX: Force the specific token assignment BEFORE any operations
        github_manager = self.components['github']
        github_manager.execute('force_token', token_index=assigned_token_index)
        self.log_info(f"Locked token {assigned_token_index} for project {project_name}")
        
        try:
            # STEP 1: Ensure any existing workspace is cleaned up first
            self._ensure_clean_workspace(project_name)
            
            # STEP 2: Process the project with the locked token
            result = self._process_single_project(project, assigned_token_index)
            
            # STEP 3: If successful, optionally cleanup or preserve based on config
            if result.get('status') != 'completed':
                cleanup_on_failure = self.automation_config.get('cleanup_on_failure', True)
                if cleanup_on_failure:
                    self._cleanup_failed_project(project_name)
                    self.log_info(f"Cleaned up failed project workspace: {project_name}")
                else:
                    self.log_info(f"Project {project_name} failed - workspace preserved for debugging")
            else:
                # SUCCESS - DON'T CLEANUP unless explicitly configured
                cleanup_on_success = self.automation_config.get('cleanup_on_success', False)
                if cleanup_on_success:
                    self._cleanup_successful_project(project_name)
                    self.log_info(f"Cleaned up successful project workspace: {project_name}")
                else:
                    self.log_info(f"Project {project_name} completed successfully - workspace preserved")
            
            return result
            
        except Exception as e:
            # STEP 4: On failure, cleanup the workspace to prevent conflicts
            self.log_error(f"Project {project_name} failed: {str(e)}")
            
            cleanup_on_failure = self.automation_config.get('cleanup_on_failure', True)  # Default True for failures
            if cleanup_on_failure:
                self._cleanup_failed_project(project_name)
                self.log_info(f"Cleaned up failed project workspace: {project_name}")
            else:
                self.log_info(f"Project {project_name} failed - workspace preserved for debugging")
            
            # Re-raise the exception
            raise e
            
        finally:
            # STEP 5: Always release the token
            github_manager.forced_token_index = None
            self.log_info(f"Released token {assigned_token_index} after {project_name}")


    def _process_projects_sequential_1to1_safe(self, projects: List[Dict[str, Any]], available_tokens: List[int]) -> List[Dict[str, Any]]:
        """Process projects sequentially with 1:1 token assignment and safe workspace handling"""
        results = []
        
        for i, project in enumerate(projects):
            if i >= len(available_tokens):
                self.log_info(f"Stopping at project {i+1} - no more tokens available (1:1 mapping)")
                break
            
            project_name = project['name']
            token_index = available_tokens[i]
            
            try:
                self.log_info(f"Processing {project_name} with assigned token {token_index}")
                
                # Mark project as started
                self.state_tracker.mark_project_started(project_name, token_index)
                
                # CRITICAL FIX: Process project completely before moving to next
                # This ensures no workspace conflicts
                result = self._process_single_project_with_token_safe(project, token_index)
                results.append(result)
                
                # Record completion in state tracker
                self.state_tracker.mark_project_completed(
                    project_name,
                    token_index,
                    success=(result.get('status') == 'completed'),
                    duration=result.get('duration', 0),
                    error=result.get('error'),
                    pr_url=result.get('pr_url')
                )
                
                self.log_info(f"Completed project: {project_name} using assigned token {token_index}")
                
                # IMPORTANT: Save summaries immediately after each success
                if result.get('status') == 'completed':
                    self.components['summary'].execute('record_summary', result=result)
                    self.components['summary'].save_immediately()
                    self.log_info(f"Saved summary for completed project: {project_name}")
                
            except Exception as e:
                error_result = {
                    'project_name': project_name,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.time(),
                    'token_index': token_index
                }
                results.append(error_result)
                
                # Record failure in state tracker
                self.state_tracker.mark_project_completed(
                    project_name,
                    token_index,
                    success=False,
                    error=str(e)
                )
                
                self.log_error(f"Project {project_name} failed with assigned token {token_index}: {str(e)}")
        
        return results

    
    def _get_random_commit_message(self, project_name: str) -> str:
        """Generate a random, unique commit message (for backward compatibility)"""
        return CommitMessageGenerator.generate_final_commit(project_name)
    
    def _compile_loop(self, project: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Compile contract with error fixing loop using persistent Claude sessions"""
        max_retries = self.automation_config.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                # Compile contract only
                compile_result = self.components['contract'].execute('compile',
                                                                   workspace_path=workspace_path,
                                                                   contract_file="")
                
                if compile_result['success']:
                    # Compilation successful!
                    self.log_info(f"Contract compilation successful on attempt {attempt + 1}")
                    
                    # Close Claude sessions for this project since we're done
                    try:
                        self.components['claude'].execute('close_sessions', project_name=project['name'])
                    except Exception as e:
                        self.log_warning(f"Failed to close Claude sessions: {str(e)}")
                    
                    # Log warnings if any
                    if compile_result.get('has_warnings', False):
                        warnings = compile_result.get('warnings', [])
                        self.log_info(f"Compilation succeeded with {len(warnings)} warnings")
                        for warning in warnings:
                            self.log_warning(f"Warning: {warning.get('message', 'Unknown warning')}")
                    
                    return {
                        'status': 'success',
                        'attempts': attempt + 1,
                        'compile_result': compile_result,
                        'has_warnings': compile_result.get('has_warnings', False),
                        'warnings': compile_result.get('warnings', []),
                        'timestamp': time.time()
                    }
                else:
                    # Compilation failed - extract error details for Claude
                    error_details = compile_result.get('error_details', {})
                    formatted_errors = error_details.get('formatted_for_claude', '') if error_details else ''
                    
                    # Use formatted errors if available, otherwise fallback to basic error message
                    error_message = formatted_errors or compile_result.get('errors', 'Compilation failed')
                    
                    self.log_warning(f"Compilation failed (attempt {attempt + 1})")
                    self.log_warning(f"Error details: {error_message[:200]}...")  # Truncate for logging
                    
                    if attempt < max_retries - 1:
                        # Fix the error with Claude using session context and attempt number
                        self.log_info(f"Sending error to Claude for fixing (attempt {attempt + 1})")
                        
                        # Get session status before fixing
                        try:
                            session_status = self.components['claude'].execute('get_session_status', 
                                                                             project_name=project['name'])
                            self.log_info(f"Claude session status: {session_status}")
                        except Exception as e:
                            self.log_warning(f"Could not get session status: {str(e)}")
                        
                        # Send to Claude with attempt number for better context
                        self.components['claude'].execute('fix_error',
                                                        project=project,
                                                        workspace_path=workspace_path,
                                                        error_message=error_message,
                                                        error_details=error_details,
                                                        attempt=attempt + 1)
                    else:
                        self.log_error(f"Max retries reached. Final compilation error: {error_message[:200]}...")
                        
                        # Close sessions on final failure
                        try:
                            self.components['claude'].execute('close_sessions', project_name=project['name'])
                        except Exception as e:
                            self.log_warning(f"Failed to close Claude sessions: {str(e)}")
                
                # Wait before retry
                retry_delay = self.automation_config.get('retry_delay', 30)
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    self.log_info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                
            except Exception as e:
                self.log_error(f"Contract compilation attempt {attempt + 1} failed with exception: {str(e)}")
                
                if attempt == max_retries - 1:
                    # Close sessions on exception
                    try:
                        self.components['claude'].execute('close_sessions', project_name=project['name'])
                    except Exception as session_e:
                        self.log_warning(f"Failed to close Claude sessions: {str(session_e)}")
                    
                    return {
                        'status': 'failed',
                        'attempts': attempt + 1,
                        'error': str(e),
                        'error_type': 'exception',
                        'timestamp': time.time()
                    }
                
                time.sleep(self.automation_config.get('retry_delay', 5))
        
        # Final failure - close sessions
        try:
            self.components['claude'].execute('close_sessions', project_name=project['name'])
        except Exception as e:
            self.log_warning(f"Failed to close Claude sessions: {str(e)}")
        
        return {
            'status': 'failed',
            'attempts': max_retries,
            'error': 'Maximum retry attempts exceeded',
            'error_type': 'max_retries_exceeded',
            'timestamp': time.time()
        }
    
    def test_contract_optional(self, project: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Optional contract testing - separate from compilation workflow"""
        try:
            self.log_info(f"Running optional contract tests for {project['name']}")
            test_result = self.components['contract'].execute('test', workspace_path=workspace_path)
            
            if test_result['success']:
                self.log_info("Contract tests passed successfully")
            else:
                self.log_warning(f"Contract tests failed: {test_result.get('errors', 'Unknown test failure')}")
            
            return {
                'status': 'success' if test_result['success'] else 'failed',
                'test_result': test_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.log_error(f"Contract testing failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _cleanup_failed_project(self, project_name: str) -> None:
        """Clean up resources for a failed project"""
        try:
            # Clean up Git workspace
            self.components['git'].execute('cleanup', project_name=project_name)
            self.log_info(f"Cleaned up workspace for failed project: {project_name}")
        except Exception as e:
            self.log_error(f"Failed to cleanup project {project_name}: {str(e)}")

    def _cleanup_successful_project(self, project_name: str) -> None:
        """Clean up resources for a successful project"""
        try:
            # Clean up Git workspace
            self.components['git'].execute('cleanup', project_name=project_name)
            self.log_info(f"Cleaned up workspace for successful project: {project_name}")
        except Exception as e:
            self.log_error(f"Failed to cleanup successful project {project_name}: {str(e)}")


    def _ensure_clean_workspace(self, project_name: str) -> None:
        """Ensure workspace is clean before starting new project"""
        try:
            workspace_path = Path(f"workspace/{project_name}")
            
            if workspace_path.exists():
                self.log_warning(f"Found existing workspace for {project_name}, cleaning up...")
                self._cleanup_existing_workspace(project_name)
                
                # Wait a moment for filesystem operations to complete
                time.sleep(1)
                
                # Verify cleanup was successful
                if workspace_path.exists():
                    self.log_error(f"Failed to clean existing workspace: {workspace_path}")
                    raise AutomationError(f"Cannot proceed - workspace cleanup failed for {project_name}")
            
            self.log_info(f"Workspace ready for {project_name}")
            
        except Exception as e:
            self.log_error(f"Workspace preparation failed for {project_name}: {str(e)}")
            raise AutomationError(f"Workspace preparation failed: {str(e)}")

    def _cleanup_existing_workspace(self, project_name: str) -> None:
        """Clean up existing workspace safely"""
        try:
            # Use the git component's cleanup method if available
            self.components['git'].execute('cleanup', project_name=project_name)
            self.log_info(f"Cleaned up existing workspace for: {project_name}")
        except Exception as e:
            self.log_warning(f"Git cleanup failed, trying manual cleanup: {str(e)}")
            
            # Fallback to manual cleanup
            import shutil
            workspace_path = Path(f"workspace/{project_name}")
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
                self.log_info(f"Manually removed workspace: {workspace_path}")

    
    def get_project_status(self, project_name: str) -> Dict[str, Any]:
        """Get status of a specific project"""
        try:
            git_status = self.components['git'].execute('get_status', project_name=project_name)
            return {
                'project_name': project_name,
                'git_status': git_status,
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'project_name': project_name,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def pause_automation(self) -> None:
        """Pause the automation process"""
        self.log_info("Automation paused")
        # Implementation for pausing - could use threading events
    
    def resume_automation(self) -> None:
        """Resume the automation process"""
        self.log_info("Automation resumed")
        # Implementation for resuming
    
    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall automation status"""
        component_statuses = {}
        for name, component in self.components.items():
            try:
                component_statuses[name] = component.get_status()
            except Exception as e:
                component_statuses[name] = {'error': str(e)}
        
        return {
            'total_projects': len(self.config.get('projects', [])),
            'completed_projects': len([r for r in self.results if r.get('status') == 'completed']),
            'failed_projects': len([r for r in self.results if r.get('status') == 'failed']),
            'component_statuses': component_statuses,
            'timestamp': time.time()
        }
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute orchestrator operation"""
        operations = {
            'process_all': self.process_all_projects,
            'process_single': self._process_single_project,
            'test_contract': self.test_contract_optional,  # NEW: Optional testing
            'get_status': self.get_overall_status,
            'get_project_status': self.get_project_status,
            'pause': self.pause_automation,
            'resume': self.resume_automation
        }
        
        if operation not in operations:
            raise AutomationError(f"Unknown orchestrator operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Orchestrator operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up all components"""
        for name, component in self.components.items():
            try:
                component.cleanup()
                self.log_info(f"Cleaned up component: {name}")
            except Exception as e:
                self.log_error(f"Failed to cleanup component {name}: {str(e)}")

    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return self.get_overall_status()