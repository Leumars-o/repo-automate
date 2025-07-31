# components/claude_interface.py
from typing import Dict, Any, Optional, List
import subprocess
import os
import time
from pathlib import Path
from core.base_component import BaseComponent
from core.exceptions import ClaudeError

class ClaudeInterface(BaseComponent):
    """Handles all interactions with Claude Code CLI"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        super().__init__(config, logger)
        self.claude_config = config.get('claude', {})
        self.timeout = self.claude_config.get('timeout', 120)
        self.max_retries = config.get('automation', {}).get('max_retries', 3)
        
    def _initialize(self) -> None:
        """Initialize Claude interface"""
        self.validate_config(['claude'])
        self._verify_claude_code_available()
    
    def _verify_claude_code_available(self) -> None:
        """Verify Claude Code CLI is available"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise ClaudeError("Claude Code CLI not found or not working")
            self.log_info("Claude Code CLI verified and available")
        except subprocess.TimeoutExpired:
            raise ClaudeError("Claude Code CLI verification timed out")
        except FileNotFoundError:
            raise ClaudeError("Claude Code CLI not found. Please install it first.")
    
    def generate_smart_contract(self, project: Dict[str, Any], workspace_path: str) -> str:
        """Generate a smart contract using Claude Code"""
        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            # Prepare the prompt
            prompt = self._build_contract_prompt(project)
            
            # Execute Claude Code command
            result = self._execute_claude_command(prompt)
            
            # Find the generated contract file
            contract_file = self._find_contract_file(workspace_path)
            
            self.log_info(f"Generated smart contract: {contract_file}")
            return contract_file
            
        except Exception as e:
            raise ClaudeError(f"Failed to generate smart contract: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def fix_contract_error(self, project: Dict[str, Any], workspace_path: str, error_message: str) -> str:
        """Fix contract errors using Claude Code"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            # Prepare error fix prompt
            prompt = self._build_error_fix_prompt(project, error_message)
            
            # Execute Claude Code command
            result = self._execute_claude_command(prompt)
            
            # Find the updated contract file
            contract_file = self._find_contract_file(workspace_path)
            
            self.log_info(f"Fixed contract error: {contract_file}")
            return contract_file
            
        except Exception as e:
            raise ClaudeError(f"Failed to fix contract error: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def generate_readme(self, project: Dict[str, Any], workspace_path: str, 
                       contract_file: Optional[str] = None) -> str:
        """Generate a comprehensive README.md for the contract project"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            # If no contract file provided, try to find it
            if not contract_file:
                contract_file = self._find_contract_file(workspace_path)
            
            # Get contract analysis for README content
            contract_config = self.config.get('smart_contracts', {})
            blockchain = contract_config.get('blockchain', 'stacks')
            language = contract_config.get('language', 'clarity')
            
            # Prepare the README generation prompt
            prompt = self._build_readme_prompt(project, contract_file, blockchain, language)
            
            # Execute Claude Code command
            result = self._execute_claude_command(prompt)
            
            # Find the generated README file
            readme_file = self._find_readme_file(workspace_path)
            
            self.log_info(f"Generated README: {readme_file}")
            return readme_file
            
        except Exception as e:
            raise ClaudeError(f"Failed to generate README: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def _build_contract_prompt(self, project: Dict[str, Any]) -> str:
        """Build the prompt for contract generation"""
        contract_config = self.config.get('smart_contracts', {})
        
        prompt = f"""
        Write a smart contract: "{project['name']}"
        
        Project Description: {project['description']}
        
        Requirements:
        - Blockchain: {contract_config.get('blockchain', 'stacks')}
        - Language: {contract_config.get('language', 'clarity')}
        - Contract Type: {project.get('contract_type', 'basic')}
        - Add detailed comments explaining functionality
        - Follow best practices for security
        - Make it production-ready
        - Include proper access controls
        
        Please create a complete, functional smart contract with these specifications.
        """
        
        return prompt.strip()
    
    def _build_error_fix_prompt(self, project: Dict[str, Any], error_message: str) -> str:
        """Build the prompt for error fixing"""
        prompt = f"""
        Fix the contract error for project: "{project['name']}"
        
        Error Message:
        {error_message}
        
        Update the contract file with the corrected code.
        """
        
        return prompt.strip()
    
    def _build_readme_prompt(self, project: Dict[str, Any], contract_file: str, 
                           blockchain: str, language: str) -> str:
        """Build the prompt for README generation"""
        prompt = f"""
        Create a comprehensive README.md file for this smart contract project.
        
        Project Details:
        - Name: {project['name']}
        - Description: {project['description']}
        - Contract File: {Path(contract_file).name}
        - Blockchain: {blockchain}
        - Language: {language}
        - Contract Type: {project.get('contract_type', 'basic')}
        
        The README should include:
        1. Project title and description
        2. Features and functionality overview
        3. Technical specifications
        4. Prerequisites and dependencies
        5. Installation and setup instructions
        6. Usage examples and API documentation
        7. Contract functions and their parameters
        8. Deployment instructions for {blockchain}
        9. Testing instructions
        10. Security considerations
        11. Contributing guidelines
        12. License information
        13. Contact information
        14. Troubleshooting section
        15. Changelog/version history placeholder
        
        Make it professional, well-structured with proper markdown formatting,
        and include code examples where appropriate. Analyze the actual contract
        code to provide accurate function descriptions and usage examples.
        
        Save the content as README.md in the current directory.
        """
        
        return prompt.strip()
    
    def _find_readme_file(self, workspace_path: str) -> str:
        """Find the generated README file in the workspace"""
        workspace = Path(workspace_path)
        
        # Look for README files
        readme_patterns = ['README.md', 'readme.md', 'Readme.md', 'README.txt', 'readme.txt']
        
        for pattern in readme_patterns:
            readme_file = workspace / pattern
            if readme_file.exists():
                return str(readme_file)
        
        # Look for any recently created markdown files
        md_files = list(workspace.glob("*.md"))
        if md_files:
            latest_md = max(md_files, key=lambda f: f.stat().st_mtime)
            return str(latest_md)
        
        # Look for any recently created text files
        txt_files = list(workspace.glob("*.txt"))
        if txt_files:
            latest_txt = max(txt_files, key=lambda f: f.stat().st_mtime)
            return str(latest_txt)
        
        raise ClaudeError("No README file found after generation")
    
    def _execute_claude_command(self, prompt: str) -> subprocess.CompletedProcess:
        """Execute Claude Code command with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.log_info(f"Executing Claude Code command (attempt {attempt + 1})")
                
                # Execute the command
                result = subprocess.run(
                    ['claude'] + prompt.split()[:10],  # Limit command length
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode == 0:
                    return result
                else:
                    self.log_warning(f"Claude Code returned non-zero exit code: {result.returncode}")
                    if attempt == self.max_retries - 1:
                        raise ClaudeError(f"Claude Code failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_warning(f"Claude Code command timed out (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise ClaudeError("Claude Code command timed out after all retries")
                    
            except Exception as e:
                self.log_error(f"Claude Code command failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise ClaudeError(f"Claude Code command failed: {str(e)}")
                    
            # Wait before retry
            time.sleep(2 ** attempt)  # Exponential backoff
        
        raise ClaudeError("All Claude Code command attempts failed")
    
    def _find_contract_file(self, workspace_path: str) -> str:
        """Find the generated contract file in the workspace"""
        workspace = Path(workspace_path)
        
        # Common contract file extensions
        contract_extensions = ['.clar', '.sol', '.rs', '.move']
        
        for ext in contract_extensions:
            contract_files = list(workspace.glob(f"**/*{ext}"))
            if contract_files:
                # Return the most recently modified file
                latest_file = max(contract_files, key=lambda f: f.stat().st_mtime)
                return str(latest_file)
        
        # If no contract files found, look for any recently created files
        all_files = [f for f in workspace.rglob("*") if f.is_file()]
        if all_files:
            latest_file = max(all_files, key=lambda f: f.stat().st_mtime)
            return str(latest_file)
        
        raise ClaudeError("No contract file found after Claude Code execution")
    
    def analyze_contract_structure(self, workspace_path: str) -> Dict[str, Any]:
        """Analyze the structure of generated contract"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            prompt = """
            Analyze the contract structure in this directory and provide:
            1. Main contract file name
            2. Contract functions and their purposes
            3. Data structures used
            4. Dependencies required
            5. Testing recommendations
            
            Please provide a structured analysis.
            """
            
            result = self._execute_claude_command(prompt)
            
            return {
                'analysis': result.stdout,
                'workspace_path': workspace_path,
                'timestamp': time.time()
            }
            
        except Exception as e:
            raise ClaudeError(f"Failed to analyze contract structure: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def optimize_contract(self, workspace_path: str) -> str:
        """Optimize the contract code"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            prompt = """
            Optimize the smart contract in this directory:
            1. Improve gas efficiency
            2. Enhance security
            3. Optimize data structures
            4. Reduce code complexity
            5. Add better error handling
            
            Please optimize the contract while maintaining functionality.
            """
            
            result = self._execute_claude_command(prompt)
            contract_file = self._find_contract_file(workspace_path)
            
            self.log_info(f"Optimized contract: {contract_file}")
            return contract_file
            
        except Exception as e:
            raise ClaudeError(f"Failed to optimize contract: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def generate_tests(self, workspace_path: str, project: Dict[str, Any]) -> List[str]:
        """Generate test files for the contract"""
        try:
            original_cwd = os.getcwd()
            os.chdir(workspace_path)
            
            prompt = f"""
            Generate comprehensive tests for the smart contract in this directory.
            
            Project: {project['name']}
            Description: {project['description']}
            
            Please create:
            1. Unit tests for all functions
            2. Integration tests
            3. Edge case tests
            4. Security tests
            5. Performance tests
            
            Use the appropriate testing framework and follow best practices.
            """
            
            result = self._execute_claude_command(prompt)
            
            # Find generated test files
            test_files = []
            workspace = Path(workspace_path)
            
            # Look for test files
            for pattern in ['*test*', '*spec*', 'tests/*', 'test/*']:
                test_files.extend(workspace.glob(pattern))
            
            test_file_paths = [str(f) for f in test_files if f.is_file()]
            
            self.log_info(f"Generated {len(test_file_paths)} test files")
            return test_file_paths
            
        except Exception as e:
            raise ClaudeError(f"Failed to generate tests: {str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Claude Code operation"""
        operations = {
            'generate_contract': self.generate_smart_contract,
            'fix_error': self.fix_contract_error,
            'analyze_structure': self.analyze_contract_structure,
            'optimize': self.optimize_contract,
            'generate_tests': self.generate_tests,
            'generate_readme': self.generate_readme
        }
        
        if operation not in operations:
            raise ClaudeError(f"Unknown Claude operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Claude operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up Claude resources"""
        # No persistent resources to clean up
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get Claude interface status"""
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'cli_available': True  # Already verified in _initialize
        }