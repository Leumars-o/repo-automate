# main.py
"""
Smart Contract Automation - Main Entry Point
===========================================

This is the main entry point for the smart contract automation system.
It loads configuration, initializes the orchestrator, and provides a CLI interface.
"""

import sys
import argparse
import signal
import time
from pathlib import Path
from typing import Dict, Any

from config.config_manager import ConfigManager
from core.orchestrator import SmartContractOrchestrator
from core.exceptions import AutomationError, ConfigurationError
from utils.logger import setup_logging, get_logger

class AutomationCLI:
    """Command line interface for the automation system"""
    
    def __init__(self):
        self.orchestrator = None
        self.config_manager = None
        self.logger = None
    
    def setup(self, config_path: str = "config/settings.yaml") -> None:
        """Setup the automation system"""
        try:
            # Load configuration
            self.config_manager = ConfigManager(config_path)
            config = self.config_manager.get_config()
            
            # Setup logging with correct parameters
            setup_logging(
                log_level=config.get('automation', {}).get('log_level', 'INFO'),
                log_dir='logs',
                console_output=True,
                file_output=True,
                json_format=False
            )
            
            # Get logger instance
            self.logger = get_logger('automation.main')
            
            # Initialize orchestrator
            self.orchestrator = SmartContractOrchestrator(config, self.logger)
            
            self.logger.info("Automation system initialized successfully")
            
        except Exception as e:
            print(f"Failed to setup automation system: {str(e)}")
            sys.exit(1)
    
    def run_automation(self) -> None:
        """Run the complete automation process"""
        try:
            self.logger.info("Starting automation process")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Process all projects
            results = self.orchestrator.execute('process_all')
            
            # Generate and display summary
            summary = self.orchestrator.components['tracker'].execute('get_summary')
            self._display_summary(summary)
            
            # Export results
            csv_file = self.orchestrator.components['tracker'].execute('export_csv')
            self.logger.info(f"Results exported to: {csv_file}")
            
        except KeyboardInterrupt:
            self.logger.info("Automation interrupted by user")
        except Exception as e:
            self.logger.error(f"Automation failed: {str(e)}")
            sys.exit(1)
        finally:
            self._cleanup()
    
    def run_single_project(self, project_name: str) -> None:
        """Run automation for a single project"""
        try:
            projects = self.config_manager.get_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            
            if not project:
                self.logger.error(f"Project '{project_name}' not found in configuration")
                return
            
            self.logger.info(f"Running automation for project: {project_name}")
            result = self.orchestrator.execute('process_single', project=project)
            
            print(f"\nProject: {project_name}")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Duration: {result.get('duration', 0):.2f} seconds")
            
            if result.get('status') == 'completed':
                print(f"Pull Request: {result.get('pr_url', 'N/A')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Single project automation failed: {str(e)}")
    
    def show_status(self) -> None:
        """Show current automation status"""
        try:
            status = self.orchestrator.execute('get_status')
            
            print("\n=== Automation Status ===")
            print(f"Total Projects: {status.get('total_projects', 0)}")
            print(f"Completed: {status.get('completed_projects', 0)}")
            print(f"Failed: {status.get('failed_projects', 0)}")
            
            # Show component statuses
            print("\n=== Component Status ===")
            for name, component_status in status.get('component_statuses', {}).items():
                print(f"{name.capitalize()}: {'✓' if 'error' not in component_status else '✗'}")
                
        except Exception as e:
            self.logger.error(f"Failed to get status: {str(e)}")
    
    def show_summary(self) -> None:
        """Show automation summary report"""
        try:
            summary = self.orchestrator.components['tracker'].execute('get_summary')
            self._display_summary(summary)
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {str(e)}")
    
    def _display_summary(self, summary: Dict[str, Any]) -> None:
        """Display summary report"""
        print("\n" + "="*50)
        print("AUTOMATION SUMMARY REPORT")
        print("="*50)
        
        # Overall metrics
        overall = summary.get('summary', {})
        print(f"\nOverall Results:")
        print(f"  Total Projects: {overall.get('total_projects', 0)}")
        print(f"  Successful: {overall.get('successful_projects', 0)}")
        print(f"  Failed: {overall.get('failed_projects', 0)}")
        print(f"  Success Rate: {overall.get('success_rate', 0)}%")
        print(f"  Contracts Generated: {overall.get('contracts_generated', 0)}")
        print(f"  Pull Requests Created: {overall.get('pull_requests_created', 0)}")
        
        # Performance metrics
        performance = summary.get('performance', {})
        print(f"\nPerformance:")
        print(f"  Total Duration: {performance.get('total_duration', 0):.2f} seconds")
        print(f"  Average Duration: {performance.get('average_duration', 0):.2f} seconds")
        print(f"  Avg Successful Duration: {performance.get('average_successful_duration', 0):.2f} seconds")
        
        # Error analysis
        error_analysis = summary.get('error_analysis', {})
        common_errors = error_analysis.get('common_errors', {})
        if common_errors:
            print(f"\nCommon Errors:")
            for error_type, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error_type}: {count} occurrences")
        
        print("\n" + "="*50)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Clean up resources"""
        if self.orchestrator:
            self.orchestrator.cleanup()
            self.logger.info("Automation system cleaned up")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Smart Contract Automation System')
    
    parser.add_argument('--config', '-c', default='config/settings.yaml',
                       help='Path to configuration file')
    parser.add_argument('--action', '-a', choices=['run', 'status', 'summary', 'single'],
                       default='run', help='Action to perform')
    parser.add_argument('--project', '-p', help='Project name (for single project mode)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = AutomationCLI()
    cli.setup(args.config)
    
    # Execute requested action
    if args.action == 'run':
        cli.run_automation()
    elif args.action == 'status':
        cli.show_status()
    elif args.action == 'summary':
        cli.show_summary()
    elif args.action == 'single':
        if not args.project:
            print("Error: --project is required for single project mode")
            sys.exit(1)
        cli.run_single_project(args.project)


if __name__ == "__main__":
    main()