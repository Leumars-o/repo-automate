#!/usr/bin/env python3
# debug_contract_manager.py


import logging
from config.config_manager import ConfigManager

def debug_contract_manager():
    """Debug the ContractManager initialization"""
    # Simple logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== ContractManager Debug ===")
    
    try:
        # Load configuration
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   Full config keys: {list(config.keys())}")
        
        # Check smart_contracts config
        if 'smart_contracts' in config:
            print(f"   Smart contracts config: {config['smart_contracts']}")
        else:
            print("   ❌ No 'smart_contracts' config found")
            
        # Import ContractManager
        print("2. Importing ContractManager...")
        from components.contract_manager import ContractManager
        
        # Try to create an instance
        print("3. Creating ContractManager instance...")
        logger = logging.getLogger("test")
        contract_manager = ContractManager(config, logger)
        
        print("4. ✅ ContractManager created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_contract_manager()