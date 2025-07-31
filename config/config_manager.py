# config/config_manager.py
import yaml
import os
from typing import Dict, Any, List
from pathlib import Path
from core.exceptions import ConfigurationError

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
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}")
    
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
            raise ConfigurationError(f"Referenced YAML file not found: {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            # Recursively resolve references in the loaded file too
            return self._resolve_references(data, full_path.parent)
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing external YAML file {full_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading external YAML file {full_path}: {e}")

class ConfigManager:
    """Manages configuration loading and validation with external YAML file support"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self._config = None
        self._yaml_loader = YAMLFileReferenceLoader()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file with external reference support"""
        try:
            self._config = self._yaml_loader.load_yaml(str(self.config_path))
            self._process_config()
            self._validate_config()
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            else:
                raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _process_config(self) -> None:
        """Process configuration after loading"""
        if not self._config:
            raise ConfigurationError("Configuration is empty")
        
        # Handle GitHub tokens - now they should be loaded from external file
        github_config = self._config.get('github', {})
        tokens = github_config.get('tokens', [])
        
        # If tokens were loaded from external YAML file, they might be nested
        if isinstance(tokens, dict) and 'tokens' in tokens:
            github_config['tokens'] = tokens['tokens']
        elif isinstance(tokens, str):
            # Fallback: handle string tokens as before (single token or file path)
            tokens_file = Path(tokens)
            if tokens_file.exists():
                try:
                    with open(tokens_file, 'r') as f:
                        file_content = f.read().strip()
                        # Handle different formats
                        if file_content.startswith('[') and file_content.endswith(']'):
                            # JSON array format
                            import json
                            github_config['tokens'] = json.loads(file_content)
                        else:
                            # Newline separated tokens
                            github_config['tokens'] = [
                                line.strip() for line in file_content.split('\n') 
                                if line.strip() and not line.strip().startswith('#')
                            ]
                except Exception as e:
                    raise ConfigurationError(f"Failed to load tokens from {tokens_file}: {e}")
            else:
                # File doesn't exist, treat as a single token
                github_config['tokens'] = [tokens] if tokens else []
        elif not isinstance(tokens, list):
            # Convert single token to list
            github_config['tokens'] = [tokens] if tokens else []
        
        # Handle projects - they might be loaded from external YAML file
        projects = self._config.get('projects', [])
        if isinstance(projects, dict) and 'projects' in projects:
            self._config['projects'] = projects['projects']
        elif not isinstance(projects, list):
            raise ConfigurationError("Projects configuration must be a list or contain a 'projects' key")
    
    def _validate_config(self) -> None:
        """Validate configuration structure"""
        required_sections = ['github', 'projects', 'smart_contracts', 'automation']
        for section in required_sections:
            if section not in self._config:
                raise ConfigurationError(f"Missing required config section: {section}")
        
        # Validate GitHub tokens
        github_tokens = self._config['github'].get('tokens', [])
        if not github_tokens:
            raise ConfigurationError("No GitHub tokens found in configuration")
        
        # Basic token validation (check if they look like GitHub tokens)
        for i, token in enumerate(github_tokens):
            if not isinstance(token, str) or len(token.strip()) < 10:
                raise ConfigurationError(f"Invalid GitHub token at index {i}")
        
        # Validate projects
        projects = self._config.get('projects', [])
        if not isinstance(projects, list):
            raise ConfigurationError("Projects must be a list")
        
        for i, project in enumerate(projects):
            if not isinstance(project, dict):
                raise ConfigurationError(f"Project at index {i} must be a dictionary")
            if 'name' not in project:
                raise ConfigurationError(f"Project at index {i} missing required 'name' field")
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration"""
        return self._config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific configuration section"""
        if section not in self._config:
            raise ConfigurationError(f"Configuration section '{section}' not found")
        return self._config[section].copy()
    
    def get_github_tokens(self) -> List[str]:
        """Get list of GitHub tokens"""
        return self._config['github']['tokens']
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of projects to process"""
        return self._config['projects']
    
    def get_smart_contract_config(self) -> Dict[str, Any]:
        """Get smart contract configuration"""
        return self._config['smart_contracts']
    
    def get_automation_settings(self) -> Dict[str, Any]:
        """Get automation settings"""
        return self._config['automation']
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """Update a configuration value"""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
    
    def save_config(self) -> None:
        """Save configuration back to file (Note: external references will be preserved)"""
        with open(self.config_path, 'w') as file:
            yaml.dump(self._config, file, default_flow_style=False)
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self._load_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the loaded configuration"""
        info = {
            'config_file': str(self.config_path),
            'sections': list(self._config.keys()),
            'token_count': len(self.get_github_tokens()),
            'project_count': len(self.get_projects())
        }
        return info