# components/result_tracker.py
from typing import Dict, Any, List, Optional
import json
import csv
from pathlib import Path
import time
from core.base_component import BaseComponent
from core.exceptions import AutomationError

class ResultTracker(BaseComponent):
    """Tracks and persists automation results"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.results_config = config.get('results', {})
        self.output_file = Path(self.results_config.get('output_file', 'results/automation_results.json'))
        self.backup_enabled = self.results_config.get('backup_results', True)
        self.track_metrics = self.results_config.get('track_metrics', True)
        self.results = []
        self.metrics = {
            'total_projects': 0,
            'successful_projects': 0,
            'failed_projects': 0,
            'total_duration': 0,
            'average_duration': 0,
            'github_tokens_used': 0,
            'contracts_generated': 0,
            'pull_requests_created': 0
        }
        super().__init__(config, logger)
        
    def _initialize(self) -> None:
        """Initialize result tracker"""
        # Create results directory if it doesn't exist
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing results if available
        self._load_existing_results()
        
        self.log_info(f"Result tracker initialized. Output file: {self.output_file}")
    
    def _load_existing_results(self) -> None:
        """Load existing results from file"""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
                    self.results = data.get('results', [])
                    self.metrics = data.get('metrics', self.metrics)
                    self.log_info(f"Loaded {len(self.results)} existing results")
            except Exception as e:
                self.log_warning(f"Failed to load existing results: {str(e)}")
    
    def record_result(self, result: Dict[str, Any]) -> None:
        """Record a single project result"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in result:
                result['timestamp'] = time.time()
            
            # Add to results list
            self.results.append(result)
            
            # Update metrics
            if self.track_metrics:
                self._update_metrics(result)
            
            # Save to file
            self._save_results()
            
            self.log_info(f"Recorded result for project: {result.get('project_name', 'Unknown')}")
            
        except Exception as e:
            raise AutomationError(f"Failed to record result: {str(e)}")
    
    def _update_metrics(self, result: Dict[str, Any]) -> None:
        """Update metrics based on result"""
        self.metrics['total_projects'] += 1
        
        if result.get('status') == 'completed':
            self.metrics['successful_projects'] += 1
            
            # Track pull requests created
            if result.get('pr_url'):
                self.metrics['pull_requests_created'] += 1
                
        elif result.get('status') == 'failed':
            self.metrics['failed_projects'] += 1
        
        # Update duration metrics
        duration = result.get('duration', 0)
        if duration > 0:
            self.metrics['total_duration'] += duration
            self.metrics['average_duration'] = (
                self.metrics['total_duration'] / self.metrics['total_projects']
            )
        
        # Track contracts generated
        if result.get('steps', {}).get('contract_generation', {}).get('status') == 'success':
            self.metrics['contracts_generated'] += 1
    
    def _save_results(self) -> None:
        """Save results to file"""
        try:
            # Prepare data structure
            data = {
                'metadata': {
                    'generated_at': time.time(),
                    'total_results': len(self.results),
                    'version': '1.0'
                },
                'metrics': self.metrics,
                'results': self.results
            }
            
            # Save main results file
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup()
            
        except Exception as e:
            raise AutomationError(f"Failed to save results: {str(e)}")
    
    def _create_backup(self) -> None:
        """Create backup of results"""
        try:
            timestamp = int(time.time())
            backup_file = self.output_file.parent / f"backup_{timestamp}_{self.output_file.name}"
            
            with open(backup_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'backup_created_at': time.time(),
                        'original_file': str(self.output_file)
                    },
                    'metrics': self.metrics,
                    'results': self.results
                }, f, indent=2, default=str)
            
        except Exception as e:
            self.log_warning(f"Failed to create backup: {str(e)}")
    
    def export_to_csv(self, csv_file: str = None) -> str:
        """Export results to CSV format"""
        try:
            if not csv_file:
                csv_file = str(self.output_file.parent / 'automation_results.csv')
            
            csv_path = Path(csv_file)
            
            # Flatten results for CSV export
            flattened_results = []
            for result in self.results:
                flat_result = {
                    'project_name': result.get('project_name', ''),
                    'status': result.get('status', ''),
                    'duration': result.get('duration', 0),
                    'start_time': result.get('start_time', 0),
                    'end_time': result.get('end_time', 0),
                    'pr_url': result.get('pr_url', ''),
                    'error': result.get('error', ''),
                    'github_repo_status': result.get('steps', {}).get('github_repo', {}).get('status', ''),
                    'contract_generation_status': result.get('steps', {}).get('contract_generation', {}).get('status', ''),
                    'contract_testing_status': result.get('steps', {}).get('contract_testing', {}).get('status', ''),
                    'pull_request_status': result.get('steps', {}).get('pull_request', {}).get('status', '')
                }
                flattened_results.append(flat_result)
            
            # Write to CSV
            if flattened_results:
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=flattened_results[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_results)
            
            self.log_info(f"Exported {len(flattened_results)} results to CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            raise AutomationError(f"Failed to export to CSV: {str(e)}")
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Generate summary report"""
        try:
            # Calculate success rate
            success_rate = 0
            if self.metrics['total_projects'] > 0:
                success_rate = (self.metrics['successful_projects'] / self.metrics['total_projects']) * 100
            
            # Get recent results (last 10)
            recent_results = self.results[-10:] if len(self.results) >= 10 else self.results
            
            # Calculate average duration for successful projects
            successful_durations = [
                r.get('duration', 0) for r in self.results 
                if r.get('status') == 'completed' and r.get('duration', 0) > 0
            ]
            avg_successful_duration = sum(successful_durations) / len(successful_durations) if successful_durations else 0
            
            # Get common error types
            error_types = {}
            for result in self.results:
                if result.get('status') == 'failed' and result.get('error'):
                    error_type = result['error'].split(':')[0]  # Get error type before colon
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            return {
                'summary': {
                    'total_projects': self.metrics['total_projects'],
                    'successful_projects': self.metrics['successful_projects'],
                    'failed_projects': self.metrics['failed_projects'],
                    'success_rate': round(success_rate, 2),
                    'contracts_generated': self.metrics['contracts_generated'],
                    'pull_requests_created': self.metrics['pull_requests_created']
                },
                'performance': {
                    'total_duration': round(self.metrics['total_duration'], 2),
                    'average_duration': round(self.metrics['average_duration'], 2),
                    'average_successful_duration': round(avg_successful_duration, 2)
                },
                'error_analysis': {
                    'common_errors': error_types,
                    'failure_rate': round(100 - success_rate, 2)
                },
                'recent_activity': {
                    'last_10_results': [
                        {
                            'project_name': r.get('project_name', ''),
                            'status': r.get('status', ''),
                            'duration': r.get('duration', 0),
                            'timestamp': r.get('timestamp', 0)
                        } for r in recent_results
                    ]
                },
                'generated_at': time.time()
            }
            
        except Exception as e:
            raise AutomationError(f"Failed to generate summary report: {str(e)}")
    
    def get_project_results(self, project_name: str) -> List[Dict[str, Any]]:
        """Get results for a specific project"""
        return [r for r in self.results if r.get('project_name') == project_name]
    
    def get_failed_projects(self) -> List[Dict[str, Any]]:
        """Get all failed project results"""
        return [r for r in self.results if r.get('status') == 'failed']
    
    def get_successful_projects(self) -> List[Dict[str, Any]]:
        """Get all successful project results"""
        return [r for r in self.results if r.get('status') == 'completed']
    
    def clear_results(self) -> None:
        """Clear all results (use with caution)"""
        if self.backup_enabled:
            self._create_backup()
        
        self.results = []
        self.metrics = {
            'total_projects': 0,
            'successful_projects': 0,
            'failed_projects': 0,
            'total_duration': 0,
            'average_duration': 0,
            'github_tokens_used': 0,
            'contracts_generated': 0,
            'pull_requests_created': 0
        }
        
        self._save_results()
        self.log_info("All results cleared")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute result tracker operation"""
        operations = {
            'record_result': self.record_result,
            'export_csv': self.export_to_csv,
            'get_summary': self.get_summary_report,
            'get_project_results': self.get_project_results,
            'get_failed': self.get_failed_projects,
            'get_successful': self.get_successful_projects,
            'clear_results': self.clear_results
        }
        
        if operation not in operations:
            raise AutomationError(f"Unknown result tracker operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Result tracker operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up result tracker resources"""
        try:
            self._save_results()
        except Exception as e:
            self.log_error(f"Failed to save results during cleanup: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get result tracker status"""
        return {
            'total_results': len(self.results),
            'output_file': str(self.output_file),
            'backup_enabled': self.backup_enabled,
            'track_metrics': self.track_metrics,
            'metrics': self.metrics
        }