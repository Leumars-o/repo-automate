#!/usr/bin/env python3
# debug_orchestrator.py


import logging
from config.config_manager import ConfigManager

def debug_orchestrator():
    """Debug the SmartContractOrchestrator initialization"""
    # Simple logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== Orchestrator Debug ===")
    
    try:
        # Load configuration
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   Full config keys: {list(config.keys())}")
        
        # Import the orchestrator
        print("2. Importing SmartContractOrchestrator...")
        from core.orchestrator import SmartContractOrchestrator
        
        # Check the class definition
        print("3. Checking SmartContractOrchestrator class...")
        print(f"   Class: {SmartContractOrchestrator}")
        print(f"   MRO: {[cls.__name__ for cls in SmartContractOrchestrator.__mro__]}")
        
        # Try to create an instance
        print("4. Creating SmartContractOrchestrator instance...")
        orchestrator = SmartContractOrchestrator(config)
        
        print("5. Checking orchestrator attributes...")
        attrs = dir(orchestrator)
        print(f"   Available attributes: {[attr for attr in attrs if not attr.startswith('_')]}")
        
        # Check if components attribute exists
        if hasattr(orchestrator, 'components'):
            print(f"   ✅ Has 'components' attribute: {type(orchestrator.components)}")
            if hasattr(orchestrator.components, '__dict__'):
                print(f"   Components content: {vars(orchestrator.components)}")
        else:
            print("   ❌ Missing 'components' attribute")
            
        # Check other key attributes
        for attr in ['config', 'logger', 'github_manager', 'smart_contract_manager']:
            if hasattr(orchestrator, attr):
                print(f"   ✅ Has '{attr}' attribute")
            else:
                print(f"   ❌ Missing '{attr}' attribute")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_orchestrator()