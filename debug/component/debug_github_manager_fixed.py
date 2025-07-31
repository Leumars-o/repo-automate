# debug_github_manager_fixed.py
import sys
import os
sys.path.append('.')

from config.config_manager import ConfigManager
from components.github_manager import GitHubManager
import traceback

def debug_github_manager():
    print("=== GitHub Manager Debug (Fixed) ===")
    
    try:
        # Load the config
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"   Full config keys: {list(config.keys())}")
        github_config = config.get('github', {})
        print(f"   GitHub config keys: {list(github_config.keys())}")
        print(f"   Tokens available: {len(github_config.get('tokens', []))}")
        
        # Try to create GitHubManager with FULL config (not just github section)
        print("\n2. Creating GitHubManager with full config...")
        github_manager = GitHubManager(config)  # Pass full config, not just github_config
        
        print("   ✅ GitHubManager created successfully!")
        
        # Check if tokens attribute exists
        print("\n3. Checking GitHubManager attributes...")
        print(f"   Has 'tokens' attribute: {hasattr(github_manager, 'tokens')}")
        if hasattr(github_manager, 'tokens'):
            print(f"   Tokens count: {len(github_manager.tokens)}")
            print(f"   First token starts with: {github_manager.tokens[0][:10] if github_manager.tokens else 'No tokens'}...")
        
        # Check other attributes
        attrs_to_check = ['config', 'logger', 'github_clients', 'current_client_index']
        for attr in attrs_to_check:
            has_attr = hasattr(github_manager, attr)
            print(f"   Has '{attr}' attribute: {has_attr}")
            if has_attr and attr == 'github_clients':
                clients = getattr(github_manager, attr)
                print(f"      {attr} count: {len(clients) if clients else 0}")
        
        # Try to execute a simple operation
        print("\n4. Testing GitHubManager operations...")
        try:
            # Try to get status (this is what was failing)
            result = github_manager.execute('get_status')
            print(f"   ✅ get_status operation successful: {type(result)}")
            if isinstance(result, dict):
                print(f"      Result keys: {list(result.keys())}")
        except Exception as e:
            print(f"   ❌ get_status operation failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_github_manager()