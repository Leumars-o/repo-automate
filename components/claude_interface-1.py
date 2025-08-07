# components/claude_interface.py
from typing import Dict, Any, Optional, List
import asyncio
import os
import time
from pathlib import Path
from core.base_component import BaseComponent
from core.exceptions import ClaudeError

# Import Claude Code SDK
try:
    from claude_code_sdk import query, ClaudeCodeOptions
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    print("Warning: claude_code_sdk not available. Please install it with: pip install claude-code-sdk")

class ClaudeSession:
    """Manages a persistent Claude session for iterative development"""
    
    def __init__(self, session_id: str, workspace_path: str, max_turns: int = 10):
        self.session_id = session_id
        self.workspace_path = workspace_path
        self.max_turns = max_turns
        self.turns_used = 0
        self.conversation_history = []
        self.options = ClaudeCodeOptions(
            max_turns=max_turns,
            system_prompt=self._get_system_prompt(),
            cwd=Path(workspace_path),
            allowed_tools=["Read", "Write", "Bash"],
            permission_mode="acceptEdits"
        )
        self.active_query = None
        self.is_active = False
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the session"""
        return """You are an expert smart contract developer specializing in Clarity for the Stacks blockchain. 

            Key responsibilities:
            - Write secure, efficient, and well-documented smart contracts
            - Fix compilation errors with minimal changes that preserve functionality
            - Follow Clarity best practices and security patterns
            - Maintain code consistency and readability

            When fixing errors:
            1. Read and understand the current contract code
            2. Identify the specific issue causing the error
            3. Make targeted fixes that address the root cause
            4. Verify the fix doesn't break existing functionality

            You have persistent context across multiple interactions in this session."""
    
    async def send_message(self, message: str) -> str:
        """Send a message in the current session context"""
        if self.turns_used >= self.max_turns:
            raise ClaudeError(f"Session {self.session_id} has reached maximum turns ({self.max_turns})")
        
        try:
            responses = []
            
            # If this is a continuation of an existing session, we need to maintain context
            if self.is_active and self.active_query:
                # Continue the existing query with new context
                full_message = f"\n\nContinuing from previous context...\n\n{message}"
            else:
                # Start a new query session
                full_message = message
                self.is_active = True
            
            # Execute the query
            async for response in query(prompt=full_message, options=self.options):
                responses.append(str(response))
            
            combined_response = "\n".join(responses)
            
            # Update session state
            self.turns_used += 1
            self.conversation_history.append({
                'turn': self.turns_used,
                'user_message': message,
                'claude_response': combined_response,
                'timestamp': time.time()
            })
            
            return combined_response
            
        except Exception as e:
            raise ClaudeError(f"Session message failed: {str(e)}")
    
    def get_remaining_turns(self) -> int:
        """Get remaining turns in this session"""
        return max(0, self.max_turns - self.turns_used)
    
    def close_session(self):
        """Close the session"""
        self.is_active = False
        self.active_query = None


class ClaudeInterface(BaseComponent):
    """Handles all interactions with Claude Code SDK with session management"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        super().__init__(config, logger)
        self.claude_config = config.get('claude', {})
        self.timeout = self.claude_config.get('timeout', 120)
        self.max_retries = config.get('automation', {}).get('max_retries', 3)
        self.active_sessions = {}  # Track active sessions per project
        
    def _initialize(self) -> None:
        """Initialize Claude interface"""
        self.validate_config(['claude'])
        self._verify_claude_sdk_available()
    
    def _verify_claude_sdk_available(self) -> None:
        """Verify Claude Code SDK is available"""
        if not CLAUDE_SDK_AVAILABLE:
            raise ClaudeError("Claude Code SDK not found. Please install it with: pip install claude-code-sdk")
        self.log_info("Claude Code SDK verified and available")

    def _get_or_create_session(self, project_name: str, workspace_path: str, session_type: str = "default") -> ClaudeSession:
        """Get existing session or create new one for a project"""
        session_key = f"{project_name}_{session_type}"
        
        if session_key not in self.active_sessions:
            self.log_info(f"Creating new Claude session: {session_key}")
            self.active_sessions[session_key] = ClaudeSession(
                session_id=session_key,
                workspace_path=workspace_path,
                max_turns=15  # Allow more turns for error correction
            )
        else:
            session = self.active_sessions[session_key]
            if session.get_remaining_turns() <= 1:
                self.log_info(f"Session {session_key} near limit, creating fresh session")
                session.close_session()
                self.active_sessions[session_key] = ClaudeSession(
                    session_id=session_key,
                    workspace_path=workspace_path,
                    max_turns=15
                )
        
        return self.active_sessions[session_key]

    async def _execute_claude_query(self, prompt: str, workspace_path: str, max_turns: int = 8) -> str:
        """Execute one-off Claude query with increased turns for README"""
        try:
            options = ClaudeCodeOptions(
                max_turns=max_turns,
                system_prompt="You are an expert technical writer and smart contract developer. Create comprehensive, professional documentation. Work efficiently and complete tasks within the turn limit.",
                cwd=Path(workspace_path),
                allowed_tools=["Read", "Write", "Bash"],
                permission_mode="acceptEdits"
            )
            
            responses = []
            self.log_info(f"Starting one-off Claude query with {max_turns} max turns")
            
            async for message in query(prompt=prompt, options=options):
                responses.append(str(message))
                # Only log first 50 chars to reduce noise
                self.log_info(f"Claude response: {str(message)[:50]}...")
            
            combined_response = "\n".join(responses)
            self.log_info("Claude query completed successfully")
            return combined_response
            
        except Exception as e:
            self.log_error(f"Claude query failed: {str(e)}")
            raise ClaudeError(f"Failed to execute Claude query: {str(e)}")

    def generate_contract(self, project: Dict[str, Any], workspace_path: str) -> str:
        """Generate smart contract using Claude Code SDK with session"""
        try:
            project_name = project['name']
            project_workspace = Path(workspace_path).resolve()
            
            if not project_workspace.exists():
                raise ClaudeError(f"Workspace path does not exist: {workspace_path}")
            
            # Find the contract directory
            contract_dir_name = f"{project_name}_contract"
            contract_path = project_workspace / contract_dir_name
            
            if not contract_path.exists():
                clarinet_dirs = [d for d in project_workspace.iterdir() 
                            if d.is_dir() and (d / 'Clarinet.toml').exists()]
                if clarinet_dirs:
                    contract_path = clarinet_dirs[0]
                    contract_dir_name = contract_path.name
                else:
                    raise ClaudeError(f"Contract directory not found. Expected: {contract_dir_name}")
            
            self.log_info(f"Working in contract directory: {contract_path}")
            
            # Create a session for this project
            session = self._get_or_create_session(project_name, str(contract_path), "contract_generation")
            
            # Prepare the prompt for Claude
            prompt = self._build_contract_prompt(project)
            
            # Generate contract using session
            result = asyncio.run(session.send_message(prompt))
            
            # Find the generated contract file
            contracts_dir = contract_path / 'contracts'
            if contracts_dir.exists():
                contract_files = list(contracts_dir.glob('*.clar'))
                if contract_files:
                    self.log_info(f"Contract generated successfully: {contract_files[0].name}")
                    return str(contract_files[0])
                else:
                    raise ClaudeError("No Clarity contract files found after generation")
            else:
                raise ClaudeError("Contracts directory not found after generation")
                
        except Exception as e:
            raise ClaudeError(f"Failed to generate smart contract: {str(e)}")

    def fix_error(self, project: Dict[str, Any], workspace_path: str, 
                  error_message: str, error_details: Dict[str, Any], attempt: int = 1) -> None:
        """Fix contract compilation errors using persistent Claude session"""
        try:
            project_name = project['name']
            project_workspace = Path(workspace_path)
            contract_dir_name = f"{project_name}_contract"
            contract_path = project_workspace / contract_dir_name
            
            if not contract_path.exists():
                clarinet_dirs = [d for d in project_workspace.iterdir() 
                            if d.is_dir() and (d / 'Clarinet.toml').exists()]
                if clarinet_dirs:
                    contract_path = clarinet_dirs[0]
            
            self.log_info(f"Fixing errors in contract directory: {contract_path} (attempt {attempt})")
            
            # Get or create session for error fixing (separate from generation)
            session = self._get_or_create_session(project_name, str(contract_path), "error_fixing")
            
            # Build error fixing prompt with context about the attempt
            if attempt == 1:
                fix_prompt = self._build_initial_error_fix_prompt(project, error_message, error_details)
            else:
                fix_prompt = self._build_followup_error_fix_prompt(project, error_message, error_details, attempt)
            
            # Execute error fix in session context
            result = asyncio.run(session.send_message(fix_prompt))
            
            self.log_info(f"Error fixing completed (attempt {attempt}). Remaining turns: {session.get_remaining_turns()}")
            
        except Exception as e:
            raise ClaudeError(f"Failed to fix contract error: {str(e)}")

    def generate_readme(self, project: Dict[str, Any], workspace_path: str, 
                       contract_file: Optional[str] = None) -> str:
        """Generate README with more efficient approach"""
        try:
            workspace = Path(workspace_path)
            self.log_info(f"Generating README in workspace: {workspace}")
            
            if not contract_file:
                contract_file = self._find_contract_file(workspace_path)
            
            contract_config = self.config.get('smart_contracts', {})
            blockchain = contract_config.get('blockchain', 'stacks')
            language = contract_config.get('language', 'clarity')
            
            # Use more efficient README prompt that focuses on completion
            prompt = self._build_efficient_readme_prompt(project, contract_file, blockchain, language)
            
            # Use more turns for README generation since it's complex
            result = asyncio.run(self._execute_claude_query(prompt, str(workspace), max_turns=10))
            
            # Verify README was actually created/updated
            readme_file = self._find_readme_file(workspace_path)
            
            # Check if README was actually updated (not just a placeholder)
            if self._verify_readme_quality(readme_file, project['name']):
                self.log_info(f"Generated comprehensive README: {readme_file}")
                return readme_file
            else:
                self.log_warning("README appears to be placeholder content, attempting regeneration")
                # Try a more direct approach
                self._create_basic_readme(workspace, project, blockchain, language)
                return str(workspace / "README.md")
            
        except Exception as e:
            self.log_error(f"Failed to generate README with Claude: {str(e)}")
            # Fallback: create basic README
            try:
                self._create_basic_readme(workspace, project, blockchain, language)
                return str(workspace / "README.md")
            except Exception as fallback_e:
                raise ClaudeError(f"Failed to generate README: {str(e)}. Fallback also failed: {str(fallback_e)}")

    def _verify_readme_quality(self, readme_path: str, project_name: str) -> bool:
        """Check if README contains actual content for the project"""
        try:
            with open(readme_path, 'r') as f:
                content = f.read()
            
            # Check for project-specific content
            has_project_name = project_name.lower() in content.lower()
            has_meaningful_content = len(content) > 500  # More than just headers
            has_clarity_mention = 'clarity' in content.lower() or 'stacks' in content.lower()
            
            return has_project_name and has_meaningful_content and has_clarity_mention
        except Exception:
            return False

    def _create_basic_readme(self, workspace: Path, project: Dict[str, Any], blockchain: str, language: str) -> None:
        """Create a basic README as fallback"""
        readme_content = f"""# {project['name']}

        ## Overview
        {project['description']}

        ## Technical Specifications
        - **Blockchain**: {blockchain}
        - **Language**: {language}
        - **Framework**: Clarinet

        ## Prerequisites
        - [Clarinet](https://github.com/hirosystems/clarinet) - Clarity development environment
        - [Stacks CLI](https://docs.stacks.co/docs/stacks-cli/) - For deployment

        ## Installation & Setup

        1. Clone the repository:
        ```bash
        git clone <repository-url>
        cd {project['name']}
        ```

        2. Navigate to the contract directory:
        ```bash
        cd {project['name']}_contract
        ```

        3. Check the contract:
        ```bash
        clarinet check
        ```

        ## Project Structure
        ```
        {project['name']}_contract/
        ├── Clarinet.toml          # Project configuration
        ├── contracts/             # Smart contract files
        ├── tests/                 # Test files
        └── settings/              # Network settings
        ```

        ## Usage

        ### Testing
        Run the test suite:
        ```bash
        clarinet test
        ```

        ### Deployment
        Deploy to testnet:
        ```bash
        clarinet deploy --testnet
        ```

        ## Contract Functions
        See the contract file in `contracts/` directory for detailed function documentation.

        ## Security Considerations
        - All functions include proper input validation
        - Access controls are implemented where appropriate
        - Contract follows Clarity security best practices

        ## Contributing
        1. Fork the repository
        2. Create a feature branch
        3. Make your changes
        4. Add tests
        5. Submit a pull request

        ## License
        MIT License
        """
        
        readme_path = workspace / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        self.log_info(f"Created basic README at: {readme_path}")

    def _build_efficient_readme_prompt(self, project: Dict[str, Any], contract_file: str, 
                                     blockchain: str, language: str) -> str:
        """Build a more efficient prompt that focuses on completing the task quickly"""
        return f"""Create a comprehensive README.md file for the {project['name']} smart contract project.

            IMPORTANT: Work efficiently to complete this task within the turn limit.

            Project: {project['name']}
            Description: {project['description']}
            Blockchain: {blockchain}
            Language: {language}

            Steps:
            1. Examine the contract directory structure quickly
            2. Read the main contract file to understand key functions
            3. Replace the existing README.md with comprehensive documentation

            Required sections for README.md:
            - Project title and description
            - Features (based on contract analysis)
            - Technical specifications
            - Installation instructions
            - Usage examples
            - Contract functions documentation
            - Deployment guide
            - Security notes

            Focus on creating complete, accurate content rather than extensive exploration. Save the final README.md in the root directory.
            """

    def _build_initial_error_fix_prompt(self, project: Dict[str, Any], error_message: str, 
                                       error_details: Dict[str, Any]) -> str:
        """Build the initial error fixing prompt"""
        formatted_errors = error_details.get('formatted_for_claude', '') if error_details else error_message
        
        return f"""I need you to fix compilation errors in the smart contract for project: "{project['name']}"

            This is the FIRST attempt at fixing these errors.

            The contract failed to compile with the following errors:
            {formatted_errors}

            Please:
            1. Read the current contract file in the contracts/ directory
            2. Analyze the compilation errors carefully  
            3. Fix the specific issues mentioned in the error messages
            4. Ensure the corrected code follows Clarity best practices
            5. Maintain the original functionality while fixing the errors

            Important: This is a persistent session, so if there are still errors after this fix, I'll send you the new error messages and you can make additional corrections based on the full context of our conversation."""

    def _build_followup_error_fix_prompt(self, project: Dict[str, Any], error_message: str, 
                                        error_details: Dict[str, Any], attempt: int) -> str:
        """Build followup error fixing prompt with session context"""
        formatted_errors = error_details.get('formatted_for_claude', '') if error_details else error_message
        
        return f"""The contract still has compilation errors after our previous fix attempt.

            This is attempt #{attempt} at fixing the errors.

            NEW ERROR OUTPUT:
            {formatted_errors}

            Based on our previous conversation and the changes you already made, please:
            1. Review what was changed in the previous attempt
            2. Analyze these new/remaining errors
            3. Make additional targeted fixes
            4. Explain what additional changes you're making and why
            5. Consider if the previous fix introduced any new issues

            Remember: You have the full context of our previous fixes, so build upon what was already done."""

    # Keep existing helper methods
    def _build_contract_prompt(self, project: Dict[str, Any]) -> str:
        """Build the prompt for contract generation"""
        contract_config = self.config.get('smart_contracts', {})
        
        prompt = f"""I need you to create a simple smart contract for a project called "{project['name']}".

            Project Description: {project['description']}

            Requirements:
            - Blockchain: {contract_config.get('blockchain', 'stacks')}
            - Language: {contract_config.get('language', 'clarity')}
            - Contract Type: {project.get('contract_type', 'basic')}

            Please follow these steps:

            1. First, examine the current directory structure to understand the Clarinet project layout
            2. Look at the existing contract file in the contracts/ directory
            3. Replace the placeholder content with a complete, functional smart contract that implements the project requirements
            4. The contract should be saved in the contracts/ directory with a .clar extension

            Note: This is the start of a persistent session. If there are compilation errors, I'll send them to you and you can make corrections while maintaining the context of what was already built.
            """
        
        return prompt.strip()
    
    def _find_readme_file(self, workspace_path: str) -> str:
        """Find the generated README file in the workspace"""
        workspace = Path(workspace_path)
        
        readme_patterns = ['README.md', 'readme.md', 'Readme.md', 'README.txt', 'readme.txt']
        
        for pattern in readme_patterns:
            readme_file = workspace / pattern
            if readme_file.exists():
                return str(readme_file)
        
        md_files = list(workspace.glob("*.md"))
        if md_files:
            latest_md = max(md_files, key=lambda f: f.stat().st_mtime)
            return str(latest_md)
        
        raise ClaudeError("No README file found after generation")
    
    def _find_contract_file(self, workspace_path: str) -> str:
        """Find the generated contract file in the workspace"""
        workspace = Path(workspace_path)
        
        contract_extensions = ['.clar', '.sol', '.rs', '.move']
        
        for ext in contract_extensions:
            contract_files = list(workspace.glob(f"**/*{ext}"))
            if contract_files:
                latest_file = max(contract_files, key=lambda f: f.stat().st_mtime)
                return str(latest_file)
        
        raise ClaudeError("No contract file found after Claude Code execution")

    def close_project_sessions(self, project_name: str) -> None:
        """Close all sessions for a project"""
        sessions_to_close = [key for key in self.active_sessions if key.startswith(f"{project_name}_")]
        
        for session_key in sessions_to_close:
            session = self.active_sessions[session_key]
            session.close_session()
            del self.active_sessions[session_key]
            self.log_info(f"Closed session: {session_key}")

    def get_session_status(self, project_name: str) -> Dict[str, Any]:
        """Get status of all sessions for a project"""
        project_sessions = {}
        
        for session_key, session in self.active_sessions.items():
            if session_key.startswith(f"{project_name}_"):
                project_sessions[session_key] = {
                    'turns_used': session.turns_used,
                    'remaining_turns': session.get_remaining_turns(),
                    'is_active': session.is_active,
                    'conversation_length': len(session.conversation_history)
                }
                
        return project_sessions
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Claude Code operation"""
        operations = {
            'generate_contract': self.generate_contract,
            'fix_error': self.fix_error,
            'generate_readme': self.generate_readme,
            'close_sessions': self.close_project_sessions,
            'get_session_status': self.get_session_status
        }
        
        if operation not in operations:
            raise ClaudeError(f"Unknown Claude operation: {operation}")
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            self.log_error(f"Claude operation '{operation}' failed: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up Claude resources and close all sessions"""
        for session_key in list(self.active_sessions.keys()):
            session = self.active_sessions[session_key]
            session.close_session()
            del self.active_sessions[session_key]
        
        self.log_info("All Claude sessions closed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get Claude interface status"""
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'sdk_available': CLAUDE_SDK_AVAILABLE,
            'active_sessions': len(self.active_sessions),
            'session_details': {key: {
                'turns_used': session.turns_used,
                'remaining_turns': session.get_remaining_turns()
            } for key, session in self.active_sessions.items()}
        }