# Smart Contract Automation System

A comprehensive, modular automation system for generating, testing, and deploying smart contracts across multiple GitHub accounts using Claude Code integration with advanced state tracking and token management.

## 🏗️ Architecture Overview

The system is built with a modular, scalable architecture where each component operates independently and can be modified without affecting the entire codebase. The system now includes persistent state tracking, intelligent token rotation, and project completion management.

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
│   ├── github_manager.py      # GitHub operations with token rotation
│   ├── git_operations.py      # Git operations
│   ├── claude_interface.py    # Claude Code integration
│   ├── contract_manager.py    # Smart contract operations
│   └── result_tracker.py      # Results tracking
├── utils/
│   ├── __init__.py
│   ├── logger.py              # Logging utilities
│   ├── validators.py          # Input validation
│   └── helpers.py             # Helper functions
├── secrets/                   # State persistence (gitignored)
│   ├── tokens.yaml           # GitHub tokens
│   ├── token_state.json      # Token usage tracking
│   ├── project_state.json    # Project completion tracking
│   └── execution_log.json    # Detailed execution logs
├── tests/
│   ├── __init__.py
│   ├── test_components.py
│   └── test_integration.py
├── workspaces/               # Local project workspace
├── results/                  # Automation results
├── logs/                     # System logs
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
- Handles state tracking and persistence
- Provides progress monitoring
- Manages error recovery and token rotation

### **StateTracker**
Persistent state management that:
- Tracks project completion status
- Manages token usage and rotation
- Handles blacklist management
- Provides session resume capability
- Maintains execution audit trail

### **ConfigManager**
Configuration hub that:
- Loads and validates YAML configuration
- Provides type-safe config access
- Supports environment-specific settings
- Handles configuration updates

## 🔧 Functional Components

### **GitHubManager**
GitHub integration component with intelligent token management:
- **Repository Management**: Creates repos with custom settings
- **Intelligent Token Rotation**: Automatic switching with usage tracking
- **Rate Limit Handling**: Monitors and respects API limits with blacklisting
- **Pull Request Creation**: Automated PR generation
- **Multi-Account Operations**: Seamless operation across 50+ accounts
- **Token Health Monitoring**: Automatic blacklisting of failed tokens

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
- **Testing**: Automated test execution with optional testing mode
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

# Create secrets directory for state tracking
mkdir -p secrets
```

### Configuration Setup
Create `config/settings.yaml`:
```yaml
github:
  tokens:
    - "ghp_your_token_1"
    - "ghp_your_token_2"
    # Add all your GitHub tokens

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

## 📋 Usage Commands

### **Complete CLI Reference**

```bash
# Core Actions
--config/-c          # Configuration file path (default: config/settings.yaml)
--action/-a          # Action: run, single, test, status, summary, state, reset-state
--verbose/-v         # Enable verbose logging

# Project Selection
--project/-p         # Project name for single operations
--token-index/-t     # Manual token selection (0-based index)
--with-tests         # Enable testing for single projects

# Batch Processing Options
--skip-completed     # Skip completed projects (default: True)
--force              # Force reprocess completed projects

# State Management
--reset-tokens       # Reset token state tracking
--reset-projects     # Reset project completion tracking
```

### **Basic Usage**

```bash
# Run complete automation for all projects (skip completed)
python main.py --action run

# Run complete automation including completed projects
python main.py --action run --force

# Check system status
python main.py --action status

# View state tracking summary
python main.py --action state

# Generate summary report
python main.py --action summary
```

### **Single Project Operations**

```bash
# Run single project with auto token selection
python main.py --action single --project "Escrow-chain"

# Run single project with specific token
python main.py --action single --project "Escrow-chain" --token-index 2

# Run single project with testing enabled
python main.py --action single --project "Escrow-chain" --with-tests

# Combine manual token selection with testing
python main.py --action single --project "Escrow-chain" --token-index 1 --with-tests
```

