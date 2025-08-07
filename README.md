# Smart Contract Automation System

A comprehensive, modular automation system for generating, testing, and deploying smart contracts across multiple GitHub accounts using Claude Code integration.

## 🏗️ Architecture Overview

The system is built with a modular, scalable architecture where each component operates independently and can be modified without affecting the entire codebase.

### Directory Structure
```
smart_contract_automation/
├── main.py                    # Entry point and CLI interface
├── config/
│   ├── __init__.py
│   ├── config_manager.py      # Configuration management
│   └── settings.yaml          # Main configuration file
├── core/
│   ├── __init__.py
│   ├── base_component.py      # Base class for all components
│   ├── orchestrator.py        # Main orchestration logic
│   └── exceptions.py          # Custom exceptions
├── components/
│   ├── __init__.py
│   ├── github_manager.py      # GitHub operations
│   ├── git_operations.py      # Git operations
│   ├── claude_interface.py    # Claude Code integration
│   ├── contract_manager.py    # Smart contract operations
│   └── result_tracker.py      # Results tracking
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging utilities
│   ├── validators.py          # Input validation
│   └── helpers.py             # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_components.py
│   └── test_integration.py
├── workspace/                 # Local project workspace
├── results/                   # Automation results
├── logs/                      # System logs
├── requirements.txt
└── README.md
```

## 🧩 Core Components

### **BaseComponent**
Abstract base class that provides:
- Common initialization patterns
- Configuration validation
- Logging infrastructure
- Error handling standardization
- Status reporting interface

### **Orchestrator**
Central coordinator that:
- Manages component lifecycle
- Coordinates the complete workflow
- Handles parallel processing
- Provides progress monitoring
- Manages error recovery

### **ConfigManager**
Configuration hub that:
- Loads and validates YAML configuration
- Provides type-safe config access
- Supports environment-specific settings
- Handles configuration updates

## 🔧 Functional Components

### **GitHubManager**
GitHub integration component:
- **Repository Management**: Creates repos with custom settings
- **Token Rotation**: Automatic switching between 50+ GitHub accounts
- **Rate Limit Handling**: Monitors and respects API limits
- **Pull Request Creation**: Automated PR generation
- **Account Management**: Seamless multi-account operations

### **GitOperations**
Git workflow management:
- **Repository Cloning**: Local workspace setup
- **Branch Management**: Automated branching strategies
- **Commit Operations**: Staged commits with meaningful messages
- **Push Operations**: Remote synchronization
- **Configuration Setup**: Per-project Git config

### **ClaudeInterface**
Claude Code integration:
- **Contract Generation**: AI-powered smart contract creation
- **Error Fixing**: Automatic error resolution with context
- **Code Optimization**: Performance and security improvements
- **Test Generation**: Comprehensive test suite creation
- **Interactive Development**: Iterative improvement cycles

### **ContractManager**
Smart contract operations:
- **Multi-Blockchain Support**: Stacks, Ethereum, and extensible
- **Environment Setup**: Automated toolchain initialization
- **Compilation**: Cross-platform contract compilation
- **Testing**: Automated test execution
- **Deployment**: Testnet/mainnet deployment management

### **ResultTracker**
Comprehensive result management:
- **Result Persistence**: JSON/CSV export capabilities
- **Metrics Tracking**: Performance and success analytics
- **Report Generation**: Detailed summary reports
- **Error Analysis**: Pattern recognition and insights
- **Backup Management**: Automated result backups

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git installed and configured
- Claude Code CLI installed and authenticated
- Blockchain toolchains (Clarinet for Stacks, Hardhat for Ethereum)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd smart_contract_automation

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config/settings.yaml.example config/settings.yaml
# Edit config/settings.yaml with your tokens and projects
```

### Configuration Setup
Create `config/settings.yaml`:
```yaml
github:
  tokens:
    - "ghp_your_token_1"
    - "ghp_your_token_2"
    # Add all 50 tokens

projects:
  - name: "DeFiLendingProtocol"
    description: "A decentralized lending protocol with collateral management"
    blockchain: "stacks"
    contract_type: "clarity"
    priority: "high"
    
  - name: "NFTMarketplace"
    description: "NFT trading platform with royalty distribution"
    blockchain: "stacks"
    contract_type: "clarity"
    priority: "medium"

