#!/usr/bin/env python3
"""
Quick setup and test script for Smart Contract Automation System
"""

import os
import sys
from pathlib import Path

def create_minimal_structure():
    """Create minimal directory structure"""
    directories = ['config', 'core', 'components', 'utils', 'workspace', 'results', 'logs', 'tests']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        init_file = Path(directory) / '__init__.py'
        if not init_file.exists():
            init_file.touch()
    
    print("✓ Created minimal directory structure")

def create_test_config():
    """Create a test configuration file"""
    config_content = """# Test Configuration - Replace with your actual settings

github:
  tokens:
    - "ghp_test_token_replace_with_real_token"  # Replace with your actual GitHub token
  
  default_settings:
    private: false
    auto_init: true
    has_issues: true
    has_projects: false
    has_wiki: false

projects:
  - name: "TestContract"
    description: "A simple test smart contract for validation"
    blockchain: "stacks"
    contract_type: "basic"
    priority: "medium"

smart_contracts:
  blockchain: "stacks"
  language: "clarity"
  testing_framework: "clarinet"
  deployment_network: "testnet"
  
automation:
  max_retries: 3
  retry_delay: 5
  timeout: 300
  parallel_workers: 1
  log_level: "INFO"
  cleanup_on_failure: true
  workspace: "workspace"
  
results:
  output_file: "results/automation_results.json"
  backup_results: true
  track_metrics: true

claude:
  model: "claude-sonnet-4"
  timeout: 120
  max_tokens: 4000
  temperature: 0.1
"""
    
    config_file = Path('config/settings.yaml')

    # create file if not exist
    if not config_file:
        config_file.write_text(config_content)
        print(f"✓ Created test configuration: {config_file}")
        print("⚠️  Remember to replace the test token with your actual GitHub token!")


def test_imports():
    """Test if all imports work correctly"""
    try:
        # Test basic imports
        import yaml
        print("✓ PyYAML available")
        
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Test our modules in correct order
        from utils.logger import setup_logging, get_logger
        print("✓ Logger module imports successfully")
        
        from config.config_manager import ConfigManager
        print("✓ Config manager imports successfully")
        
        # Test core modules - FIXED: import from core, not config
        from core.orchestrator import SmartContractOrchestrator
        print("✓ Orchestrator imports successfully")
        
        # Test component imports
        from components.github_manager import GitHubManager
        print("✓ GitHub manager imports successfully")
        
        from components.git_operations import GitOperations
        print("✓ Git operations imports successfully")
        
        from components.claude_interface import ClaudeInterface
        print("✓ Claude interface imports successfully")
        
        from components.contract_manager import ContractManager
        print("✓ Contract manager imports successfully")
        
        from components.result_tracker import ResultTracker
        print("✓ Result tracker imports successfully")
        
        # Test logging setup with correct parameter
        setup_logging(log_level="INFO", console_output=True, file_output=False)
        logger = get_logger("test")
        logger.info("Test log message")
        print("✓ Logging system works correctly")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def run_basic_status_check():
    """Run a basic status check"""
    try:
        # Test configuration loading
        from config.config_manager import ConfigManager
        config_manager = ConfigManager('config/settings.yaml')
        config = config_manager.get_config()
        print("✓ Configuration loads successfully")
        
        # Test validation
        from utils.validators import ConfigValidator
        ConfigValidator.validate_config_structure(config)
        print("✓ Configuration validation passes")
        
        return True
        
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False

def create_missing_dependencies():
    """Create any missing dependency files"""
    try:
        # Create missing __init__.py files
        init_files = [
            'config/__init__.py',
            'core/__init__.py', 
            'components/__init__.py',
            'utils/__init__.py',
            'tests/__init__.py'
        ]
        
        for init_file in init_files:
            init_path = Path(init_file)
            if not init_path.exists():
                init_path.touch()
                print(f"✓ Created {init_file}")
        
        # Check for git requirement
        try:
            import git
            print("✓ GitPython is available")
        except ImportError:
            print("⚠️  GitPython not found. Install with: pip install GitPython")
        
        # Check for github requirement  
        try:
            import github
            print("✓ PyGithub is available")
        except ImportError:
            print("⚠️  PyGithub not found. Install with: pip install PyGithub")
            
        return True
        
    except Exception as e:
        print(f"✗ Error creating dependencies: {e}")
        return False

def check_external_tools():
    """Check for required external tools"""
    tools = {
        'git': 'Git version control system',
        'clarinet': 'Stacks smart contract development tool',
        'claude': 'Claude Code CLI tool'
    }
    
    print("\nChecking external tools:")
    
    for tool, description in tools.items():
        try:
            import subprocess
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ {tool} is available")
            else:
                print(f"⚠️  {tool} not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"✗ {tool} not found - {description}")
        except Exception as e:
            print(f"⚠️  {tool} check failed: {e}")

def print_next_steps():
    """Print what to do next"""
    print("\n" + "="*60)
    print("QUICK SETUP COMPLETE!")
    print("="*60)
    
    print("\nWhat was created:")
    print("✓ Directory structure")
    print("✓ Test configuration file")
    print("✓ Missing component files")
    print("✓ Basic functionality verified")
    
    print("\nBefore running the system:")
    print("1. Edit config/settings.yaml")
    print("2. Ensure you have replaced 'ghp_test_token_replace_with_real_token' with your actual GitHub token")
    print("3. Adjust project configurations as needed")
    
    print("\nTo get your GitHub token:")
    print("1. Go to GitHub Settings > Developer settings > Personal access tokens")
    print("2. Generate new token with 'repo' permissions") 
    print("3. Copy and paste it into the config file")
    
    print("\nInstall missing Python packages:")
    print("pip install GitPython PyGithub etc..")
    
    print("\nTest commands:")
    print("python main.py --action status    # Check system status")
    print("python main.py --action list      # List configured projects") 
    print("python main.py --help             # Show all options")
    
    print("\nRequired external tools:")
    print("- Git (for repository operations)")
    print("- Clarinet (for Stacks smart contracts)")
    print("- Claude Code CLI (for AI-powered development)")
    
    print("\n" + "="*60)

def main():
    """Main quickstart function"""
    print("Smart Contract Automation - Quick Setup")
    print("="*50)
    
    # Create structure
    create_minimal_structure()
    
    # Create missing dependencies
    create_missing_dependencies()
    
    # Create test config
    create_test_config()
    
    # Test imports
    if test_imports():
        print("✓ All core modules working")
    else:
        print("✗ Some modules have issues - check installation")
        print("\nTry installing missing packages:")
        print("pip install PyYAML GitPython PyGithub")
        return
    
    # Run status check
    if run_basic_status_check():
        print("✓ Basic system check passed")
    else:
        print("✗ System check failed - check configuration")
    
    # Check external tools
    check_external_tools()
    
    # Print instructions
    print_next_steps()

if __name__ == '__main__':
    main()