### **Testing Operations**

```bash
# Test existing project (requires prior compilation)
python main.py --action test --project "Escrow-chain"
```

### **State Management**

```bash
# View comprehensive state summary
python main.py --action state

# Reset token usage tracking
python main.py --action reset-state --reset-tokens

# Reset project completion tracking
python main.py --action reset-state --reset-projects

# Reset all state tracking
python main.py --action reset-state --reset-tokens --reset-projects
```

### **Advanced Usage**

```bash
# Custom configuration file
python main.py --config custom_config.yaml --action run

# Verbose logging for debugging
python main.py --action single --project "MyContract" --verbose

# Force reprocess with verbose output
python main.py --action run --force --verbose
```

## 🔄 Workflow Process

For each project, the system executes:

1. **State Check & Token Selection**
   - Checks if project is already completed (unless --force)
   - Selects least-used, non-blacklisted token
   - Records execution start in state tracking

2. **GitHub Repository Creation**
   - Creates repository using selected token
   - Applies configured repository settings
   - Handles name conflicts and permissions

3. **Local Environment Setup**
   - Clones repository to local workspace
   - Configures Git user settings
   - Sets up project-specific branching

4. **Smart Contract Environment**
   - Initializes blockchain-specific toolchain
   - Installs required dependencies
   - Configures testing framework

5. **AI-Powered Contract Generation**
   - Calls Claude Code with project context
   - Generates production-ready smart contract
   - Includes comprehensive documentation

6. **Compilation and Testing Loop**
   - Compiles contract with blockchain tools
   - Runs automated tests (if enabled)
   - Fixes errors using Claude Code feedback
   - Repeats until successful

7. **Git Operations**
   - Commits generated code with meaningful messages
   - Pushes to remote repository
   - Handles merge conflicts

8. **Pull Request Creation**
   - Creates PR with detailed description
   - Links to deployment information
   - Records PR URL for tracking

9. **State Persistence**
   - Records project completion status
   - Updates token usage statistics
   - Saves execution metrics and results

10. **Token Management**
    - Updates token usage counters
    - Handles rate limiting and blacklisting
    - Prepares for next project execution

## 📊 State Tracking & Token Management

### **Persistent State Features**

The system maintains persistent state across sessions:

- **Token Usage Tracking**: Monitors usage count, last used time, blacklist status
- **Project Completion**: Tracks successful completions, failures, and execution metrics  
- **Session Resume**: Automatically resumes interrupted batch processing
- **Intelligent Token Selection**: Auto-selects least used, healthy tokens

### **State Files**

All state is stored in JSON files in the `secrets/` directory:

```
secrets/
├── tokens.yaml           # Your GitHub tokens
├── token_state.json      # Token usage tracking
├── project_state.json    # Project completion tracking
└── execution_log.json    # Detailed execution logs
```

### **Token Management Features**

**Automatic Token Selection**: System selects optimal token based on:
- Usage frequency (prefers least used)
- Recent usage timing
- Blacklist status
- Rate limit status

**Token Blacklisting**: Automatic blacklisting for:
- Rate limiting errors (403, 429)
- Authentication failures (401)
- Persistent API errors

**Manual Token Override**: Force specific token usage when needed

### **Project Completion Tracking**

**Smart Skip Logic**: Automatically skips completed projects unless:
- `--force` flag is used
- Project completion status is manually reset

**Failure Recovery**: Tracks failed projects with:
- Failure count and timestamps
- Error details and context
- Retry eligibility

### **State Summary Example**

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

## 📊 Monitoring & Results

### **Real-Time Status**
- **Project Progress**: Live updates on current operations
- **Component Health**: Individual component status monitoring
- **Performance Metrics**: Duration, success rates, error patterns
- **Resource Usage**: Token rotation, API calls, disk space

### **Reporting Features**
- **JSON Export**: Machine-readable results for integration
- **CSV Export**: Spreadsheet-compatible format
- **Summary Reports**: Executive-level overview
- **Error Analysis**: Detailed failure pattern recognition
- **Performance Analytics**: Optimization insights

