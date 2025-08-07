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
from typing import Dict, Any, Optional

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
    
    def run_automation(self, skip_completed: bool = True) -> None:
        """Run the complete automation process"""
        try:
            self.logger.info("Starting automation process")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Process all projects with skip_completed option
            results = self.orchestrator.execute('process_all', skip_completed=skip_completed)
            
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
    
    def run_single_project(self, project_name: str, enable_testing: bool = False, token_index: Optional[int] = None) -> None:
        """Run automation for a single project with optional testing and token selection"""
        try:
            projects = self.config_manager.get_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            
            if not project:
                self.logger.error(f"Project '{project_name}' not found in configuration")
                return
            
            # Check if project is already completed
            if self.orchestrator.state_tracker.is_project_completed(project_name):
                print(f"⚠️  Project '{project_name}' has already been completed successfully!")
                print("   Use --force flag to reprocess completed projects (coming soon)")
                return
            
            self.logger.info(f"Running automation for project: {project_name}")
            
            if token_index is not None:
                self.logger.info(f"Using manual token index: {token_index}")
                print(f"🔑 Using token index: {token_index}")
                
                # CRITICAL FIX: Force the GitHub manager to use the specific token
                self.orchestrator.components['github'].execute('force_token', token_index=token_index)
            else:
                print("🔑 Auto-selecting least used available token")
            
            if enable_testing:
                self.logger.info("Testing is ENABLED for this run")
                print("🧪 Testing: ENABLED")
            else:
                self.logger.info("Testing is DISABLED for this run (compile only)")
                print("🧪 Testing: DISABLED (compile only)")
            
            # Execute single project with manual token index
            result = self.orchestrator.execute('process_single', 
                                              project=project, 
                                              manual_token_index=token_index)
            
            print(f"\n📊 Results for {project_name}:")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Duration: {result.get('duration', 0):.2f} seconds")
            print(f"Token Used: Index {result.get('token_index', 'unknown')}")
            
            # Show compilation results
            compile_result = result.get('steps', {}).get('contract_compilation', {})
            if compile_result:
                print(f"\n🔨 Compilation:")
                print(f"  Status: {compile_result.get('status', 'unknown')}")
                print(f"  Attempts: {compile_result.get('attempts', 'unknown')}")
                
                if compile_result.get('has_warnings', False):
                    warnings = compile_result.get('warnings', [])
                    print(f"  ⚠️  Warnings: {len(warnings)} detected")
                    for warning in warnings:
                        print(f"    - {warning.get('message', 'Unknown warning')}")
            
            # Run optional testing if requested
            if enable_testing and result.get('status') == 'completed':
                print(f"\n🧪 Running optional tests...")
                test_result = self.orchestrator.execute('test_contract', 
                                                       project=project, 
                                                       workspace_path=result.get('steps', {}).get('git_clone', {}).get('workspace_path', ''))
                
                print(f"Testing:")
                print(f"  Status: {test_result.get('status', 'unknown')}")
                if test_result.get('test_result'):
                    tr = test_result['test_result'].get('test_results', {})
                    print(f"  Tests Passed: {tr.get('passed', 0)}")
                    print(f"  Tests Failed: {tr.get('failed', 0)}")
                    print(f"  Total Tests: {tr.get('total', 0)}")
            
            if result.get('status') == 'completed':
                print(f"\n✅ Success! Pull Request: {result.get('pr_url', 'N/A')}")
                
                # Record completion in state tracker
                self.orchestrator.state_tracker.mark_project_completed(
                    project_name,
                    result.get('token_index', 0),
                    success=True,
                    duration=result.get('duration', 0),
                    pr_url=result.get('pr_url')
                )
                
            else:
                print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
                
                # Record failure in state tracker
                self.orchestrator.state_tracker.mark_project_completed(
                    project_name,
                    result.get('token_index', 0),
                    success=False,
                    error=result.get('error', 'Unknown error'),
                    duration=result.get('duration', 0)
                )
                
        except Exception as e:
            self.logger.error(f"Single project automation failed: {str(e)}")
            print(f"\n💥 Exception: {str(e)}")
    
    def test_project(self, project_name: str) -> None:
        """Run tests only for a specific project"""
        try:
            projects = self.config_manager.get_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            
            if not project:
                self.logger.error(f"Project '{project_name}' not found in configuration")
                return
            
            # Find the workspace path (assuming project structure)
            workspace_path = f"./workspaces/{project_name}"
            if not Path(workspace_path).exists():
                print(f"❌ Workspace not found: {workspace_path}")
                print("   Run the project first with: python main.py --action single --project {project_name}")
                return
            
            print(f"🧪 Running tests for project: {project_name}")
            test_result = self.orchestrator.execute('test_contract', 
                                                   project=project, 
                                                   workspace_path=workspace_path)
            
            print(f"\nTest Results:")
            print(f"Status: {test_result.get('status', 'unknown')}")
            
            if test_result.get('test_result'):
                tr = test_result['test_result'].get('test_results', {})
                print(f"Tests Passed: {tr.get('passed', 0)}")
                print(f"Tests Failed: {tr.get('failed', 0)}")
                print(f"Total Tests: {tr.get('total', 0)}")
                
                if test_result['status'] == 'failed':
                    print(f"Error Details: {test_result['test_result'].get('errors', 'Unknown error')}")
            
        except Exception as e:
            self.logger.error(f"Project testing failed: {str(e)}")
    
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
    
    def show_state_summary(self) -> None:
        """Show current state tracking summary"""
        try:
            summary = self.orchestrator.state_tracker.get_state_summary()
            github_status = self.orchestrator.components['github'].get_status()
            
            print("\n" + "="*60)
            print("STATE TRACKING SUMMARY")
            print("="*60)
            
            # Token state
            token_state = summary['token_state']
            print(f"\n🔑 Token State:")
            print(f"  Total Tokens: {token_state['total_tokens']}")
            print(f"  Current Index: {token_state['current_index']}")
            print(f"  Blacklisted: {token_state['blacklisted_tokens']}")
            print(f"  Rotations: {token_state['rotation_count']}")
            print(f"  Available: {github_status['available_tokens']}")
            print(f"  Available Indices: {github_status['available_token_indices']}")
            
            # Project state
            project_state = summary['project_state']
            print(f"\n📋 Project State:")
            print(f"  Completed: {project_state['completed_projects']}")
            print(f"  Failed: {project_state['failed_projects']}")
            print(f"  In Progress: {project_state['in_progress']}")
            print(f"  Total Executions: {project_state['total_executions']}")
            
            # Show incomplete projects
            all_projects = self.config_manager.get_projects()
            incomplete = self.orchestrator.state_tracker.get_incomplete_projects(all_projects)
            
            if incomplete:
                print(f"\n⏳ Incomplete Projects ({len(incomplete)}):")
                for project in incomplete:
                    print(f"  - {project['name']}")
            else:
                print(f"\n🎉 All projects completed!")
            
            print("\n" + "="*60)
            
        except Exception as e:
            self.logger.error(f"Failed to show state summary: {str(e)}")
    
    def reset_state(self, reset_tokens: bool = False, reset_projects: bool = False) -> None:
        """Reset state tracking"""
        try:
            self.orchestrator.state_tracker.reset_state(reset_tokens, reset_projects)
            print("✅ State reset successfully")
        except Exception as e:
            self.logger.error(f"Failed to reset state: {str(e)}")
            print(f"❌ Failed to reset state: {str(e)}")
    
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
    parser = argparse.ArgumentParser(description='Smart Contract Automation System with State Tracking')
    
    parser.add_argument('--config', '-c', default='config/settings.yaml',
                       help='Path to configuration file')
    parser.add_argument('--action', '-a', choices=['run', 'status', 'summary', 'single', 'test', 'state', 'reset-state'],
                       default='run', help='Action to perform')
    parser.add_argument('--project', '-p', help='Project name (for single project mode)')
    parser.add_argument('--token-index', '-t', type=int, 
                       help='Manual token index to use (0-based)')
    parser.add_argument('--with-tests', action='store_true',
                       help='Enable testing for single project mode')
    parser.add_argument('--skip-completed', action='store_true', default=True,
                       help='Skip already completed projects in batch mode (default: True)')
    parser.add_argument('--force', action='store_true',
                       help='Force reprocessing of completed projects')
    parser.add_argument('--reset-tokens', action='store_true',
                       help='Reset token state tracking')
    parser.add_argument('--reset-projects', action='store_true',
                       help='Reset project completion tracking')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Validate token index if provided
    if args.token_index is not None and args.token_index < 0:
        print("Error: --token-index must be 0 or greater")
        sys.exit(1)
    
    # Initialize CLI
    cli = AutomationCLI()
    cli.setup(args.config)
    
    # Validate token index against available tokens
    if args.token_index is not None:
        github_status = cli.orchestrator.components['github'].get_status()
        total_tokens = github_status['total_tokens']
        
        if args.token_index >= total_tokens:
            print(f"Error: --token-index {args.token_index} is out of range (0-{total_tokens-1})")
            print(f"Available tokens: {total_tokens}")
            sys.exit(1)
        
        available_indices = github_status['available_token_indices']
        if args.token_index not in available_indices:
            print(f"Warning: Token index {args.token_index} may be blacklisted or unavailable")
            print(f"Available token indices: {available_indices}")
            confirm = input("Continue anyway? (y/N): ").lower()
            if confirm != 'y':
                sys.exit(1)
    
    # Execute requested action
    if args.action == 'run':
        # Override skip_completed if force is used
        skip_completed = args.skip_completed and not args.force
        
        if args.force:
            print("🔄 Force mode: Will reprocess completed projects")
        elif skip_completed:
            print("⏭️  Skip mode: Will skip completed projects")
        else:
            print("🔄 Full mode: Will process all projects")
        
        cli.run_automation(skip_completed=skip_completed)
        
    elif args.action == 'status':
        cli.show_status()
        
    elif args.action == 'summary':
        cli.show_summary()
        
    elif args.action == 'single':
        if not args.project:
            print("Error: --project is required for single project mode")
            print("Usage: python main.py --action single --project PROJECT_NAME [--token-index N] [--with-tests]")
            print("\nExamples:")
            print("  python main.py --action single --project Escrow-chain")
            print("  python main.py --action single --project Escrow-chain --token-index 2")
            print("  python main.py --action single --project Escrow-chain --with-tests")
            sys.exit(1)
        cli.run_single_project(args.project, enable_testing=args.with_tests, token_index=args.token_index)
        
    elif args.action == 'test':
        if not args.project:
            print("Error: --project is required for test mode")
            print("Usage: python main.py --action test --project PROJECT_NAME")
            sys.exit(1)
        cli.test_project(args.project)
        
    elif args.action == 'state':
        cli.show_state_summary()
        
    elif args.action == 'reset-state':
        if not (args.reset_tokens or args.reset_projects):
            print("Error: Must specify --reset-tokens and/or --reset-projects")
            print("Usage:")
            print("  python main.py --action reset-state --reset-tokens")
            print("  python main.py --action reset-state --reset-projects") 
            print("  python main.py --action reset-state --reset-tokens --reset-projects")
            sys.exit(1)
        
        # Confirmation prompt
        reset_items = []
        if args.reset_tokens:
            reset_items.append("token usage tracking")
        if args.reset_projects:
            reset_items.append("project completion tracking")
        
        print(f"⚠️  This will reset: {', '.join(reset_items)}")
        confirm = input("Are you sure? This action cannot be undone! (type 'yes' to confirm): ")
        
        if confirm.lower() == 'yes':
            cli.reset_state(args.reset_tokens, args.reset_projects)
        else:
            print("Reset cancelled")


if __name__ == "__main__":
    main()