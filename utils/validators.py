# utils/validators.py
from typing import Dict, Any, List, Optional, Union
import re
import os
import yaml
from pathlib import Path
from urllib.parse import urlparse
from core.exceptions import AutomationError, ConfigurationError

class ValidationError(AutomationError):
    """Raised when validation fails"""
    pass

class ConfigValidator:
    """Validates configuration files and structures"""
    
    REQUIRED_CONFIG_SECTIONS = ['github', 'projects', 'smart_contracts', 'automation']
    
    REQUIRED_GITHUB_FIELDS = ['tokens']
    REQUIRED_PROJECT_FIELDS = ['name', 'description']
    REQUIRED_SMART_CONTRACT_FIELDS = ['blockchain', 'language']
    REQUIRED_AUTOMATION_FIELDS = ['max_retries', 'timeout']
    
    SUPPORTED_BLOCKCHAINS = ['stacks', 'ethereum', 'polygon', 'arbitrum']
    SUPPORTED_LANGUAGES = ['clarity', 'solidity', 'rust', 'move']
    
    @classmethod
    def validate_config_file(cls, config_path: str) -> Dict[str, Any]:
        """Validate configuration file exists and has valid YAML"""
        if not os.path.exists(config_path):
            raise ValidationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise ValidationError("Configuration must be a dictionary")
            
            return config
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading configuration file: {e}")
    
    @classmethod
    def validate_config_structure(cls, config: Dict[str, Any]) -> None:
        """Validate configuration structure and required fields"""
        # Check top-level sections
        missing_sections = [
            section for section in cls.REQUIRED_CONFIG_SECTIONS 
            if section not in config
        ]
        if missing_sections:
            raise ValidationError(f"Missing required config sections: {missing_sections}")
        
        # Validate GitHub section
        cls._validate_github_config(config['github'])
        
        # Validate projects section
        cls._validate_projects_config(config['projects'])
        
        # Validate smart contracts section
        cls._validate_smart_contracts_config(config['smart_contracts'])
        
        # Validate automation section
        cls._validate_automation_config(config['automation'])
    
    @classmethod
    def _validate_github_config(cls, github_config: Dict[str, Any]) -> None:
        """Validate GitHub configuration"""
        missing_fields = [
            field for field in cls.REQUIRED_GITHUB_FIELDS 
            if field not in github_config
        ]
        if missing_fields:
            raise ValidationError(f"Missing required GitHub config fields: {missing_fields}")
        
        # Validate tokens
        tokens = github_config['tokens']
        if not isinstance(tokens, list) or len(tokens) == 0:
            raise ValidationError("GitHub tokens must be a non-empty list")
        
        for i, token in enumerate(tokens):
            if not isinstance(token, str) or len(token.strip()) == 0:
                raise ValidationError(f"GitHub token at index {i} must be a non-empty string")
            
            if not cls._is_valid_github_token(token):
                raise ValidationError(f"Invalid GitHub token format at index {i}")
    
    @classmethod
    def _validate_projects_config(cls, projects_config: List[Dict[str, Any]]) -> None:
        """Validate projects configuration"""
        if not isinstance(projects_config, list):
            raise ValidationError("Projects configuration must be a list")
        
        if len(projects_config) == 0:
            raise ValidationError("At least one project must be defined")
        
        project_names = []
        for i, project in enumerate(projects_config):
            if not isinstance(project, dict):
                raise ValidationError(f"Project at index {i} must be a dictionary")
            
            # Check required fields
            missing_fields = [
                field for field in cls.REQUIRED_PROJECT_FIELDS 
                if field not in project
            ]
            if missing_fields:
                raise ValidationError(f"Project at index {i} missing required fields: {missing_fields}")
            
            # Validate project name
            project_name = project['name']
            if not cls._is_valid_project_name(project_name):
                raise ValidationError(f"Invalid project name at index {i}: {project_name}")
            
            # Check for duplicate project names
            if project_name in project_names:
                raise ValidationError(f"Duplicate project name: {project_name}")
            project_names.append(project_name)
            
            # Validate blockchain if specified
            if 'blockchain' in project and project['blockchain'] not in cls.SUPPORTED_BLOCKCHAINS:
                raise ValidationError(f"Unsupported blockchain in project {project_name}: {project['blockchain']}")
            
            # Validate priority if specified
            if 'priority' in project and project['priority'] not in ['low', 'medium', 'high']:
                raise ValidationError(f"Invalid priority in project {project_name}: {project['priority']}")
    
    @classmethod
    def _validate_smart_contracts_config(cls, contracts_config: Dict[str, Any]) -> None:
        """Validate smart contracts configuration"""
        missing_fields = [
            field for field in cls.REQUIRED_SMART_CONTRACT_FIELDS 
            if field not in contracts_config
        ]
        if missing_fields:
            raise ValidationError(f"Missing required smart contract config fields: {missing_fields}")
        
        # Validate blockchain
        blockchain = contracts_config['blockchain']
        if blockchain not in cls.SUPPORTED_BLOCKCHAINS:
            raise ValidationError(f"Unsupported blockchain: {blockchain}")
        
        # Validate language
        language = contracts_config['language']
        if language not in cls.SUPPORTED_LANGUAGES:
            raise ValidationError(f"Unsupported language: {language}")
        
        # Validate blockchain-language compatibility
        if not cls._is_compatible_blockchain_language(blockchain, language):
            raise ValidationError(f"Incompatible blockchain-language combination: {blockchain}-{language}")
        
        # Validate deployment network if specified
        if 'deployment_network' in contracts_config:
            network = contracts_config['deployment_network']
            if network not in ['testnet', 'mainnet', 'devnet']:
                raise ValidationError(f"Invalid deployment network: {network}")
    
    @classmethod
    def _validate_automation_config(cls, automation_config: Dict[str, Any]) -> None:
        """Validate automation configuration"""
        missing_fields = [
            field for field in cls.REQUIRED_AUTOMATION_FIELDS 
            if field not in automation_config
        ]
        if missing_fields:
            raise ValidationError(f"Missing required automation config fields: {missing_fields}")
        
        # Validate numeric fields
        numeric_fields = {
            'max_retries': (1, 10),
            'retry_delay': (1, 60),
            'timeout': (30, 600),
            'parallel_workers': (1, 10)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in automation_config:
                value = automation_config[field]
                if not isinstance(value, int) or not min_val <= value <= max_val:
                    raise ValidationError(f"Invalid {field}: must be integer between {min_val} and {max_val}")
        
        # Validate log level if specified
        if 'log_level' in automation_config:
            log_level = automation_config['log_level']
            if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                raise ValidationError(f"Invalid log level: {log_level}")
    
    @staticmethod
    def _is_valid_github_token(token: str) -> bool:
        """Check if GitHub token has valid format"""
        # GitHub personal access tokens start with 'ghp_' and are 40 characters total
        # GitHub App tokens start with different prefixes
        token_patterns = [
            r'^ghp_[A-Za-z0-9]{36}$',  # Personal access token
            r'^gho_[A-Za-z0-9]{36}$',  # OAuth token
            r'^ghu_[A-Za-z0-9]{36}$',  # User-to-server token
            r'^ghs_[A-Za-z0-9]{36}$',  # Server-to-server token
        ]
        
        return any(re.match(pattern, token) for pattern in token_patterns)
    
    @staticmethod
    def _is_valid_project_name(name: str) -> bool:
        """Check if project name is valid for GitHub repositories"""
        if not isinstance(name, str) or len(name) == 0:
            return False
        
        # GitHub repository name rules
        if len(name) > 100:
            return False
        
        # Must start and end with alphanumeric
        if not (name[0].isalnum() and name[-1].isalnum()):
            return False
        
        # Can contain alphanumeric, hyphens, underscores, periods
        if not re.match(r'^[A-Za-z0-9._-]+$', name):
            return False
        
        # Cannot be just dots
        if name in ['.', '..']:
            return False
        
        return True
    
    @staticmethod
    def _is_compatible_blockchain_language(blockchain: str, language: str) -> bool:
        """Check if blockchain and language combination is compatible"""
        compatibility_map = {
            'stacks': ['clarity'],
            'ethereum': ['solidity'],
            'polygon': ['solidity'],
            'arbitrum': ['solidity'],
            'solana': ['rust'],
            'aptos': ['move'],
            'sui': ['move']
        }
        
        compatible_languages = compatibility_map.get(blockchain, [])
        return language in compatible_languages

class ProjectValidator:
    """Validates individual project configurations and data"""
    
    @classmethod
    def validate_project(cls, project: Dict[str, Any]) -> None:
        """Validate a single project configuration"""
        if not isinstance(project, dict):
            raise ValidationError("Project must be a dictionary")
        
        # Required fields
        required_fields = ['name', 'description']
        missing_fields = [field for field in required_fields if field not in project]
        if missing_fields:
            raise ValidationError(f"Project missing required fields: {missing_fields}")
        
        # Validate name
        if not ConfigValidator._is_valid_project_name(project['name']):
            raise ValidationError(f"Invalid project name: {project['name']}")
        
        # Validate description
        description = project['description']
        if not isinstance(description, str) or len(description.strip()) == 0:
            raise ValidationError("Project description must be a non-empty string")
        
        if len(description) > 500:
            raise ValidationError("Project description must be 500 characters or less")
        
        # Validate optional fields
        if 'priority' in project:
            if project['priority'] not in ['low', 'medium', 'high']:
                raise ValidationError(f"Invalid priority: {project['priority']}")
        
        if 'blockchain' in project:
            if project['blockchain'] not in ConfigValidator.SUPPORTED_BLOCKCHAINS:
                raise ValidationError(f"Unsupported blockchain: {project['blockchain']}")
        
        if 'contract_type' in project:
            contract_type = project['contract_type']
            valid_types = ['basic', 'token', 'nft', 'defi', 'dao', 'marketplace']
            if contract_type not in valid_types:
                raise ValidationError(f"Invalid contract type: {contract_type}")

class GitHubValidator:
    """Validates GitHub-related inputs and configurations"""
    
    @classmethod
    def validate_repository_url(cls, url: str) -> bool:
        """Validate GitHub repository URL format"""
        if not isinstance(url, str):
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        # Check if it's a GitHub URL
        if parsed.netloc not in ['github.com', 'www.github.com']:
            return False
        
        # Check path format (should be /username/repository or /username/repository.git)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 2:
            return False
        
        username, repo = path_parts
        repo = repo.replace('.git', '')  # Remove .git suffix if present
        
        return cls._is_valid_github_username(username) and cls._is_valid_repo_name(repo)
    
    @classmethod
    def validate_github_token(cls, token: str) -> bool:
        """Validate GitHub token format"""
        return ConfigValidator._is_valid_github_token(token)
    
    @staticmethod
    def _is_valid_github_username(username: str) -> bool:
        """Check if GitHub username is valid"""
        if not isinstance(username, str) or len(username) == 0:
            return False
        
        # GitHub username rules
        if len(username) > 39:
            return False
        
        # Can contain alphanumeric and hyphens, but not start/end with hyphen
        if not re.match(r'^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$', username):
            return False
        
        return True
    
    @staticmethod
    def _is_valid_repo_name(repo_name: str) -> bool:
        """Check if repository name is valid"""
        return ConfigValidator._is_valid_project_name(repo_name)

class FileSystemValidator:
    """Validates file system paths and operations"""
    
    @classmethod
    def validate_workspace_path(cls, path: str) -> None:
        """Validate workspace path"""
        if not isinstance(path, str) or len(path.strip()) == 0:
            raise ValidationError("Workspace path must be a non-empty string")
        
        path_obj = Path(path)
        
        # Check if path is absolute or relative
        if path_obj.is_absolute():
            # For absolute paths, check if parent directory exists
            if not path_obj.parent.exists():
                raise ValidationError(f"Parent directory does not exist: {path_obj.parent}")
        
        # Check for invalid characters (Windows-specific)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in path for char in invalid_chars):
            raise ValidationError(f"Path contains invalid characters: {path}")
        
        # Check path length (Windows has 260 character limit)
        if len(str(path_obj.absolute())) > 250:  # Leave some buffer
            raise ValidationError("Path is too long")
    
    @classmethod
    def validate_file_path(cls, file_path: str, must_exist: bool = False) -> None:
        """Validate file path"""
        if not isinstance(file_path, str) or len(file_path.strip()) == 0:
            raise ValidationError("File path must be a non-empty string")
        
        path_obj = Path(file_path)
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in invalid_chars):
            raise ValidationError(f"File path contains invalid characters: {file_path}")
        
        # Check if parent directory exists (for new files)
        if not must_exist and not path_obj.parent.exists():
            raise ValidationError(f"Parent directory does not exist: {path_obj.parent}")
    
    @classmethod
    def validate_directory_writable(cls, directory: str) -> None:
        """Check if directory is writable"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            raise ValidationError(f"Directory does not exist: {directory}")
        
        if not dir_path.is_dir():
            raise ValidationError(f"Path is not a directory: {directory}")
        
        # Test write access by creating a temporary file
        test_file = dir_path / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise ValidationError(f"Directory is not writable: {directory}")
        except Exception as e:
            raise ValidationError(f"Cannot write to directory {directory}: {e}")

class ContractValidator:
    """Validates smart contract related inputs"""
    
    SUPPORTED_CONTRACT_EXTENSIONS = {
        'clarity': ['.clar'],
        'solidity': ['.sol'],
        'rust': ['.rs'],
        'move': ['.move']
    }
    
    @classmethod
    def validate_contract_file(cls, file_path: str, language: str = None) -> None:
        """Validate contract file exists and has correct extension"""
        FileSystemValidator.validate_file_path(file_path, must_exist=True)
        
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if language:
            expected_extensions = cls.SUPPORTED_CONTRACT_EXTENSIONS.get(language, [])
            if extension not in expected_extensions:
                raise ValidationError(
                    f"Invalid file extension '{extension}' for {language}. "
                    f"Expected: {expected_extensions}"
                )
    
    @classmethod
    def validate_contract_name(cls, name: str) -> None:
        """Validate contract name"""
        if not isinstance(name, str) or len(name.strip()) == 0:
            raise ValidationError("Contract name must be a non-empty string")
        
        # Contract names should be valid identifiers
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
            raise ValidationError(
                "Contract name must start with a letter and contain only "
                "letters, numbers, and underscores"
            )
        
        if len(name) > 100:
            raise ValidationError("Contract name must be 100 characters or less")
    
    @classmethod
    def validate_blockchain_network(cls, network: str) -> None:
        """Validate blockchain network"""
        valid_networks = ['mainnet', 'testnet', 'devnet', 'localhost']
        if network not in valid_networks:
            raise ValidationError(f"Invalid network: {network}. Valid options: {valid_networks}")

class InputSanitizer:
    """Sanitizes and normalizes input data"""
    
    @staticmethod
    def sanitize_project_name(name: str) -> str:
        """Sanitize project name for GitHub repository"""
        if not isinstance(name, str):
            raise ValidationError("Project name must be a string")
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Replace spaces with hyphens
        name = re.sub(r'\s+', '-', name)
        
        # Remove invalid characters
        name = re.sub(r'[^A-Za-z0-9._-]', '', name)
        
        # Ensure it doesn't start or end with special characters
        name = re.sub(r'^[._-]+|[._-]+$', '', name)
        
        # Ensure it's not empty after sanitization
        if not name:
            raise ValidationError("Project name is empty after sanitization")
        
        return name
    
    @staticmethod
    def sanitize_description(description: str) -> str:
        """Sanitize project description"""
        if not isinstance(description, str):
            raise ValidationError("Description must be a string")
        
        # Remove leading/trailing whitespace
        description = description.strip()
        
        # Normalize whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove potentially harmful characters
        description = re.sub(r'[<>"\']', '', description)
        
        return description
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize file system path"""
        if not isinstance(path, str):
            raise ValidationError("Path must be a string")
        
        # Convert to Path object and resolve
        path_obj = Path(path)
        
        # Resolve relative paths and remove redundant separators
        try:
            normalized = path_obj.resolve()
            return str(normalized)
        except Exception as e:
            raise ValidationError(f"Cannot normalize path {path}: {e}")

