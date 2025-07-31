#!/usr/bin/env python3
# config_test.py
"""
Test script for the enhanced ConfigManager with external YAML file support
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

# Import the enhanced ConfigManager
from config.config_manager import ConfigManager, ConfigurationError

def test_config_manager():
    """Test the enhanced ConfigManager"""
    print("Testing Enhanced ConfigManager")
    print("=" * 50)
    
    try:
        # Initialize ConfigManager with your config file
        config_manager = ConfigManager("config/settings.yaml")
        
        print("✓ ConfigManager initialized successfully")
        
        # Get configuration info
        info = config_manager.get_config_info()
        print(f"✓ Config file: {info['config_file']}")
        print(f"✓ Sections: {', '.join(info['sections'])}")
        print(f"✓ Token count: {info['token_count']}")
        print(f"✓ Project count: {info['project_count']}")
        
        # Test GitHub tokens
        print(f"\n" + "-" * 30)
        print("GitHub Tokens:")
        print("-" * 30)
        
        tokens = config_manager.get_github_tokens()
        for i, token in enumerate(tokens, 1):
            # Mask tokens for security
            masked_token = token[:10] + "..." + token[-4:] if len(token) > 14 else token[:6] + "..."
            print(f"  {i}. {masked_token}")
        
        # Test projects
        print(f"\n" + "-" * 30)
        print("Projects:")
        print("-" * 30)
        
        projects = config_manager.get_projects()
        for i, project in enumerate(projects, 1):
            name = project.get('name', 'Unknown')
            description = project.get('description', 'No description')
            priority = project.get('priority', 'N/A')
            blockchain = project.get('blockchain', 'N/A')
            
            print(f"  {i}. {name}")
            print(f"     Description: {description}")
            print(f"     Priority: {priority}, Blockchain: {blockchain}")
            print()
        
        # Test other sections
        print("-" * 30)
        print("Other Configuration Sections:")
        print("-" * 30)
        
        # Smart contracts config
        sc_config = config_manager.get_smart_contract_config()
        print(f"Smart Contracts - Blockchain: {sc_config.get('blockchain', 'N/A')}")
        print(f"Smart Contracts - Language: {sc_config.get('language', 'N/A')}")
        
        # Automation settings
        auto_config = config_manager.get_automation_settings()
        print(f"Automation - Max Retries: {auto_config.get('max_retries', 'N/A')}")
        print(f"Automation - Parallel Workers: {auto_config.get('parallel_workers', 'N/A')}")
        
        # Test getting specific section
        github_config = config_manager.get_section('github')
        print(f"GitHub - Default Private: {github_config.get('default_settings', {}).get('private', 'N/A')}")
        
        print(f"\n✓ All tests passed!")
        
        # Show usage example
        print(f"\n" + "=" * 50)
        print("USAGE EXAMPLE:")
        print("=" * 50)
        print("""
# Your existing code can use it like this:
config_manager = ConfigManager("config/settings.yaml")

# Get tokens (now loaded from secrets/tokens.yaml)
tokens = config_manager.get_github_tokens()
for token in tokens:
    # Use token for GitHub API calls
    pass

# Get projects (now loaded from data/projects.yaml)  
projects = config_manager.get_projects()
for project in projects:
    name = project['name']
    description = project['description']
    blockchain = project['blockchain']
    # Process project
    pass
        """)
        
    except ConfigurationError as e:
        print(f"✗ Configuration Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        return False
    
    return True

def show_file_structure():
    """Show the expected file structure"""
    print("\nExpected File Structure:")
    print("-" * 30)
    print("""
project_root/
├── config/
│   ├── settings.yaml      # Main config with file references
│   └── config_manager.py  # Enhanced ConfigManager
├── secrets/
│   └── tokens.yaml        # Private tokens (add to .gitignore)
├── data/
│   └── projects.yaml      # Project configurations
└── test_config.py         # This test script
    """)

def main():
    """Main function"""
    show_file_structure()
    
    print("\n" + "=" * 60)
    
    success = test_config_manager()
    
    if success:
        print(f"\n✓ Benefits of this approach:")
        print("  - Tokens are kept private in secrets/tokens.yaml")
        print("  - Projects can be shared safely in data/projects.yaml") 
        print("  - Same ConfigManager interface as before")
        print("  - Easy to switch between different token/project sets")
        print("  - Pure YAML - no need to learn new formats")
        print(f"\n✓ Don't forget to add 'secrets/' to your .gitignore!")
    else:
        print(f"\nPlease check your file structure and YAML files.")

if __name__ == "__main__":
    main()