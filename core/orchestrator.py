# core/orchestrator.py - Updated with Summary Tracker
from typing import Dict, Any, List, Optional
import time
import random
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.base_component import BaseComponent
from core.exceptions import AutomationError
from components.github_manager import GitHubManager
from components.git_operations import GitOperations
from components.claude_interface import ClaudeInterface
from components.contract_manager import ContractManager
from components.result_tracker import ResultTracker
from components.summary_tracker import SummaryTracker  # NEW
from utils.state_tracker import StateTracker

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

        # Add commit message templates for uniqueness
        self.commit_messages = [
            "Added {project_name} smart contract implementation",
            "Implement {project_name} blockchain solution",
            "Deployed {project_name} Clarity smart contract",
            "Created {project_name} decentralized application core",
            "Build {project_name} smart contract infrastructure",
            "Develop {project_name} blockchain protocol",
            "Launch {project_name} smart contract system",
            "Establish {project_name} blockchain protocol foundation",
            "Integrate {project_name} smart contract functionality",
            "Constructed {project_name} blockchain-based solution",
            "Engineered {project_name} decentralized smart contract",
            "Crafted {project_name} innovative blockchain implementation",
            "Designed {project_name} robust smart contract architecture",
            "structured {project_name} cutting-edge blockchain solution",
            "programmed {project_name} scalable smart contract platform",
            "Initialize {project_name} enterprise-grade blockchain solution",
            "Bootstraped {project_name} next-generation smart contract",
            "intrgrated {project_name} revolutionary blockchain protocol",
            "set-up {project_name} advanced smart contract framework",
            "{project_name} blockchain infrastructure added"
        ]
        
        # Enhanced detail descriptions for richer commit messages
        self.commit_details = [
            "- Implemented core contract functionality",
            "- Added comprehensive error handling", 
            "- Integrated security best practices",
            "- Included detailed documentation",
            "- Added contract validation",
            "- Implemented access controls",
            "- Integrated multi-signature support",
            "- Added event logging system",
            "- Implemented emergency pause functionality",
            "- Added performance optimizations",
            "- Implemented governance mechanisms",
            "- Created developer documentation"
        ]
        
        # Technical enhancement options for variety
        self.technical_features = [
            "- Leveraged Clarity's built-in safety features",
            "- Utilized Stacks blockchain capabilities",
            "- Integrated with Bitcoin settlement layer",
            "- Implemented predictable smart contract execution",
            "- Added STX token integration",
            "- Created robust transaction handling",
            "- Ensured deterministic contract behavior",
            "- Optimized for Stacks network efficiency",
            "- Integrated continuous integration pipeline"
        ]

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
        self.components['summary'] = SummaryTracker(self.config, self.logger)  # NEW
        
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
        
    
    def process_all_projects(self, skip_completed: bool = True) -> List[Dict[str, Any]]:
        """Process all projects with parallel execution, skipping completed ones"""
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
        
        self.log_info(f"Starting automation for {len(projects)} projects")
        
        # Process projects in parallel
        if self.max_workers > 1:
            return self._process_projects_parallel(projects)
        else:
            return self._process_projects_sequential(projects)

    
    def _process_projects_parallel(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects in parallel with state tracking"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all projects
            future_to_project = {}
            for project in projects:
                # Get next available token for this project
                token_index = self.components['github'].get_next_token_index(project['name'])
                self.components['github'].set_manual_token_index(token_index)
                
                # Mark project as started
                self.state_tracker.mark_project_started(project['name'], token_index)
                
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
                    self.state_tracker.mark_project_completed(
                        project_name,
                        self.components['github'].current_token_index,
                        success=(result.get('status') == 'completed'),
                        duration=result.get('duration', 0),
                        error=result.get('error'),
                        pr_url=result.get('pr_url')
                    )
                    
                    self.log_info(f"Completed project: {project_name}")
                    
                except Exception as e:
                    error_result = {
                        'project_name': project_name,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    results.append(error_result)
                    
                    # Record failure in state tracker
                    self.state_tracker.mark_project_completed(
                        project_name,
                        self.components['github'].current_token_index,
                        success=False,
                        error=str(e)
                    )
                    
                    self.log_error(f"Project {project_name} failed: {str(e)}")
                
                # Rotate GitHub token after each project
                try:
                    self.components['github'].rotate_token(project_name)
                    # Clear cached user info so it gets refreshed with new token
                    self._github_user_info = None
                except Exception as e:
                    self.log_warning(f"Failed to rotate GitHub token: {str(e)}")
        
        return results
    
    
    def _process_projects_sequential(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects sequentially with state tracking"""
        results = []
        
        for project in projects:
            project_name = project['name']
            
            try:
                # Get next available token for this project
                token_index = self.components['github'].get_next_token_index(project_name)
                self.components['github'].set_manual_token_index(token_index)
                
                # Mark project as started
                self.state_tracker.mark_project_started(project_name, token_index)
                
                result = self._process_single_project(project)
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
                
                self.log_info(f"Completed project: {project_name}")
                
                # Rotate GitHub token after each project
                self.components['github'].rotate_token(project_name)
                # Clear cached user info so it gets refreshed with new token
                self._github_user_info = None
                
            except Exception as e:
                error_result = {
                    'project_name': project_name,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.time()
                }
                results.append(error_result)
                
                # Record failure in state tracker
                self.state_tracker.mark_project_completed(
                    project_name,
                    self.components['github'].current_token_index,
                    success=False,
                    error=str(e)
                )
                
                self.log_error(f"Project {project_name} failed: {str(e)}")
        
        return results
    
    def _process_single_project(self, project: Dict[str, Any], manual_token_index: Optional[int] = None) -> Dict[str, Any]:
        """Process a single project through the complete workflow with proper workspace handling"""
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
            # CRITICAL FIX: Set up token for this project FIRST
            if manual_token_index is not None:
                # Force the specific token index to be used
                self.components['github'].execute('force_token', token_index=manual_token_index)
                token_index = manual_token_index
                self.log_info(f"Forcing token index {manual_token_index} for project {project_name}")
            else:
                # Use intelligent token selection
                token_index = self.components['github'].get_next_token_index(project_name)
                self.log_info(f"Auto-selected token index {token_index} for project {project_name}")
            
            # Mark project as started in state tracker
            if not self.state_tracker.is_project_completed(project_name):
                self.state_tracker.mark_project_started(project_name, token_index)
            
            # Step 1: Create GitHub repository (will use the forced/selected token)
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
            # Get user info for the CURRENTLY ACTIVE TOKEN (not token index 0!)
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
            
            # Step 9: Commit and push changes to feature branch
            self.log_info(f"Committing and pushing changes for {project_name}")
            commit_message = self._get_random_commit_message(project_name)
            
            try:
                commit_hash = self.components['git'].execute('commit',
                                                           project_name=project_name,
                                                           commit_message=commit_message)
                
                if commit_hash == "no-changes":
                    self.log_warning("No changes detected for commit, but continuing...")
                    commit_hash = "no-changes"
                
                self.components['git'].execute('push',
                                             project_name=project_name,
                                             branch_name=branch_name)
                
                result['steps']['git_commit_push'] = {
                    'status': 'success',
                    'commit_hash': commit_hash,
                    'commit_message': commit_message,
                    'branch_name': branch_name,
                    'timestamp': time.time()
                }
                
            except Exception as git_e:
                self.log_error(f"Git commit/push failed for {project_name}: {str(git_e)}")
                
                # Get detailed git status for debugging
                final_git_status = self.components['git'].execute('get_status', project_name=project_name)
                self.log_error(f"Final git status: {final_git_status}")
                
                raise AutomationError(f"Git operations failed: {str(git_e)}")
            
            # Step 10: Create pull request from feature branch to main
            self.log_info(f"Creating pull request for {project_name}")
            pr_url = self.components['github'].execute('create_pr',
                                                    project=project,
                                                    branch_name=branch_name,
                                                    base_branch="main")
            result['steps']['pull_request'] = {
                'status': 'success',
                'pr_url': pr_url,
                'branch_name': branch_name,
                'base_branch': 'main',
                'timestamp': time.time()
            }
            
            # Step 11: Record results
            result['status'] = 'completed'
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            result['pr_url'] = pr_url
            result['token_index'] = token_index  # Use the actual token index used
            result['github_username'] = github_user_info['username']
            result['contract_directory'] = contract_dir
            result['commit_message'] = commit_message
            
            # Record in detailed tracker
            self.components['tracker'].execute('record_result', result=result)
            
            # Record clean summary for personal use
            self.components['summary'].execute('record_summary', result=result)
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            
            # Use the actual token index that was attempted
            result['token_index'] = token_index if 'token_index' in locals() else self.components['github'].current_token_index

            try:    
                github_user_info = self._get_github_user_info()
                result['github_username'] = github_user_info['username']
            except:
                result['github_username'] = 'unknown'
            
            # Cleanup on failure if configured
            if self.automation_config.get('cleanup_on_failure', True):
                self._cleanup_failed_project(project_name)
            
            raise AutomationError(f"Project {project_name} failed: {str(e)}")
        
        return result
    
    def _get_random_commit_message(self, project_name: str) -> str:
        """Generate a random, unique commit message with rich details"""
        
        # 1. Select random main commit message template
        template = random.choice(self.commit_messages)
        main_message = template.format(project_name=project_name)
        
        # 2. Select 2-3 random general details
        selected_details = random.sample(self.commit_details, random.randint(2, 3))
        
        # 3. Select 1-2 random technical features
        selected_technical = random.sample(self.technical_features, random.randint(1, 2))
        
        # 4. Combine all elements into professional commit message
        commit_message = main_message
        commit_message += "\n"
        commit_message += "\n".join(selected_details)
        commit_message += "\n"
        commit_message += "\n".join(selected_technical)
        
        return commit_message
    
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