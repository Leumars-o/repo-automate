# components/contract_manager.py
from typing import Dict, Any, List, Optional
import subprocess
import os
import json
import re
from pathlib import Path
from core.base_component import BaseComponent
from core.exceptions import ContractError

class ContractManager(BaseComponent):
    """Handles smart contract compilation, testing, and deployment operations"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        self.contract_config = config.get('smart_contracts', {})
        self.blockchain = self.contract_config.get('blockchain', 'stacks')
        self.language = self.contract_config.get('language', 'clarity')
        self.testing_framework = self.contract_config.get('testing_framework', 'clarinet')
        super().__init__(config, logger)
        
    def _initialize(self) -> None:
        """Initialize contract manager"""
        self.validate_config(['smart_contracts'])
        self._verify_tools()
    
    def _verify_tools(self) -> None:
        """Verify required blockchain tools are installed"""
        tools_to_check = []
        
        if self.blockchain == 'stacks':
            tools_to_check.extend(['clarinet', 'stx'])
        elif self.blockchain == 'ethereum':
            tools_to_check.extend(['hardhat', 'truffle'])
        
        for tool in tools_to_check:
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_info(f"Verified tool: {tool}")
                else:
                    self.log_warning(f"Tool {tool} may not be properly installed")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_warning(f"Tool {tool} not found or not responding")
    
    def initialize_project(self, workspace_path: str, project: Dict[str, Any]) -> None:
        """Initialize smart contract project environment"""
        try:
            project_path = Path(workspace_path)
            os.chdir(project_path)
            
            if self.blockchain == 'stacks':
                self._initialize_stacks_project(project)
            elif self.blockchain == 'ethereum':
                self._initialize_ethereum_project(project)
            else:
                raise ContractError(f"Unsupported blockchain: {self.blockchain}")
            
            self.log_info(f"Initialized {self.blockchain} project in {workspace_path}")
            
        except Exception as e:
            raise ContractError(f"Failed to initialize project: {str(e)}")
    
    def _initialize_stacks_project(self, project: Dict[str, Any]) -> None:
        """Initialize Stacks/Clarity project"""
        try:
            project_name = project['name']
            project_path = Path(project_name)
            
            # Check if project directory already exists
            if not project_path.exists():
                # Initialize new Clarinet project with automatic 'n' response to telemetry prompt
                result = subprocess.run(['clarinet', 'new', project_name], 
                                    input='n\n',  # Automatically respond 'n' to telemetry prompt
                                    capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise ContractError(f"Failed to create new Clarinet project: {result.stderr}")
                
                self.log_info(f"Created new Clarinet project: {project_name}")
            else:
                self.log_info(f"Project directory {project_name} already exists, using existing structure")
            
            # Change to project directory for further setup
            os.chdir(project_path)
            
            # Check and create necessary directories only if they don't exist
            required_dirs = ['contracts', 'tests', 'settings']
            for dir_name in required_dirs:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    dir_path.mkdir(exist_ok=True)
                    self.log_info(f"Created missing directory: {dir_name}")
                else:
                    self.log_info(f"Directory {dir_name} already exists")
            
            # Check for Clarinet.toml and create/update if necessary
            clarinet_config_path = Path('Clarinet.toml')
            if not clarinet_config_path.exists():
                self._create_clarinet_config(project)
                self.log_info("Created Clarinet.toml configuration file")
                
        except Exception as e:
            raise ContractError(f"Failed to initialize Stacks project: {str(e)}")

        
    def _initialize_ethereum_project(self, project: Dict[str, Any]) -> None:
        """Initialize Ethereum project"""
        try:
            # Initialize npm project
            subprocess.run(['npm', 'init', '-y'], capture_output=True, text=True)
            
            # Install required dependencies
            dependencies = [
                'hardhat', '@nomiclabs/hardhat-waffle', 'ethereum-waffle',
                'chai', '@nomiclabs/hardhat-ethers', 'ethers'
            ]
            
            for dep in dependencies:
                subprocess.run(['npm', 'install', '--save-dev', dep], 
                             capture_output=True, text=True)
            
            # Initialize Hardhat
            subprocess.run(['npx', 'hardhat', 'init'], 
                         capture_output=True, text=True)
            
        except Exception as e:
            raise ContractError(f"Failed to initialize Ethereum project: {str(e)}")
    
    def _create_clarinet_config(self, project: Dict[str, Any]) -> None:
        """Create Clarinet configuration file"""
        config = {
            "name": project['name'],
            "description": project['description'],
            "version": "1.0.0",
            "epoch": "2.1",
            "clarity_version": "2",
            "boot_contracts": [],
            "contracts": {},
            "requirements": []
        }
        
        with open('Clarinet.toml', 'w') as f:
            # Simple TOML-like format
            f.write(f'[project]\n')
            f.write(f'name = "{config["name"]}"\n')
            f.write(f'description = "{config["description"]}"\n')
            f.write(f'version = "{config["version"]}"\n')
            f.write(f'epoch = "{config["epoch"]}"\n')
            f.write(f'clarity_version = "{config["clarity_version"]}"\n')
    
    def compile_contract(self, workspace_path: str, contract_file: str = "") -> Dict[str, Any]:
        """Compile smart contract - UPDATED: Only compilation, no testing"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            if self.blockchain == 'stacks':
                result = self._compile_stacks_contract(contract_file)
            elif self.blockchain == 'ethereum':
                result = self._compile_ethereum_contract(contract_file)
            else:
                raise ContractError(f"Unsupported blockchain: {self.blockchain}")
            
            return result
            
        except Exception as e:
            raise ContractError(f"Failed to compile contract: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def _compile_stacks_contract(self, contract_file: str) -> Dict[str, Any]:
        """Compile Stacks/Clarity contract with improved error parsing"""
        try:
            # Check if contracts directory has any .clar files
            contracts_dir = Path('contracts')
            if contracts_dir.exists():
                clarity_files = list(contracts_dir.glob('*.clar'))
                if not clarity_files:
                    return {
                        'success': False,
                        'output': '',
                        'errors': 'No Clarity contract files found in contracts/ directory',
                        'contract_file': contract_file,
                        'error_details': {
                            'type': 'missing_files',
                            'message': 'No .clar files found'
                        }
                    }
            
            # Run clarinet check
            result = subprocess.run(['clarinet', 'check'], 
                                  capture_output=True, text=True, timeout=60)
            
            # Parse the output to determine success/failure and extract details
            compilation_result = self._parse_clarinet_output(result.stdout, result.stderr, result.returncode)
            compilation_result['contract_file'] = contract_file
            
            return compilation_result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'errors': 'Contract compilation timed out after 60 seconds',
                'contract_file': contract_file,
                'error_details': {
                    'type': 'timeout',
                    'message': 'Compilation timed out'
                }
            }
        except FileNotFoundError:
            return {
                'success': False,
                'output': '',
                'errors': 'Clarinet tool not found. Please install Clarinet CLI.',
                'contract_file': contract_file,
                'error_details': {
                    'type': 'missing_tool',
                    'message': 'Clarinet not installed'
                }
            }
    
    def _parse_clarinet_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse clarinet check output to determine success/failure and extract error details"""
        combined_output = stdout + stderr
        
        # Check for success patterns
        success_patterns = [
            r'✔ \d+ contracts? checked',
            r'contracts? checked'
        ]
        
        # Check for error patterns  
        error_patterns = [
            r'error: (.+)',
            r'x \d+ errors? detected'
        ]
        
        # Check for warning patterns
        warning_patterns = [
            r'warning: (.+)',
            r'! \d+ warnings? detected'
        ]
        
        has_errors = any(re.search(pattern, combined_output, re.IGNORECASE) for pattern in error_patterns)
        has_warnings = any(re.search(pattern, combined_output, re.IGNORECASE) for pattern in warning_patterns)
        has_success = any(re.search(pattern, combined_output, re.IGNORECASE) for pattern in success_patterns)
        
        # Extract specific error details for Claude
        error_details = None
        if has_errors:
            error_details = self._extract_clarinet_errors(combined_output)
        
        # Determine success - successful if no errors (warnings are okay)
        success = returncode == 0 and not has_errors and has_success
        
        return {
            'success': success,
            'output': stdout,
            'errors': stderr,
            'combined_output': combined_output,
            'has_warnings': has_warnings,
            'has_errors': has_errors,
            'error_details': error_details,
            'warnings': self._extract_clarinet_warnings(combined_output) if has_warnings else [],
            'compilation_status': 'success' if success else 'failed'
        }
    
    def _extract_clarinet_errors(self, output: str) -> Dict[str, Any]:
        """Extract detailed error information for Claude to fix"""
        lines = output.split('\n')
        errors = []
        
        current_error = None
        for line in lines:
            # Match error pattern: "error: expected whitespace before expression"
            error_match = re.match(r'error: (.+)', line)
            if error_match:
                if current_error:
                    errors.append(current_error)
                current_error = {
                    'message': error_match.group(1),
                    'location': None,
                    'code_snippet': None,
                    'full_context': [line]
                }
            # Match location pattern: "--> contracts/escrow-vault.clar:48:19"
            elif current_error and line.startswith('-->'):
                location_match = re.match(r'--> (.+):(\d+):(\d+)', line.strip())
                if location_match:
                    current_error['location'] = {
                        'file': location_match.group(1),
                        'line': int(location_match.group(2)),
                        'column': int(location_match.group(3))
                    }
                current_error['full_context'].append(line)
            # Capture code snippet lines
            elif current_error and (line.strip().startswith('(') or '^' in line):
                current_error['full_context'].append(line)
                if '^' in line:
                    # This is the error pointer line
                    current_error['code_snippet'] = current_error['full_context'][-2] if len(current_error['full_context']) >= 2 else None
        
        # Add the last error if exists
        if current_error:
            errors.append(current_error)
        
        return {
            'type': 'compilation_error',
            'count': len(errors),
            'errors': errors,
            'formatted_for_claude': self._format_errors_for_claude(errors)
        }
    
    def _extract_clarinet_warnings(self, output: str) -> List[Dict[str, Any]]:
        """Extract warning information"""
        lines = output.split('\n')
        warnings = []
        
        current_warning = None
        for line in lines:
            warning_match = re.match(r'warning: (.+)', line)
            if warning_match:
                if current_warning:
                    warnings.append(current_warning)
                current_warning = {
                    'message': warning_match.group(1),
                    'location': None,
                    'context': [line]
                }
            elif current_warning and line.startswith('-->'):
                location_match = re.match(r'--> (.+):(\d+):(\d+)', line.strip())
                if location_match:
                    current_warning['location'] = {
                        'file': location_match.group(1),
                        'line': int(location_match.group(2)),
                        'column': int(location_match.group(3))
                    }
                current_warning['context'].append(line)
        
        if current_warning:
            warnings.append(current_warning)
        
        return warnings
    
    def _format_errors_for_claude(self, errors: List[Dict[str, Any]]) -> str:
        """Format errors in a way that's helpful for Claude to understand and fix"""
        if not errors:
            return ""
        
        formatted = "Clarinet compilation errors:\n\n"
        
        for i, error in enumerate(errors, 1):
            formatted += f"Error {i}: {error['message']}\n"
            
            if error['location']:
                loc = error['location']
                formatted += f"Location: {loc['file']} at line {loc['line']}, column {loc['column']}\n"
            
            if error['full_context']:
                formatted += "Context:\n"
                for context_line in error['full_context']:
                    formatted += f"  {context_line}\n"
            
            formatted += "\n"
        
        return formatted.strip()
    
    def _compile_ethereum_contract(self, contract_file: str) -> Dict[str, Any]:
        """Compile Ethereum contract"""
        try:
            result = subprocess.run(['npx', 'hardhat', 'compile'], 
                                  capture_output=True, text=True, timeout=60)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'contract_file': contract_file
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract compilation timed out")
    
    def test_contract(self, workspace_path: str) -> Dict[str, Any]:
        """Run contract tests - OPTIONAL: Now separate from compilation"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            if self.blockchain == 'stacks':
                result = self._test_stacks_contract()
            elif self.blockchain == 'ethereum':
                result = self._test_ethereum_contract()
            else:
                raise ContractError(f"Unsupported blockchain: {self.blockchain}")
            
            return result
            
        except Exception as e:
            raise ContractError(f"Failed to test contract: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def _test_stacks_contract(self) -> Dict[str, Any]:
        """Test Stacks contract"""
        try:
            result = subprocess.run(['clarinet', 'test'], 
                                  capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'test_results': self._parse_clarinet_test_output(result.stdout)
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract testing timed out")
    
    def _test_ethereum_contract(self) -> Dict[str, Any]:
        """Test Ethereum contract"""
        try:
            result = subprocess.run(['npx', 'hardhat', 'test'], 
                                  capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'test_results': self._parse_hardhat_test_output(result.stdout)
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract testing timed out")
    
    def _parse_clarinet_test_output(self, output: str) -> Dict[str, Any]:
        """Parse Clarinet test output"""
        lines = output.split('\n')
        passed = len([line for line in lines if 'PASS' in line or '✓' in line])
        failed = len([line for line in lines if 'FAIL' in line or '✗' in line])
        
        return {
            'passed': passed,
            'failed': failed,
            'total': passed + failed
        }
    
    def _parse_hardhat_test_output(self, output: str) -> Dict[str, Any]:
        """Parse Hardhat test output"""
        lines = output.split('\n')
        passed = len([line for line in lines if '✓' in line])
        failed = len([line for line in lines if '✗' in line or 'failing' in line])
        
        return {
            'passed': passed,
            'failed': failed,
            'total': passed + failed
        }
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute contract operation"""
        operations = {
            'initialize': self.initialize_project,
            'compile': self.compile_contract,
            'test': self.test_contract,  # Now optional/separate
        }
        
        if operation not in operations:
            raise ContractError(f"Unknown contract operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Contract operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up contract resources"""
        # No persistent resources to clean up
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get contract manager status"""
        return {
            'blockchain': self.blockchain,
            'language': self.language,
            'testing_framework': self.testing_framework,
            'tools_verified': True
        }