smart_contracts:
  blockchain: "stacks"
  language: "clarity"
  testing_framework: "clarinet"
  deployment_network: "testnet"
  
automation:
  max_retries: 3
  retry_delay: 5
  timeout: 300
  parallel_workers: 3
  log_level: "INFO"
  cleanup_on_failure: true
```

## 📋 Usage

### Basic Commands
```bash
# Run complete automation for all projects
python main.py --action run

# Run single project
python main.py --action single --project "DeFiLendingProtocol"

# Check system status
python main.py --action status

# Generate summary report
python main.py --action summary

# Verbose logging
python main.py --action run --verbose
```

### Advanced Usage
```bash
# Custom configuration file
python main.py --config custom_config.yaml --action run

# Process specific project with custom settings
python main.py --action single --project "MyContract" --verbose
```

## 🔄 Workflow Process

For each project, the system executes:

1. **GitHub Repository Creation**
   - Creates repository using current token
   - Applies configured repository settings
   - Handles name conflicts and permissions

2. **Local Environment Setup**
   - Clones repository to local workspace
   - Configures Git user settings
   - Sets up project-specific branching

3. **Smart Contract Environment**
   - Initializes blockchain-specific toolchain
   - Installs required dependencies
   - Configures testing framework

4. **AI-Powered Contract Generation**
   - Calls Claude Code with project context
   - Generates production-ready smart contract
   - Includes comprehensive documentation

5. **Compilation and Testing Loop**
   - Compiles contract with blockchain tools
   - Runs automated tests
   - Fixes errors using Claude Code feedback
   - Repeats until successful

6. **Git Operations**
   - Commits generated code with meaningful messages
   - Pushes to remote repository
   - Handles merge conflicts

7. **Pull Request Creation**
   - Creates PR with detailed description
   - Links to deployment information
   - Records PR URL for tracking

8. **Token Rotation**
   - Automatically switches to next GitHub account
   - Monitors rate limits
   - Handles authentication errors

9. **Result Tracking**
   - Records all metrics and outcomes
   - Generates detailed reports
   - Updates success/failure statistics

## 📊 Monitoring & Results

### Real-Time Status
- **Project Progress**: Live updates on current operations
- **Component Health**: Individual component status monitoring
- **Performance Metrics**: Duration, success rates, error patterns
- **Resource Usage**: Token rotation, API calls, disk space

### Reporting Features
- **JSON Export**: Machine-readable results for integration
- **CSV Export**: Spreadsheet-compatible format
- **Summary Reports**: Executive-level overview
- **Error Analysis**: Detailed failure pattern recognition
- **Performance Analytics**: Optimization insights

### Sample Output
```
=== AUTOMATION SUMMARY REPORT ===

Overall Results:
  Total Projects: 50
  Successful: 47
  Failed: 3
  Success Rate: 94.0%
  Contracts Generated: 47
  Pull Requests Created: 47

Performance:
  Total Duration: 2847.3 seconds
  Average Duration: 56.9 seconds
  Avg Successful Duration: 52.1 seconds

Common Errors:
  CompilationError: 2 occurrences
  NetworkTimeout: 1 occurrence
```

## 🛠️ Extensibility

### Adding New Blockchain Support
1. Extend `ContractManager` with new blockchain methods
2. Add blockchain-specific configuration options
3. Implement compilation and testing logic
4. Update project templates

### Custom Error Handling
1. Create custom exceptions in `core/exceptions.py`
2. Implement error-specific recovery logic
3. Add error patterns to result tracking
4. Update Claude Code prompts for error context

### Component Customization
1. Inherit from `BaseComponent`
2. Implement required abstract methods
3. Add to orchestrator component registry
4. Update configuration schema

## 🔒 Security Considerations

- **Token Management**: Secure storage and rotation of GitHub tokens
- **Code Review**: Automated security scanning of generated contracts
- **Network Security**: HTTPS-only communications
- **Error Handling**: Sensitive information filtering in logs
- **Access Control**: Component-level permission management

## 🚨 Error Recovery

The system handles various failure scenarios:

### Compilation Errors
- Sends error context back to Claude Code
- Implements retry logic with exponential backoff
- Maintains error history for pattern analysis

### GitHub API Limits
- Automatic token rotation
- Rate limit monitoring
- Graceful degradation strategies

### Network Issues
- Configurable timeout handling
- Automatic retry mechanisms
- Offline mode capabilities

### Claude Code Timeouts
- Fallback to simpler prompts
- Progressive timeout increases
- Manual intervention alerts

## 📈 Performance Optimization

### Parallel Processing
- Configurable worker threads
- Resource-aware scheduling
- Load balancing across GitHub accounts

### Caching Strategies
- Template caching for common contracts
- Configuration caching
- Result caching for repeated operations

### Resource Management
- Automatic cleanup of temporary files
- Memory usage monitoring
- Disk space management

## 🧪 Testing

### Unit Tests
```bash
# Run all unit tests
python -m pytest tests/

