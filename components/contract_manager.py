# components/contract_manager.py
from typing import Dict, Any, List, Optional
import subprocess
import os
import json
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
            # Initialize Clarinet project
            result = subprocess.run(['clarinet', 'new', project['name']], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # If project already exists, just configure it
                self.log_info("Project already exists, configuring...")
            
            # Create necessary directories
            Path('contracts').mkdir(exist_ok=True)
            Path('tests').mkdir(exist_ok=True)
            Path('settings').mkdir(exist_ok=True)
            
            # Create basic Clarinet.toml if not exists
            self._create_clarinet_config(project)
            
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
    
    def compile_contract(self, workspace_path: str, contract_file: str) -> Dict[str, Any]:
        """Compile smart contract"""
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
        """Compile Stacks/Clarity contract"""
        try:
            # Check syntax first
            result = subprocess.run(['clarinet', 'check'], 
                                  capture_output=True, text=True, timeout=60)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'contract_file': contract_file
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract compilation timed out")
    
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
        """Run contract tests"""
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
        # Simple parsing - can be enhanced based on actual output format
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
        # Simple parsing - can be enhanced based on actual output format
        lines = output.split('\n')
        passed = len([line for line in lines if '✓' in line])
        failed = len([line for line in lines if '✗' in line or 'failing' in line])
        
        return {
            'passed': passed,
            'failed': failed,
            'total': passed + failed
        }
    
    def deploy_contract(self, workspace_path: str, network: str = 'testnet') -> Dict[str, Any]:
        """Deploy contract to blockchain"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            if self.blockchain == 'stacks':
                result = self._deploy_stacks_contract(network)
            elif self.blockchain == 'ethereum':
                result = self._deploy_ethereum_contract(network)
            else:
                raise ContractError(f"Unsupported blockchain: {self.blockchain}")
            
            return result
            
        except Exception as e:
            raise ContractError(f"Failed to deploy contract: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def _deploy_stacks_contract(self, network: str) -> Dict[str, Any]:
        """Deploy Stacks contract"""
        try:
            # For testnet deployment
            result = subprocess.run(['clarinet', 'deploy', '--network', network], 
                                  capture_output=True, text=True, timeout=180)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'network': network
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract deployment timed out")
    
    def _deploy_ethereum_contract(self, network: str) -> Dict[str, Any]:
        """Deploy Ethereum contract"""
        try:
            result = subprocess.run(['npx', 'hardhat', 'run', 'scripts/deploy.js', '--network', network], 
                                  capture_output=True, text=True, timeout=180)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'network': network
            }
            
        except subprocess.TimeoutExpired:
            raise ContractError("Contract deployment timed out")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute contract operation"""
        operations = {
            'initialize': self.initialize_project,
            'compile': self.compile_contract,
            'test': self.test_contract,
            'deploy': self.deploy_contract
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