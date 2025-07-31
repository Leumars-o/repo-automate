#!/usr/bin/env python3
# debug/debug_runner.py
"""
Centralized debug runner for the automation program.
Provides both individual component debugging and full system diagnosis.
Works with existing debug files in debug/component/ folder.
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add debug/component to path for importing debug modules
debug_component_path = Path(__file__).parent / "component"
sys.path.insert(0, str(debug_component_path))

class DebugRunner:
    """Centralized debug runner for systematic program diagnosis"""
    
    def __init__(self):
        self.setup_logging()
        self.results = {}
        
    def setup_logging(self):
        """Setup logging for debug operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('DebugRunner')
        
    def run_config_debug(self) -> Dict[str, Any]:
        """Debug configuration management using existing debug_config.py"""
        print("\n" + "="*60)
        print("🔧 DEBUGGING CONFIGURATION")
        print("="*60)
        
        result = {
            'component': 'config',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug_config function
            import debug_config
            
            # Capture the output by running the debug function
            # Since debug_config.py has a debug_config() function, we'll call it
            if hasattr(debug_config, 'debug_config'):
                debug_config.debug_config()
                result['status'] = 'success'
                result['details'] = {'message': 'Config debug completed successfully'}
                print(f"✅ Config debug completed (using debug_config.py)")
            else:
                # Fallback to our own logic
                from config.config_manager import ConfigManager
                
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                result['details'] = {
                    'config_keys': list(config.keys()),
                    'github_tokens_count': len(config_manager.get_github_tokens()),
                    'projects_count': len(config_manager.get_projects()),
                    'sections': list(config.keys())
                }
                
                print(f"✅ Config loaded successfully")
                print(f"   - Sections: {', '.join(config.keys())}")
                print(f"   - GitHub tokens: {len(config_manager.get_github_tokens())}")
                print(f"   - Projects: {len(config_manager.get_projects())}")
                
                result['status'] = 'success'
            
        except Exception as e:
            error_msg = f"Config error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_github_debug(self) -> Dict[str, Any]:
        """Debug GitHub manager using existing debug_github_manager_fixed.py"""
        print("\n" + "="*60)
        print("🐙 DEBUGGING GITHUB MANAGER")
        print("="*60)
        
        result = {
            'component': 'github_manager',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug function
            import debug_github_manager_fixed
            
            if hasattr(debug_github_manager_fixed, 'debug_github_manager'):
                debug_github_manager_fixed.debug_github_manager()
                result['status'] = 'success'
                result['details'] = {'message': 'GitHub Manager debug completed successfully'}
                print(f"✅ GitHub Manager debug completed (using debug_github_manager_fixed.py)")
            else:
                # Fallback to our own logic
                from config.config_manager import ConfigManager
                from components.github_manager import GitHubManager
                
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                github_manager = GitHubManager(config)
                
                # Test basic operations
                status_result = github_manager.execute('get_status')
                
                result['details'] = {
                    'tokens_available': len(getattr(github_manager, 'tokens', [])),
                    'clients_created': len(getattr(github_manager, 'github_clients', [])),
                    'status_check': 'success' if status_result else 'failed'
                }
                
                print(f"✅ GitHub Manager initialized successfully")
                print(f"   - Tokens: {result['details']['tokens_available']}")
                print(f"   - Clients: {result['details']['clients_created']}")
                print(f"   - Status check: {result['details']['status_check']}")
                
                result['status'] = 'success'
            
        except Exception as e:
            error_msg = f"GitHub Manager error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_contract_debug(self) -> Dict[str, Any]:
        """Debug contract manager using existing debug_contract_manager.py"""
        print("\n" + "="*60)
        print("📜 DEBUGGING CONTRACT MANAGER")
        print("="*60)
        
        result = {
            'component': 'contract_manager',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug function
            import debug_contract_manager
            
            if hasattr(debug_contract_manager, 'debug_contract_manager'):
                debug_contract_manager.debug_contract_manager()
                result['status'] = 'success'
                result['details'] = {'message': 'Contract Manager debug completed successfully'}
                print(f"✅ Contract Manager debug completed (using debug_contract_manager.py)")
            else:
                # Fallback to our own logic
                from config.config_manager import ConfigManager
                from components.contract_manager import ContractManager
                
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                contract_manager = ContractManager(config, self.logger)
                
                result['details'] = {
                    'blockchain_support': config.get('smart_contracts', {}).get('blockchain', 'unknown'),
                    'language': config.get('smart_contracts', {}).get('language', 'unknown'),
                    'initialized': True
                }
                
                print(f"✅ Contract Manager initialized successfully")
                print(f"   - Blockchain: {result['details']['blockchain_support']}")
                print(f"   - Language: {result['details']['language']}")
                
                result['status'] = 'success'
            
        except Exception as e:
            error_msg = f"Contract Manager error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_orchestrator_debug(self) -> Dict[str, Any]:
        """Debug orchestrator using existing debug_orchestrator.py"""
        print("\n" + "="*60)
        print("🎼 DEBUGGING ORCHESTRATOR")
        print("="*60)
        
        result = {
            'component': 'orchestrator',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug function
            import debug_orchestrator
            
            if hasattr(debug_orchestrator, 'debug_orchestrator'):
                debug_orchestrator.debug_orchestrator()
                result['status'] = 'success'
                result['details'] = {'message': 'Orchestrator debug completed successfully'}
                print(f"✅ Orchestrator debug completed (using debug_orchestrator.py)")
            else:
                # Fallback to our own logic
                from config.config_manager import ConfigManager
                from core.orchestrator import SmartContractOrchestrator
                
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                orchestrator = SmartContractOrchestrator(config)
                
                # Check key attributes
                attributes = {
                    'has_components': hasattr(orchestrator, 'components'),
                    'has_config': hasattr(orchestrator, 'config'),
                    'has_logger': hasattr(orchestrator, 'logger'),
                    'has_github_manager': hasattr(orchestrator, 'github_manager'),
                    'has_contract_manager': hasattr(orchestrator, 'smart_contract_manager')
                }
                
                result['details'] = attributes
                
                print(f"✅ Orchestrator initialized successfully")
                for attr, exists in attributes.items():
                    status = "✅" if exists else "❌"
                    print(f"   {status} {attr}: {exists}")
                
                result['status'] = 'success'
            
        except Exception as e:
            error_msg = f"Orchestrator error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_result_tracker_debug(self) -> Dict[str, Any]:
        """Debug result tracker using existing debug_result_tracker.py"""
        print("\n" + "="*60)
        print("📊 DEBUGGING RESULT TRACKER")
        print("="*60)
        
        result = {
            'component': 'result_tracker',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug function
            import debug_result_tracker
            
            if hasattr(debug_result_tracker, 'debug_result_tracker'):
                debug_result_tracker.debug_result_tracker()
                result['status'] = 'success'
                result['details'] = {'message': 'Result Tracker debug completed successfully'}
                print(f"✅ Result Tracker debug completed (using debug_result_tracker.py)")
            else:
                # Fallback to our own logic
                from config.config_manager import ConfigManager
                from components.result_tracker import ResultTracker
                
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                result_tracker = ResultTracker(config, self.logger)
                
                result['details'] = {
                    'output_file': config.get('results', {}).get('output_file', 'unknown'),
                    'backup_enabled': config.get('results', {}).get('backup_results', False),
                    'metrics_enabled': config.get('results', {}).get('track_metrics', False)
                }
                
                print(f"✅ Result Tracker initialized successfully")
                print(f"   - Output file: {result['details']['output_file']}")
                print(f"   - Backup enabled: {result['details']['backup_enabled']}")
                print(f"   - Metrics enabled: {result['details']['metrics_enabled']}")
                
                result['status'] = 'success'
            
        except Exception as e:
            error_msg = f"Result Tracker error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_git_operations_debug(self) -> Dict[str, Any]:
        """Debug git operations using existing debug_git_operations.py"""
        print("\n" + "="*60)
        print("🔧 DEBUGGING GIT OPERATIONS")
        print("="*60)
        
        result = {
            'component': 'git_operations',
            'status': 'unknown',
            'errors': [],
            'details': {}
        }
        
        try:
            # Import and run the existing debug function
            import debug_git_operations
            
            if hasattr(debug_git_operations, 'debug_git_operations'):
                debug_git_operations.debug_git_operations()
                result['status'] = 'success'
                result['details'] = {'message': 'Git Operations debug completed successfully'}
                print(f"✅ Git Operations debug completed (using debug_git_operations.py)")
            else:
                # If no specific function, just report success
                result['status'] = 'success'
                result['details'] = {'message': 'Git Operations module imported successfully'}
                print(f"✅ Git Operations module accessible")
            
        except Exception as e:
            error_msg = f"Git Operations error: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'failed'
            print(f"❌ {error_msg}")
            if self.logger.level <= logging.DEBUG:
                traceback.print_exc()
                
        return result
    
    def run_full_system_debug(self) -> Dict[str, Any]:
        """Run complete system debug"""
        print("\n" + "🚀" + "="*58 + "🚀")
        print("🔍 FULL SYSTEM DIAGNOSTIC")
        print("🚀" + "="*58 + "🚀")
        
        start_time = datetime.now()
        
        # Run all component debugs
        debug_methods = [
            self.run_config_debug,
            self.run_github_debug,
            self.run_contract_debug,
            self.run_orchestrator_debug,
            self.run_result_tracker_debug,
            self.run_git_operations_debug
        ]
        
        results = []
        for debug_method in debug_methods:
            try:
                result = debug_method()
                results.append(result)
                self.results[result['component']] = result
            except Exception as e:
                error_result = {
                    'component': debug_method.__name__,
                    'status': 'failed',
                    'errors': [f"Debug method failed: {str(e)}"],
                    'details': {}
                }
                results.append(error_result)
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_count = len(results)
        
        print("\n" + "="*60)
        print("📋 DIAGNOSTIC SUMMARY")
        print("="*60)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Successful: {success_count}/{total_count}")
        print(f"❌ Failed: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        else:
            print(f"\n⚠️  {total_count - success_count} COMPONENTS NEED ATTENTION")
            for result in results:
                if result['status'] == 'failed':
                    print(f"   ❌ {result['component']}: {', '.join(result['errors'])}")
        
        return {
            'summary': {
                'duration': duration,
                'success_count': success_count,
                'total_count': total_count,
                'overall_status': 'healthy' if success_count == total_count else 'issues_detected'
            },
            'components': results
        }
    
    def save_debug_report(self, results: Dict[str, Any], filename: Optional[str] = None):
        """Save debug results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_report_{timestamp}.json"
        
        debug_dir = Path(__file__).parent
        report_path = debug_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Debug report saved to: {report_path}")

def main():
    """Main debug runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug the automation program')
    parser.add_argument('component', nargs='?', 
                       choices=['config', 'github', 'contract', 'orchestrator', 'result_tracker', 'git_operations', 'full'],
                       default='full',
                       help='Component to debug (default: full)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--save-report', '-s', action='store_true',
                       help='Save debug report to file')
    
    args = parser.parse_args()
    
    # Setup verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = DebugRunner()
    
    # Map component names to methods
    component_map = {
        'config': runner.run_config_debug,
        'github': runner.run_github_debug,
        'contract': runner.run_contract_debug,
        'orchestrator': runner.run_orchestrator_debug,
        'result_tracker': runner.run_result_tracker_debug,
        'git_operations': runner.run_git_operations_debug,
        'full': runner.run_full_system_debug
    }
    
    # Run the requested debug
    debug_method = component_map[args.component]
    results = debug_method()
    
    # Save report if requested
    if args.save_report:
        runner.save_debug_report(results)
    
    return results

if __name__ == "__main__":
    main()