# Run specific component tests
python -m pytest tests/test_components.py

# Run with coverage
python -m pytest tests/ --cov=components --cov-report=html
```

### Integration Tests
```bash
# Run integration tests
python -m pytest tests/test_integration.py

# Test with sample configuration
python -m pytest tests/ --config tests/sample_config.yaml
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-component`
3. **Implement changes** following the component pattern
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request** with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- **Documentation**: Check the `/docs` directory
- **Issues**: Use GitHub issues for bug reports




# Individual component debugging (uses your existing files)
python debug/debug_runner.py config
python debug/debug_runner.py github
python debug/debug_runner.py git_operations

# Full system debug (runs all 6 components)
python debug/debug_runner.py full

# With verbose output and report generation
python debug/debug_runner.py full --verbose --save-report



# State Tracking and Token Management - Usage Guide

## 🎯 Overview

The automation system now includes comprehensive state tracking that persists across sessions:

- **Token rotation and usage tracking**
- **Project completion tracking** 
- **Blacklist management for failed tokens**
- **Manual token selection**
- **Resume interrupted executions**

## 📁 State Files

All state is stored in JSON files in the `secrets/` directory:

```
secrets/
├── tokens.yaml           # Your GitHub tokens
├── token_state.json      # Token usage tracking
├── project_state.json    # Project completion tracking
└── execution_log.json    # Detailed execution logs
```

## 🔧 New CLI Commands

### **Single Project with Token Selection**
```bash
# Auto-select least used token
python main.py --action single --project "Escrow-chain"

# Use specific token (index 2)
python main.py --action single --project "Escrow-chain" --token-index 2

# With testing enabled
python main.py --action single --project "Escrow-chain" --with-tests

# Combine token selection + testing
python main.py --action single --project "Escrow-chain" --token-index 1 --with-tests
```

### **Batch Processing with Smart Resume**
```bash
# Process all incomplete projects (default)
python main.py --action run

# Force reprocess completed projects
python main.py --action run --force

# Process all projects (including completed)
python main.py --action run --skip-completed=false
```

### **State Management**
```bash
# View state summary
python main.py --action state

# Reset token usage tracking
python main.py --action reset-state --reset-tokens

# Reset project completion tracking  
python main.py --action reset-state --reset-projects

# Reset everything
python main.py --action reset-state --reset-tokens --reset-projects
```

### **Testing Only**
```bash
# Test existing project
python main.py --action test --project "Escrow-chain"
```

## 🔑 Token Management Features

### **Automatic Token Selection**
The system automatically selects the least-used, non-blacklisted token:

```python
# Token usage is tracked:
Token 0: Used 5 times, last used 2 hours ago
Token 1: Used 2 times, last used 1 hour ago  ← Will be selected
Token 2: Used 8 times, blacklisted (rate limited)
```

### **Token Blacklisting**
Tokens are automatically blacklisted when they encounter:
- Rate limiting errors
- Authentication failures (401, 403)
- Other persistent failures

### **Manual Token Override**
```bash
# Force use of specific token
python main.py --action single --project "Project1" --token-index 3
```

## 📋 Project Completion Tracking

### **Automatic Skip of Completed Projects**
```bash
# Only processes incomplete projects
python main.py --action run
```

Output:
```
⏭️  Skip mode: Will skip completed projects
Skipping 3 already completed projects
Starting automation for 2 projects
```

### **Completion Status Check**
```bash
python main.py --action single --project "AlreadyDone"
```

Output:
```
⚠️  Project 'AlreadyDone' has already been completed successfully!
   Use --force flag to reprocess completed projects (coming soon)
