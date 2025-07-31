#!/usr/bin/env python3
"""
YAML loader that automatically resolves external YAML file references
Supports: file:path/to/file.yaml syntax
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Union

class YAMLFileReferenceLoader:
    """Custom YAML loader that resolves external YAML file references"""
    
    def load_yaml(self, file_path: str) -> Dict[Any, Any]:
        """Load YAML and resolve any external YAML file references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            # Recursively process the data to resolve file references
            return self._resolve_references(data, Path(file_path).parent)
            
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return {}
    
    def _resolve_references(self, data: Any, base_path: Path) -> Any:
        """Recursively resolve external YAML file references"""
        if isinstance(data, dict):
            return {key: self._resolve_references(value, base_path) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._resolve_references(item, base_path) for item in data]
        elif isinstance(data, str):
            return self._resolve_string_reference(data, base_path)
        else:
            return data
    
    def _resolve_string_reference(self, value: str, base_path: Path) -> Any:
        """Resolve a string that might be an external YAML file reference"""
        # Check for file reference: file:path/to/file.yaml
        if value.startswith('file:'):
            file_path = value[5:]  # Remove 'file:' prefix
            return self._load_external_yaml(file_path, base_path)
        else:
            # Regular string, return as-is
            return value
    
    def _load_external_yaml(self, file_path: str, base_path: Path) -> Any:
        """Load content from external YAML file"""
        # Handle relative paths
        if not Path(file_path).is_absolute():
            full_path = base_path / file_path
        else:
            full_path = Path(file_path)
        
        if not full_path.exists():
            print(f"Warning: Referenced YAML file '{full_path}' not found")
            return []
        
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            print(f"Loaded external YAML: {full_path}")
            
            # Recursively resolve references in the loaded file too
            return self._resolve_references(data, full_path.parent)
            
        except yaml.YAMLError as e:
            print(f"Error parsing external YAML file {full_path}: {e}")
            return []
        except Exception as e:
            print(f"Error loading external YAML file {full_path}: {e}")
            return []

def create_sample_files():
    """Create sample YAML files and main config for testing"""
    
    # Create directories
    secrets_dir = Path('secrets')
    data_dir = Path('data')
    secrets_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    
    # Create tokens.yaml
    tokens_data = {
        'tokens': [
            'ghp_sample_token_1_from_yaml',
            'ghp_sample_token_2_from_yaml',
            'ghp_sample_token_3_from_yaml'
        ]
    }
    
    with open('secrets/tokens.yaml', 'w') as f:
        yaml.dump(tokens_data, f, default_flow_style=False)
    
    # Create projects.yaml
    projects_data = {
        'projects': [
            {
                'name': 'DeFiLendingProtocol',
                'description': 'A decentralized lending protocol with collateral management',
                'blockchain': 'stacks',
                'contract_type': 'clarity',
                'priority': 'high'
            },
            {
                'name': 'NFTMarketplace',
                'description': 'NFT trading platform with royalty distribution',
                'blockchain': 'stacks',
                'contract_type': 'clarity',
                'priority': 'medium'
            },
            {
                'name': 'TokenSwapDEX',
                'description': 'Decentralized exchange for token swapping',
                'blockchain': 'stacks',
                'contract_type': 'clarity',
                'priority': 'low'
            }
        ]
    }
    
    with open('data/projects.yaml', 'w') as f:
        yaml.dump(projects_data, f, default_flow_style=False)
    
    # Create test projects (smaller set for testing)
    test_projects_data = {
        'projects': [
            {
                'name': 'TestContract',
                'description': 'Simple test contract for development',
                'blockchain': 'stacks',
                'contract_type': 'clarity',
                'priority': 'high'
            }
        ]
    }
    
    with open('data/test-projects.yaml', 'w') as f:
        yaml.dump(test_projects_data, f, default_flow_style=False)
    
    # Create main config with file references
    config_data = {
        'github': {
            'tokens': 'file:secrets/tokens.yaml',  # External YAML reference
            'default_settings': {
                'private': False,
                'auto_init': True,
                'has_issues': True,
                'has_projects': False,
                'has_wiki': False
            }
        },
        'projects': 'file:data/projects.yaml',  # External YAML reference
        'smart_contracts': {
            'blockchain': 'stacks',
            'language': 'clarity',
            'testing_framework': 'clarinet',
            'deployment_network': 'testnet',
            'contract_template': 'basic'
        },
        'automation': {
            'max_retries': 3,
            'retry_delay': 5,
            'timeout': 300,
            'parallel_workers': 3,
            'log_level': 'INFO',
            'cleanup_on_failure': True
        },
        'results': {
            'output_file': 'results/automation_results.json',
            'backup_results': True,
            'track_metrics': True
        },
        'claude': {
            'model': 'claude-sonnet-4',
            'timeout': 120,
            'max_tokens': 4000,
            'temperature': 0.1
        }
    }
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    # Create test config that uses test projects
    test_config_data = config_data.copy()
    test_config_data['projects'] = 'file:data/test-projects.yaml'
    
    with open('config-test.yaml', 'w') as f:
        yaml.dump(test_config_data, f, default_flow_style=False, sort_keys=False)
    
    print("Created sample files:")
    print("- secrets/tokens.yaml (private tokens)")
    print("- data/projects.yaml (main project list)")
    print("- data/test-projects.yaml (test project list)")
    print("- config.yaml (main config with file references)")
    print("- config-test.yaml (test config using test projects)")