# Convenience functions for common validations
def validate_config(config_path: str) -> Dict[str, Any]:
    """Validate complete configuration file"""
    config = ConfigValidator.validate_config_file(config_path)
    ConfigValidator.validate_config_structure(config)
    return config

def validate_project_list(projects: List[Dict[str, Any]]) -> None:
    """Validate list of projects"""
    for i, project in enumerate(projects):
        try:
            ProjectValidator.validate_project(project)
        except ValidationError as e:
            raise ValidationError(f"Invalid project at index {i}: {e}")

def validate_workspace_setup(workspace_path: str) -> None:
    """Validate workspace can be created and used"""
    FileSystemValidator.validate_workspace_path(workspace_path)
    
    # Create workspace directory if it doesn't exist
    workspace = Path(workspace_path)
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Check if it's writable
    FileSystemValidator.validate_directory_writable(workspace_path)

def validate_github_setup(tokens: List[str]) -> None:
    """Validate GitHub tokens"""
    if not tokens:
        raise ValidationError("No GitHub tokens provided")
    
    for i, token in enumerate(tokens):
        if not GitHubValidator.validate_github_token(token):
            raise ValidationError(f"Invalid GitHub token at index {i}")

# Export all validators and functions
__all__ = [
    'ValidationError',
    'ConfigValidator', 
    'ProjectValidator',
    'GitHubValidator',
    'FileSystemValidator', 
    'ContractValidator',
    'InputSanitizer',
    'validate_config',
    'validate_project_list',
    'validate_workspace_setup',
    'validate_github_setup'
]
