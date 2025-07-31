#!/usr/bin/env python3
# debug_git_operations.py


import logging
from config.config_manager import ConfigManager

def debug_git_operations():
    """Debug the GitOperations initialization"""
    # Simple logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== GitOperations Debug ===")
    
    try:
        # Load configuration
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   Full config keys: {list(config.keys())}")
        
        # Check if automation config exists
        if 'automation' in config:
            print(f"   Automation config: {config['automation']}")
        else:
            print("   ❌ No 'automation' config found")
            
        # Import GitOperations
        print("2. Importing GitOperations...")
        from components.git_operations import GitOperations
        
        # Check the first few lines of the __init__ method
        print("3. Checking GitOperations class...")
        print(f"   Class: {GitOperations}")
        
        # Try to create an instance
        print("4. Creating GitOperations instance...")
        logger = logging.getLogger("test")
        git_ops = GitOperations(config, logger)
        
        print("5. ✅ GitOperations created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_git_operations()