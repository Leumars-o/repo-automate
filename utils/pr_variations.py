# utils/pr_variations.py
import random
from typing import Dict, List

class PRVariations:
    """Contains variations for pull request titles and descriptions"""
    
    # 20 different PR title templates
    PR_TITLES = [
        "Add {project_name} smart contract",
        "Implement {project_name} blockchain solution",
        "Deploy {project_name} smart contract system",
        "Introduce {project_name} decentralized application",
        "Create {project_name} blockchain infrastructure",
        "Built {project_name} smart contract protocol",
        "Launch {project_name} DeFi implementation",
        "Establish {project_name} blockchain framework",
        "Developed {project_name} smart contract architecture",
        "Initialize {project_name} decentralized protocol",
        "Construct {project_name} blockchain solution",
        "Engineer {project_name} smart contract platform",
        "Implemented {project_name} blockchain application",
        "Created {project_name} smart contract ecosystem",
        "Integrate {project_name} blockchain technology",
        "{project_name} decentralized protocol implementation",
        "{project_name} blockchain application implementation"
    ]
    
    # Project type descriptions
    PROJECT_DESCRIPTIONS = [
        "This pull request adds the smart contract implementation and comprehensive documentation for {project_name}.",
        "This PR introduces a fully-featured blockchain solution for {project_name} with robust functionality.",
        "This implementation provides a complete smart contract system for {project_name} with security features.",
        "This pull request delivers a production-ready blockchain application for {project_name}.",
        "This PR establishes a comprehensive decentralized protocol for {project_name} operations.",
        "This implementation creates a scalable smart contract infrastructure for {project_name}.",
        "This pull request introduces an innovative blockchain framework for {project_name}.",
        "This PR delivers a feature-rich smart contract platform for {project_name} ecosystem.",
        "This implementation provides a secure and efficient blockchain solution for {project_name}.",
        "This pull request establishes a complete stacks blockchain protocol for {project_name} operations.",
        "This PR introduces a functional smart contract system for {project_name}.",
        "This implementation delivers advanced blockchain functionality for {project_name}.",
        "This pull request creates a comprehensive decentralized application for {project_name}.",
        "This PR establishes a robust smart contract ecosystem for {project_name}.",
        "This implementation provides cutting-edge blockchain technology for {project_name}.",
        "This pull request introduces a high-performance smart contract for {project_name}.",
        "This PR implements important changes for {project_name}.",
        "This implementation creates a smart contract platform for {project_name}.",
        "This pull request creates an efficent blockchain protocol for {project_name}.",
        "This PR introduces a stacks smart contract framework for {project_name}."
    ]

    @classmethod
    def get_random_title(cls, project_name: str) -> str:
        """Get a random PR title"""
        template = random.choice(cls.PR_TITLES)
        return template.format(project_name=project_name)
    
    @classmethod
    def get_random_description(cls, project_name: str) -> str:
        """Get a random project description"""
        template = random.choice(cls.PROJECT_DESCRIPTIONS)
        return template.format(project_name=project_name)
    
    @classmethod
    def generate_pr_content(cls, project_name: str) -> Dict[str, str]:
        """Generate complete PR content with title and body"""
        title = cls.get_random_title(project_name)
        description = cls.get_random_description(project_name)
        
        body = f"""# {project_name} Smart Contract

                    {description}
                    """
        
        return {
            'title': title,
            'body': body
        }