def test_yaml_loading():
    """Test loading YAML with external file references"""
    print("Testing YAML with External File References")
    print("=" * 55)
    
    loader = YAMLFileReferenceLoader()
    
    # Test main config
    print("\nLoading main config (config.yaml):")
    print("-" * 40)
    
    data = loader.load_yaml('config.yaml')
    
    if data:
        print("✓ Main config loaded successfully")
        
        # Test tokens
        if 'github' in data and 'tokens' in data['github']:
            tokens = data['github']['tokens']
            if isinstance(tokens, dict) and 'tokens' in tokens:
                token_list = tokens['tokens']
                print(f"✓ Found {len(token_list)} tokens from external file")
                
                # Show masked tokens
                for i, token in enumerate(token_list, 1):
                    masked = token[:10] + "..." if len(token) > 10 else token
                    print(f"   {i}. {masked}")
            else:
                print("✗ Tokens not loaded correctly")
        
        # Test projects
        if 'projects' in data:
            projects = data['projects']
            if isinstance(projects, dict) and 'projects' in projects:
                project_list = projects['projects']
                print(f"✓ Found {len(project_list)} projects from external file")
                
                # Show project names
                for i, project in enumerate(project_list, 1):
                    name = project.get('name', 'Unknown')
                    priority = project.get('priority', 'N/A')
                    print(f"   {i}. {name} (priority: {priority})")
            else:
                print("✗ Projects not loaded correctly")
        
        print(f"\n✓ Your code works the same way:")
        print(f"   tokens = data['github']['tokens']['tokens']")
        print(f"   projects = data['projects']['projects']")
    
    # Test config with test projects
    print(f"\n" + "-" * 40)
    print("Loading test config (config-test.yaml):")
    print("-" * 40)
    
    test_data = loader.load_yaml('config-test.yaml')
    
    if test_data and 'projects' in test_data:
        projects = test_data['projects']
        if isinstance(projects, dict) and 'projects' in projects:
            project_list = projects['projects']
            print(f"✓ Test config loaded {len(project_list)} test projects")
            for project in project_list:
                print(f"   - {project.get('name', 'Unknown')}")

def demo_usage():
    """Show how to use this in your existing code"""
    print("\n" + "=" * 55)
    print("USAGE IN YOUR EXISTING CODE:")
    print("=" * 55)
    
    print("""
# OLD way:
# with open('config.yaml', 'r') as file:
#     data = yaml.safe_load(file)

# NEW way (just change these 2 lines):
loader = YAMLFileReferenceLoader()
data = loader.load_yaml('config.yaml')

# Everything else stays exactly the same:
tokens = data['github']['tokens']['tokens']  # List of token strings
projects = data['projects']['projects']      # List of project dicts

# Your existing loops work unchanged:
for token in tokens:
    print(f"Using token: {token}")

for project in projects:
    name = project['name']
    blockchain = project['blockchain']
    print(f"Processing {name} on {blockchain}")
""")

def main():
    """Main test function"""
    
    # Create sample files if they don't exist
    if not Path('secrets').exists() or not Path('data').exists():
        print("Creating sample files...")
        create_sample_files()
        print()
    
    # Test the loading
    test_yaml_loading()
    
    # Show usage
    demo_usage()
    
    print("\n✓ Benefits of this approach:")
    print("  - Keep tokens private (add secrets/ to .gitignore)")
    print("  - Share project configs safely")
    print("  - Switch between test/prod projects easily")
    print("  - Your existing code needs minimal changes")
    print("  - Pure YAML - no other file formats to learn")

if __name__ == "__main__":
    main()