```

## 🔄 Smart Resume After Interruption

If you interrupt batch processing (Ctrl+C), the system remembers:
- Which projects were completed
- Which tokens were used
- Any blacklisted tokens

When you restart:
```bash
python main.py --action run
```

It will:
1. ✅ Skip completed projects
2. 🔄 Resume with next available token
3. 📋 Continue from where it left off

## 📊 State Summary Example

```bash
python main.py --action state
```

Output:
```
============================================================
STATE TRACKING SUMMARY
============================================================

🔑 Token State:
  Total Tokens: 5
  Current Index: 2
  Blacklisted: 1
  Rotations: 12
  Available: 4
  Available Indices: [0, 1, 2, 4]

📋 Project State:
  Completed: 8
  Failed: 2
  In Progress: 0
  Total Executions: 10

⏳ Incomplete Projects (3):
  - DeFi-lending
  - NFT-marketplace  
  - DAO-governance
============================================================
```

## 🛠️ Advanced Usage Scenarios

### **Large Token Pool Management**
If you have 20+ tokens and run batch processing:

```bash
python main.py --action run
```

The system will:
1. Distribute projects evenly across all tokens
2. Automatically blacklist failing tokens
3. Continue with remaining tokens
4. Persist state if interrupted

### **Selective Reprocessing**
```bash
# Reset specific failed projects
python main.py --action reset-state --reset-projects

# Then reprocess only those projects
python main.py --action run
```

### **Token Recovery**
If tokens get blacklisted incorrectly:

```bash
# Reset token blacklist
python main.py --action reset-state --reset-tokens

# Or manually edit secrets/token_state.json
```

## 🚨 Error Handling

### **Token Exhaustion**
If all tokens are blacklisted:
```
Warning: All tokens are blacklisted, resetting blacklist...
```
The system automatically resets and continues.

### **Stale Progress Cleanup**
The system automatically cleans up stale "in progress" entries from crashed executions (older than 24 hours).

## 📝 JSON State File Examples

### **token_state.json**
```json
{
  "current_token_index": 2,
  "token_usage": {
    "a1b2c3d4": {
      "index": 0,
      "usage_count": 5,
      "last_used": "2025-01-15T10:30:00",
      "projects_completed": ["Project1", "Project2"],
      "rate_limited": false
    }
  },
  "tokens_blacklisted": ["x9y8z7w6"],
  "rotation_count": 15
}
```

### **project_state.json**
```json
{
  "completed_projects": {
    "Escrow-chain": {
      "completion_time": "2025-01-15T10:30:00", 
      "token_index": 1,
      "duration": 45.2,
      "pr_url": "https://github.com/user/escrow-chain/pull/1",
      "status": "success"
    }
  },
  "failed_projects": {
    "BadProject": {
      "failure_count": 3,
      "last_failure": "2025-01-15T09:15:00",
      "last_error": "Compilation failed"
    }
  }
}
```

## 🎉 Benefits

1. **Session Persistence**: Never lose progress when interrupted
2. **Smart Token Usage**: Optimal distribution across token pool
3. **Failure Recovery**: Automatic blacklisting and recovery
4. **Manual Control**: Override automatic behavior when needed
5. **Comprehensive Logging**: Full audit trail of all operations

This implementation ensures robust, scalable automation even with large token pools and extended execution times!

--config/-c          # Configuration file path
--action/-a          # Action to perform (run, single, test, state, etc.)
--project/-p         # Project name for single operations
--token-index/-t     # Manual token selection (0-based)
--with-tests         # Enable testing for single projects
--skip-completed     # Skip completed projects (default: True)
--force              # Force reprocess completed projects
--reset-tokens       # Reset token state tracking
--reset-projects     # Reset project completion tracking
--verbose/-v         # Enable verbose logging


# Single project with auto token selection
python main.py --action single --project "Escrow-chain"

# Single project with manual token
python main.py --action single --project "Escrow-chain" --token-index 2

# Batch processing (skip completed)
python main.py --action run

# Force reprocess all projects
python main.py --action run --force

# View state tracking
python main.py --action state

# Reset tracking data
python main.py --action reset-state --reset-tokens --reset-projects