# core/orchestrator.py
from typing import Dict, Any, List, Optional
import time
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

class SmartContractOrchestrator(BaseComponent):
    """Main orchestrator that coordinates all components"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.components = {}
        self.results = []
        self.automation_config = config.get('automation', {})
        self.max_workers = self.automation_config.get('parallel_workers', 3)
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
        
        self.log_info("All components initialized successfully")
    
    def process_all_projects(self) -> List[Dict[str, Any]]:
        """Process all projects with parallel execution"""
        projects = self.config.get('projects', [])
        
        if not projects:
            self.log_warning("No projects found in configuration")
            return []
        
        self.log_info(f"Starting automation for {len(projects)} projects")
        
        # Process projects in parallel
        if self.max_workers > 1:
            return self._process_projects_parallel(projects)
        else:
            return self._process_projects_sequential(projects)
    
    def _process_projects_parallel(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all projects
            future_to_project = {
                executor.submit(self._process_single_project, project): project 
                for project in projects
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.log_info(f"Completed project: {project['name']}")
                except Exception as e:
                    error_result = {
                        'project_name': project['name'],
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    results.append(error_result)
                    self.log_error(f"Project {project['name']} failed: {str(e)}")
                
                # Rotate GitHub token after each project
                try:
                    self.components['github'].rotate_token()
                except Exception as e:
                    self.log_warning(f"Failed to rotate GitHub token: {str(e)}")
        
        return results
    
    def _process_projects_sequential(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process projects sequentially"""
        results = []
        
        for project in projects:
            try:
                result = self._process_single_project(project)
                results.append(result)
                self.log_info(f"Completed project: {project['name']}")
                
                # Rotate GitHub token after each project
                self.components['github'].rotate_token()
                
            except Exception as e:
                error_result = {
                    'project_name': project['name'],
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.time()
                }
                results.append(error_result)
                self.log_error(f"Project {project['name']} failed: {str(e)}")
        
        return results
    
    def _process_single_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single project through the complete workflow"""
        project_name = project['name']
        start_time = time.time()
        
        result = {
            'project_name': project_name,
            'status': 'in_progress',
            'start_time': start_time,
            'steps': {}
        }
        
        try:
            # Step 1: Create GitHub repository
            self.log_info(f"Creating GitHub repository for {project_name}")
            repo_url = self.components['github'].execute('create_repo', project=project)
            result['steps']['github_repo'] = {
                'status': 'success',
                'repo_url': repo_url,
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
            
            # Step 3: Setup Git configuration
            self.log_info(f"Setting up Git configuration for {project_name}")
            self.components['git'].execute('setup_config',
                                         project_name=project_name,
                                         user_name="Smart Contract Bot",
                                         user_email="bot@smartcontract.dev")
            result['steps']['git_config'] = {
                'status': 'success',
                'timestamp': time.time()
            }
            
            # Step 4: Initialize smart contract environment
            self.log_info(f"Initializing smart contract environment for {project_name}")
            self.components['contract'].execute('initialize',
                                              workspace_path=workspace_path,
                                              project=project)
            result['steps']['contract_init'] = {
                'status': 'success',
                'timestamp': time.time()
            }
            
            # Step 5: Generate smart contract with Claude
            self.log_info(f"Generating smart contract for {project_name}")
            contract_file = self.components['claude'].execute('generate_contract',
                                                            project=project,
                                                            workspace_path=workspace_path)
            result['steps']['contract_generation'] = {
                'status': 'success',
                'contract_file': contract_file,
                'timestamp': time.time()
            }
            
            # Step 6: Compile and test contract (with error fixing loop)
            self.log_info(f"Compiling and testing contract for {project_name}")
            contract_result = self._compile_and_test_loop(project, workspace_path)
            result['steps']['contract_testing'] = contract_result
            
            # Step 7: Commit and push changes
            self.log_info(f"Committing and pushing changes for {project_name}")
            commit_hash = self.components['git'].execute('commit',
                                                       project_name=project_name,
                                                       commit_message=f"Add {project_name} smart contract")
            
            self.components['git'].execute('push',
                                         project_name=project_name,
                                         branch_name="main")
            
            result['steps']['git_commit_push'] = {
                'status': 'success',
                'commit_hash': commit_hash,
                'timestamp': time.time()
            }
            
            # Step 8: Create pull request
            self.log_info(f"Creating pull request for {project_name}")
            pr_url = self.components['github'].execute('create_pr',
                                                     project=project,
                                                     branch_name="main")
            result['steps']['pull_request'] = {
                'status': 'success',
                'pr_url': pr_url,
                'timestamp': time.time()
            }
            
            # Step 9: Record results
            result['status'] = 'completed'
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            result['pr_url'] = pr_url
            
            self.components['tracker'].execute('record_result', result=result)
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['end_time'] = time.time()
            result['duration'] = result['end_time'] - start_time
            
            # Cleanup on failure if configured
            if self.automation_config.get('cleanup_on_failure', True):
                self._cleanup_failed_project(project_name)
            
            raise AutomationError(f"Project {project_name} failed: {str(e)}")
        
        return result
    
    def _compile_and_test_loop(self, project: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Compile and test contract with error fixing loop"""
        max_retries = self.automation_config.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                # Compile contract
                compile_result = self.components['contract'].execute('compile',
                                                                   workspace_path=workspace_path,
                                                                   contract_file="")
                
                if compile_result['success']:
                    # Test contract
                    test_result = self.components['contract'].execute('test',
                                                                    workspace_path=workspace_path)
                    
                    if test_result['success']:
                        return {
                            'status': 'success',
                            'attempts': attempt + 1,
                            'compile_result': compile_result,
                            'test_result': test_result,
                            'timestamp': time.time()
                        }
                    else:
                        error_message = test_result.get('errors', 'Test failed')
                        self.log_warning(f"Test failed (attempt {attempt + 1}): {error_message}")
                        
                        if attempt < max_retries - 1:
                            # Fix the error with Claude
                            self.components['claude'].execute('fix_error',
                                                            project=project,
                                                            workspace_path=workspace_path,
                                                            error_message=error_message)
                else:
                    error_message = compile_result.get('errors', 'Compilation failed')
                    self.log_warning(f"Compilation failed (attempt {attempt + 1}): {error_message}")
                    
                    if attempt < max_retries - 1:
                        # Fix the error with Claude
                        self.components['claude'].execute('fix_error',
                                                        project=project,
                                                        workspace_path=workspace_path,
                                                        error_message=error_message)
                
                # Wait before retry
                time.sleep(self.automation_config.get('retry_delay', 5))
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return {
                        'status': 'failed',
                        'attempts': attempt + 1,
                        'error': str(e),
                        'timestamp': time.time()
                    }
                
                self.log_warning(f"Contract testing attempt {attempt + 1} failed: {str(e)}")
                time.sleep(self.automation_config.get('retry_delay', 5))
        
        return {
            'status': 'failed',
            'attempts': max_retries,
            'error': 'Maximum retry attempts exceeded',
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