### **Sample Output**
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

## 🛠️ Extensibility

### **Adding New Blockchain Support**
1. Extend `ContractManager` with new blockchain methods
2. Add blockchain-specific configuration options
3. Implement compilation and testing logic
4. Update project templates

### **Custom Error Handling**
1. Create custom exceptions in `core/exceptions.py`
2. Implement error-specific recovery logic
3. Add error patterns to result tracking
4. Update Claude Code prompts for error context

### **Component Customization**
1. Inherit from `BaseComponent`
2. Implement required abstract methods
3. Add to orchestrator component registry
4. Update configuration schema

## 🔒 Security Considerations

- **Token Management**: Secure storage and rotation of GitHub tokens in `secrets/` directory
- **Code Review**: Automated security scanning of generated contracts
- **Network Security**: HTTPS-only communications
- **Error Handling**: Sensitive information filtering in logs
- **Access Control**: Component-level permission management
- **State Persistence**: Secure JSON storage with proper file permissions

## 🚨 Error Recovery

The system handles various failure scenarios:

### **Compilation Errors**
- Sends error context back to Claude Code
- Implements retry logic with exponential backoff
- Maintains error history for pattern analysis

### **GitHub API Limits**
- Automatic token rotation with blacklisting
- Rate limit monitoring with intelligent backoff
- Graceful degradation strategies

### **Network Issues**
- Configurable timeout handling
- Automatic retry mechanisms
- Offline mode capabilities

### **Claude Code Timeouts**
- Fallback to simpler prompts
- Progressive timeout increases
- Manual intervention alerts

### **Token Exhaustion**
If all tokens are blacklisted:
```
Warning: All tokens are blacklisted, resetting blacklist...
```
The system automatically resets and continues.

## 📈 Performance Optimization

### **Parallel Processing**
- Configurable worker threads
- Resource-aware scheduling
- Load balancing across GitHub accounts

### **Caching Strategies**
- Template caching for common contracts
- Configuration caching
- Result caching for repeated operations

### **Resource Management**
- Automatic cleanup of temporary files
- Memory usage monitoring
- Disk space management

### **State-Aware Processing**
- Skip completed projects by default
- Intelligent token selection
- Resume interrupted executions

## 🧪 Testing

### **Unit Tests**
```bash
# Run all unit tests
python -m pytest tests/

# Run specific component tests
python -m pytest tests/test_components.py

# Run with coverage
python -m pytest tests/ --cov=components --cov-report=html
```

### **Integration Tests**
```bash
# Run integration tests
python -m pytest tests/test_integration.py

# Test with sample configuration
python -m pytest tests/ --config tests/sample_config.yaml
```

### **Contract Testing**
```bash
# Test specific project contracts
python main.py --action test --project "ProjectName"

# Run project with testing enabled
python main.py --action single --project "ProjectName" --with-tests
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
- **State Issues**: Check `secrets/` directory for state files
- **Token Issues**: Verify tokens in `secrets/tokens.yaml`

## 📋 Quick Start Checklist

1. ✅ Install Python 3.8+ and dependencies
2. ✅ Setup `config/settings.yaml` with your tokens and projects
3. ✅ Create `secrets/` directory for state tracking
4. ✅ Test with single project: `python main.py --action single --project "YourProject"`
5. ✅ Run batch processing: `python main.py --action run`
6. ✅ Monitor state: `python main.py --action state`

## 💡 Pro Tips

- **Start Small**: Test with single projects before batch processing
- **Monitor State**: Regularly check `python main.py --action state`
- **Token Health**: Reset blacklisted tokens if they're working again
- **Backup State**: Copy `secrets/` directory before major changes
- **Use Force Carefully**: `--force` will reprocess completed projects
- **Testing Optional**: Use `--with-tests` only when you need test validation