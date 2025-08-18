# components/summary_tracker.py
from typing import Dict, Any, List
import json
import time
from pathlib import Path
from datetime import datetime
from core.base_component import BaseComponent
from core.exceptions import AutomationError

class SummaryTracker(BaseComponent):
    """Tracks clean, final results for personal use - separate from detailed automation logs"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.summary_config = config.get('summary_tracker', {})
        self.output_file = self.summary_config.get('output_file', 'results/project_summary.json')
        self.summaries = []
        super().__init__(config, logger)
    
    def _initialize(self) -> None:
        """Initialize summary tracker"""
        # Create results directory if it doesn't exist
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing summaries if file exists
        self._load_existing_summaries()
        
        self.log_info(f"Summary tracker initialized. Output file: {self.output_file}")
    
    def _load_existing_summaries(self) -> None:
        """Load existing summaries from file"""
        try:
            if Path(self.output_file).exists():
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
                    self.summaries = data.get('summaries', [])
                    self.log_info(f"Loaded {len(self.summaries)} existing project summaries")
            else:
                self.summaries = []
                self.log_info("No existing summary file found, starting fresh")
        except Exception as e:
            self.log_warning(f"Failed to load existing summaries: {str(e)}")
            self.summaries = []
    
    def record_project_summary(self, result: Dict[str, Any]) -> None:
        """Record a clean project summary with just the essential details"""
        try:
            # Extract essential information
            project_name = result.get('project_name', 'Unknown Project')
            status = result.get('status', 'unknown')
            
            # Only record successful projects
            if status != 'completed':
                self.log_info(f"Skipping summary for incomplete project: {project_name}")
                return
            
            # Extract GitHub user info
            github_username = result.get('github_username', 'unknown')
            
            # Try to get email from git_config step
            git_config_step = result.get('steps', {}).get('git_config', {})
            github_email = git_config_step.get('user_email', 'unknown@example.com')
            
            # Get pull request URL
            pr_step = result.get('steps', {}).get('pull_request', {})
            pull_request_url = pr_step.get('pr_url', result.get('pr_url', 'No PR created'))
            
            # Get timing information
            start_time = result.get('start_time', time.time())
            end_time = result.get('end_time', time.time())
            duration = result.get('duration', end_time - start_time)
            
            # Get token information
            token_index = result.get('token_index', 'unknown')
            
            # Create clean summary
            summary = {
                'project_name': project_name,
                'github_username': github_username,
                'github_email': github_email,
                'pull_request_url': pull_request_url,
                'completion_timestamp': datetime.fromtimestamp(end_time).isoformat(),
                'duration_seconds': round(duration, 2),
                'token_index': token_index,
                'status': 'completed'
            }
            
            # Check if this project already exists (avoid duplicates)
            existing_index = self._find_existing_project(project_name, github_username)
            if existing_index is not None:
                # Update existing entry
                self.summaries[existing_index] = summary
                self.log_info(f"Updated existing summary for {project_name} by {github_username}")
            else:
                # Add new entry
                self.summaries.append(summary)
                self.log_info(f"Added new summary for {project_name} by {github_username}")
            
            # Save to file
            self._save_summaries()
            
        except Exception as e:
            self.log_error(f"Failed to record project summary: {str(e)}")
    
    def _find_existing_project(self, project_name: str, github_username: str) -> int:
        """Find if a project already exists for the same user"""
        for i, summary in enumerate(self.summaries):
            if (summary.get('project_name') == project_name and 
                summary.get('github_username') == github_username):
                return i
        return None
    
    def _save_summaries(self) -> None:
        """Save summaries to JSON file"""
        try:
            # Create summary data with metadata
            data = {
                'metadata': {
                    'file_description': 'Clean project completion summaries for personal tracking',
                    'last_updated': datetime.now().isoformat(),
                    'total_projects': len(self.summaries),
                    'successful_projects': len([s for s in self.summaries if s.get('status') == 'completed'])
                },
                'summaries': self.summaries
            }
            
            # Write to file with nice formatting
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.log_info(f"Saved {len(self.summaries)} project summaries to {self.output_file}")
            
        except Exception as e:
            self.log_error(f"Failed to save summaries: {str(e)}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked summaries"""
        if not self.summaries:
            return {
                'total_projects': 0,
                'unique_users': 0,
                'recent_projects': []
            }
        
        # Count unique users
        unique_users = len(set(s.get('github_username', 'unknown') for s in self.summaries))
        
        # Get recent projects (last 5)
        recent_projects = sorted(
            self.summaries, 
            key=lambda x: x.get('completion_timestamp', ''), 
            reverse=True
        )[:5]
        
        return {
            'total_projects': len(self.summaries),
            'unique_users': unique_users,
            'recent_projects': [
                {
                    'project_name': p.get('project_name'),
                    'github_username': p.get('github_username'),
                    'completion_timestamp': p.get('completion_timestamp')
                }
                for p in recent_projects
            ]
        }
    
    def get_projects_by_user(self, github_username: str) -> List[Dict[str, Any]]:
        """Get all projects for a specific user"""
        return [
            summary for summary in self.summaries 
            if summary.get('github_username') == github_username
        ]
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute summary tracker operation"""
        operations = {
            'record_summary': self.record_project_summary,
            'get_stats': self.get_summary_stats,
            'get_by_user': self.get_projects_by_user
        }
        
        if operation not in operations:
            raise AutomationError(f"Unknown summary tracker operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Summary tracker operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up and save final state"""
        self._save_summaries()
        self.log_info("Summary tracker cleanup completed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get summary tracker status"""
        stats = self.get_summary_stats()
        return {
            'output_file': self.output_file,
            'total_summaries': len(self.summaries),
            'stats': stats
        }
    
    def save_immediately(self) -> None:
        """Save summaries immediately (called after each successful project)"""
        self._save_summaries()
        self.log_info("Summaries saved immediately after project completion")