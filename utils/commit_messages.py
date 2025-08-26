"""
Commit Message Generator
========================

Generates randomized, professional commit messages for different types of commits
in the smart contract automation workflow.
"""

import random
from typing import Dict, List


class CommitMessageGenerator:
    """Generates professional commit messages for smart contract automation"""
    
    # Smart Contract Implementation Templates
    SMART_CONTRACT_TEMPLATES = [
        "Implemented core {project_name} smart contract",
        "Added {project_name} Clarity contract implementation", 
        "Created {project_name} blockchain contract",
        "Built {project_name} smart contract foundation",
        "Developed {project_name} contract logic",
        "Initialized {project_name} smart contract system",
        "implementation of {project_name} contract architecture",
        "Construct {project_name} blockchain protocol",
        "implemented {project_name} decentralized contract",
        "created deployable {project_name} contract infrastructure",
        "initialized {project_name} smart contract solution",
        "Designed {project_name} blockchain implementation",
        "Built {project_name} Clarity-based contract",
        "Implemented {project_name} decentralized protocol",
        "Created {project_name} smart contract framework",
        "Added {project_name} smart contract implementation",
        "Implemented functional smart contract for {project_name}",
        "Created contract initialization for {project_name}",
        "Implemented contract interface for {project_name}",
        "Added comprehensive smart contract for {project_name}",
        "Utilized clarity predictable smart contract system to Created contract for {project_name}",
        "Created optimized smart contract for Stacks network efficiency", 
        "Implemented gas-efficient smart contract for {project_name}",
        "secure smart contract implementation for {project_name}",
        "clarity smart contract added",
        "smart contract implemented",
        "tested and compliled smart contract for {project_name}",
        "{project_name} smart contract implemented",
        "{project_name} smart contract initialized",
        "{project_name} clarity smart contract implementation"
    ]
    
    
    # Documentation Templates
    DOCUMENTATION_TEMPLATES = [
        "Added comprehensive documentation for {project_name}",
        "Created detailed README and project documentation",
        "Documented {project_name} contract usage and features",
        "Added project documentation and usage examples",
        "Created {project_name} developer documentation",
        "Documented contract deployment and integration guide",
        "Added comprehensive {project_name} project docs",
        "Created user and developer documentation",
        "Documented {project_name} smart contract deployment and usage",
        "Added detailed project README and guides",
        "Created {project_name} technical documentation",
        "Documented contract architecture and design",
        "Added {project_name} integration documentation",
        "Created comprehensive project guide",
        "Added comprehensive project README",
        "Documented contract functions and usage",
        "Created deployment and testing instructions",
        "Added code examples and integration guides", 
        "Documented project structure and architecture",
        "Created developer setup instructions",
        "Readme documentation with project structure and architecture",
        "Created documentation with detailed installation guide",
        "Documented contract interface specifications",        
        "Created documentation with testing and validation procedures",
        "Created Readme documentation with testing and validation procedures",
        "Created documentation with user interaction examples",
        "Created Readme with user interaction examples",
        "Added Readme with contract deployment workflows",
        "Added documentation with contract deployment workflow"
    ]
    
    
    # Final Commit Templates (for the original single commit approach)
    FINAL_COMMIT_TEMPLATES = [
        "Added {project_name} smart contract implementation",
        "Implement {project_name} blockchain solution",
        "Deployed {project_name} Clarity smart contract",
        "Created {project_name} decentralized application core",
        "Build {project_name} smart contract infrastructure",
        "Develop {project_name} blockchain protocol",
        "Launch {project_name} smart contract system",
        "Establish {project_name} blockchain protocol foundation",
        "Integrate {project_name} smart contract functionality",
        "Constructed {project_name} blockchain-based solution",
        "Engineered {project_name} decentralized smart contract",
        "Crafted {project_name} innovative blockchain implementation",
        "Designed {project_name} robust smart contract architecture",
        "Structured {project_name} cutting-edge blockchain solution",
        "Programmed {project_name} scalable smart contract platform",
        "Initialize {project_name} enterprise-grade blockchain solution",
        "Bootstrapped {project_name} next-generation smart contract",
        "Integrated {project_name} revolutionary blockchain protocol",
        "Set-up {project_name} advanced smart contract framework",
        "{project_name} blockchain infrastructure added"
    ]
    
    # Final Commit Details
    FINAL_COMMIT_DETAILS = [
        "- Implemented core contract functionality",
        "- Added comprehensive error handling", 
        "- Integrated security best practices",
        "- Included detailed documentation",
        "- Added contract validation",
        "- Implemented access controls",
        "- Integrated multi-signature support",
        "- Added event logging system",
        "- Implemented emergency pause functionality",
        "- Added performance optimizations",
        "- Implemented governance mechanisms",
        "- Created developer documentation"
    ]
    
    # Final Commit Technical Features
    FINAL_COMMIT_TECHNICAL = [
        "- Leveraged Clarity's built-in safety features",
        "- Utilized Stacks blockchain capabilities",
        "- Integrated with Bitcoin settlement layer",
        "- Implemented predictable smart contract execution",
        "- Added STX token integration",
        "- Created robust transaction handling",
        "- Ensured deterministic contract behavior",
        "- Optimized for Stacks network efficiency",
        "- Integrated continuous integration pipeline"
    ]
    
    @classmethod
    def generate_smart_contract_commit(cls, project_name: str) -> str:
        """Generate single-line commit message for smart contract implementation"""
        template = random.choice(cls.SMART_CONTRACT_TEMPLATES)
        return template.format(project_name=project_name)
    
    @classmethod
    def generate_documentation_commit(cls, project_name: str) -> str:
        """Generate single-line commit message for documentation"""
        template = random.choice(cls.DOCUMENTATION_TEMPLATES)
        return template.format(project_name=project_name)
    
    @classmethod
    def generate_final_commit(cls, project_name: str) -> str:
        """Generate commit message for final/single commit (backward compatibility)"""
        template = random.choice(cls.FINAL_COMMIT_TEMPLATES)
        main_message = template.format(project_name=project_name)
        
        # Select 2-3 general details
        selected_details = random.sample(cls.FINAL_COMMIT_DETAILS, random.randint(2, 3))
        
        # Select 1-2 technical features
        selected_technical = random.sample(cls.FINAL_COMMIT_TECHNICAL, random.randint(1, 2))
        
        # Combine into professional commit message
        commit_message = main_message
        commit_message += "\n"
        commit_message += "\n".join(selected_details)
        commit_message += "\n"
        commit_message += "\n".join(selected_technical)
        
        return commit_message
    
    @classmethod
    def generate_final_commit_single_line(cls, project_name: str) -> str:
        """Generate single-line commit message for final/single commit"""
        template = random.choice(cls.FINAL_COMMIT_TEMPLATES)
        return template.format(project_name=project_name)
    
    @classmethod
    def generate_commit_by_type(cls, commit_type: str, project_name: str) -> str:
        """Generate commit message by type"""
        commit_generators = {
            'smart_contract': cls.generate_smart_contract_commit,
            'documentation': cls.generate_documentation_commit,
            'final': cls.generate_final_commit,
            'final_single_line': cls.generate_final_commit_single_line
        }
        
        if commit_type not in commit_generators:
            raise ValueError(f"Unknown commit type: {commit_type}. Available types: {list(commit_generators.keys())}")
        
        return commit_generators[commit_type](project_name)


# Convenience functions for direct imports
def generate_smart_contract_commit(project_name: str) -> str:
    """Generate single-line smart contract implementation commit message"""
    return CommitMessageGenerator.generate_smart_contract_commit(project_name)


def generate_documentation_commit(project_name: str) -> str:
    """Generate single-line documentation commit message"""
    return CommitMessageGenerator.generate_documentation_commit(project_name)


def generate_final_commit(project_name: str) -> str:
    """Generate final/single commit message with details (backward compatibility)"""
    return CommitMessageGenerator.generate_final_commit(project_name)


def generate_final_commit_single_line(project_name: str) -> str:
    """Generate single-line final/single commit message"""
    return CommitMessageGenerator.generate_final_commit_single_line(project_name)