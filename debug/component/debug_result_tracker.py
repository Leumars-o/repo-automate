#!/usr/bin/env python3
# debug_result_tracker.py

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_result_tracker():
    """Debug ResultTracker component"""
    print("=== ResultTracker Debug ===")
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('test')
    
    try:
        print("1. Loading configuration...")
        # Try different config loader locations
        try:
            from config.config_loader import load_config
        except ImportError:
            try:
                from config_loader import load_config
            except ImportError:
                # Use a simple config loader
                import json
                config_path = Path('config/config.yaml')
                if config_path.exists():
                    import yaml
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                else:
                    # Minimal config for testing
                    config = {
                        'results': {
                            'output_file': 'results/automation_results.json',
                            'backup_results': True,
                            'track_metrics': True
                        }
                    }
        
        if 'load_config' in locals():
            config = load_config()
        print(f"   Full config keys: {list(config.keys())}")
        print(f"   Results config: {config.get('results', {})}")
        
        print("2. Importing ResultTracker...")
        from components.result_tracker import ResultTracker
        
        print("3. Creating ResultTracker instance...")
        result_tracker = ResultTracker(config, logger)
        
        print("4. ✅ ResultTracker created successfully!")
        
        return result_tracker
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_result_tracker()