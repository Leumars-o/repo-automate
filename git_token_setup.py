#!/usr/bin/env python3
# git_token_setup.py
"""
GitHub Token Setup Script
========================

This script helps you set up GitHub tokens for the automation system.
Includes account validation to check for flagged/restricted accounts.
"""

import os
import yaml
import requests
import time
from pathlib import Path

def create_secrets_directory():
    """Create secrets directory if it doesn't exist"""
    secrets_dir = Path('secrets')
    secrets_dir.mkdir(exist_ok=True)
    
    # Create .gitignore to exclude secrets if not exist
    gitignore_path = Path('.gitignore')
    gitignore_content = ""
    
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
    
    if 'secrets/' not in gitignore_content:
        with open(gitignore_path, 'a') as f:
            f.write('\n# Secrets directory\nsecrets/\n')
    
    return secrets_dir

def load_existing_tokens():
    """Load existing tokens from tokens.yaml"""
    tokens_file = Path('secrets/tokens.yaml')
    
    if not tokens_file.exists():
        return []
    
    try:
        with open(tokens_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('tokens', []) if data else []
    except Exception as e:
        print(f"Warning: Could not read existing tokens file: {e}")
        return []

def check_account_validity(username):
    """
    Check GitHub account validity - check if account exists without authentication
    This is the proper way to detect flagged accounts
    """
    print(f"\n🔍 Checking account validity for: {username}")
    
    try:
        # Check if user profile exists WITHOUT authentication - this is key!
        # Flagged accounts return 404 when accessed without auth, even if they exist
        user_response = requests.get(f'https://api.github.com/users/{username}')
        
        if user_response.status_code == 404:
            return {
                'status': 'flagged_or_nonexistent',
                'user_exists': False,
                'message': '❌ Account does not exist, is suspended, or is flagged',
                'valid': False
            }
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            return {
                'status': 'valid',
                'user_exists': True,
                'account_data': user_data,
                'message': '✅ Account is valid and publicly accessible',
                'valid': True
            }
        
        return {
            'status': 'unknown',
            'user_exists': False,
            'message': f'❌ Unexpected response: HTTP {user_response.status_code}',
            'valid': False
        }
        
    except requests.RequestException as e:
        return {
            'status': 'error',
            'user_exists': False,
            'message': f'❌ Error checking account: {str(e)}',
            'valid': False
        }

def get_github_token():
    """Get GitHub token from user input"""
    print("\n" + "="*60)
    print("GITHUB TOKEN SETUP")
    print("="*60)
    print("\nYou need a GitHub Personal Access Token to use this system.")
    print("\nTo create a token:")
    print("1. Go to https://github.com/settings/tokens")
    print("2. Click 'Generate new token (classic)'")
    print("3. Give it a name like 'code-4-stx'")
    print("4. Select these scopes:")
    print("   - repo (Full control of private repositories)")
    print("   - workflow (Update GitHub Action workflows)")
    print("5. Click 'Generate token'")
    print("6. Copy the token (it starts with 'ghp_')")
    
    while True:
        token = input("\nEnter your GitHub token: ").strip()
        
        if not token:
            print("Token cannot be empty!")
            continue
        
        if not token.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_')):
            print("Warning: Token doesn't look like a GitHub token (should start with ghp_, gho_, ghu_, or ghs_)")
            confirm = input("Continue anyway? (y/N): ").lower()
            if confirm != 'y':
                continue
        
        return token

def save_tokens_to_yaml(new_token, secrets_dir):
    """Save tokens to YAML file"""
    tokens_file = secrets_dir / 'tokens.yaml'
    
    # Load existing tokens
    existing_tokens = load_existing_tokens()
    
    # Check if token already exists
    try:
        existing_index = existing_tokens.index(new_token)
        print(f"\n⚠️  Token already exists in {tokens_file}")
        print(f"📍 Token found at index: {existing_index}")
        print("❌ Token will not be added again.")
        return tokens_file, existing_index
    except ValueError:
        # Token doesn't exist, add it
        existing_tokens.append(new_token)
        new_index = len(existing_tokens) - 1
        
        # Create YAML structure
        tokens_data = {
            'tokens': existing_tokens
        }
        
        # Save to YAML file
        with open(tokens_file, 'w') as f:
            yaml.dump(tokens_data, f, default_flow_style=False, indent=2)
        
        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(tokens_file, 0o600)
        except Exception:
            pass  # Windows doesn't support chmod
        
        print(f"\n✓ Token saved to: {tokens_file}")
        print(f"📍 Token added at index: {new_index}")
        print(f"📋 Total tokens: {len(existing_tokens)}")
        return tokens_file, new_index

def test_token_access(token):
    """Test if token works with GitHub API"""
    try:
        from github import Github
        
        print("\n🔄 Testing GitHub token...")
        client = Github(token)
        user = client.get_user()
        username = user.login
        
        print(f"✓ Token is valid!")
        print(f"  - Username: {username}")
        print(f"  - Name: {user.name or 'Not set'}")
        print(f"  - Public repos: {user.public_repos}")
        
        # Try to get email, but don't fail if permission is missing
        try:
            emails = user.get_emails()
            primary_email = None
            
            # Find the primary email
            for email_obj in emails:
                if email_obj.primary:
                    primary_email = email_obj.email
                    break
            
            # If no primary email found, get the first available email
            if not primary_email and emails:
                primary_email = emails[0].email
            
            print(f"📧 Email: {primary_email if primary_email else 'No email found'}")
            
        except Exception as email_error:
            if "404" in str(email_error) or "Not Found" in str(email_error):
                print("📧 Email: Not accessible (token missing 'user:email' scope)")
            else:
                print(f"📧 Email: Error retrieving ({email_error})")
        
        # Check account validity using our new function
        account_status = check_account_validity(username)
        print(f"  {account_status['message']}")
        
        if not account_status['valid']:
            print(f"\n❌ Account validation failed: {account_status['status']}")
            print("This means the account is flagged, suspended, or doesn't exist.")
            continue_choice = input("Continue anyway? (y/N): ").lower()
            if continue_choice != 'y':
                print("❌ Setup cancelled due to account validation failure.")
                return False
        
        # Check rate limit
        try:
            rate_limit = client.get_rate_limit()
            print(f"  - API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
        except Exception:
            print("  - API rate limit: Unable to check")
        
        return True
        
    except ImportError:
        print("⚠️  PyGithub not installed, cannot test token")
        print("   Install with: pip install PyGithub")
        
        # Still try to do basic account validation with requests
        print("\n🔍 Attempting basic account validation...")
        try:
            # Make a simple API call to get user info
            headers = {'Authorization': f'token {token}'}
            response = requests.get('https://api.github.com/user', headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data['login']
                print(f"✓ Basic token validation passed for: {username}")
                
                # Check account validity
                account_status = check_account_validity(username)
                print(f"  {account_status['message']}")
                
                if not account_status['valid']:
                    print(f"\n❌ Account validation failed: {account_status['status']}")
                    continue_choice = input("Continue anyway? (y/N): ").lower()
                    if continue_choice != 'y':
                        print("❌ Setup cancelled due to account validation failure.")
                        return False
                
                return True
            else:
                print(f"❌ Token validation failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Basic validation failed: {e}")
            return False
        
    except Exception as e:
        print(f"✗ Token test failed: {e}")
        return False

def main():
    """Main setup function"""
    
    # Create secrets directory
    secrets_dir = create_secrets_directory()
    
    # Get token from user
    token = get_github_token()
    
    # Test token (includes account validity check now)
    if not test_token_access(token):
        print("\n❌ Token validation failed!")
        retry = input("Do you want to try with a different token? (y/N): ").lower()
        if retry == 'y':
            main()  # Restart the process
            return
        else:
            print("❌ Setup cancelled.")
            return
    
    # Save token and get index information
    tokens_file, token_index = save_tokens_to_yaml(token, secrets_dir)
    
    # Load tokens to check if it was a duplicate
    existing_tokens = load_existing_tokens()
    
    print("\n" + "="*60)
    if token in existing_tokens and token_index < len(existing_tokens) - 1:
        print("TOKEN ALREADY EXISTS!")
        print("="*60)
        print(f"📍 Token exists at index: {token_index}")
        print(f"📋 Total tokens in file: {len(existing_tokens)}")
    else:
        print("TOKEN ADDED SUCCESSFULLY!")
        print("="*60)
    
    print(f"\nYou can now run:")
    print(f"  python main.py --action status")
    print(f"  python main.py --action run")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()