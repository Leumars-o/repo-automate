# debug_config_detailed.py
import sys
import os
sys.path.append('.')

from config.config_manager import ConfigManager
import json

def debug_config():
    print("=== Configuration Debug ===")
    
    try:
        # Load the config
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print("1. Raw config structure:")
        print(json.dumps(list(config.keys()), indent=2))
        
        print("\n2. GitHub section:")
        github_config = config.get('github', {})
        print(f"   Keys: {list(github_config.keys())}")
        print(f"   Tokens type: {type(github_config.get('tokens', 'NOT_FOUND'))}")
        
        
        print("\n3. Testing GitHub token access:")
        try:
            tokens = config_manager.get_github_tokens()
            print(f"   Retrieved tokens count: {len(tokens)}")
            print(f"   First token starts with: {tokens[0][:10] if tokens else 'No tokens'}...")
        except Exception as e:
            print(f"   Error getting tokens: {e}")


        print("\n4. Projects section:")
        projects = config.get('projects', [])
        print(f"   Type: {type(projects)}")
        print(f"   Length: {len(projects) if isinstance(projects, list) else 'N/A'}")
        if isinstance(projects, list) and len(projects) > 0:
            print(f"   First project keys: {list(projects[0].keys()) if isinstance(projects[0], dict) else 'Not a dict'}")
        
        print("\n5. Testing project access:")
        try:
            projects = config_manager.get_projects()
            print(f"   Retrieved projects count: {len(projects)}")
            if projects:
                print(f"   First project: {projects[0].get('name', 'No name')}")
                print("\n=====================================================================\n")
        except Exception as e:
            print(f"   Error getting projects: {e}")
            
    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()