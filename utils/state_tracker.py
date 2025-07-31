# utils/state_tracker.py
import json
import time
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
import hashlib

class StateTracker:
    """Tracks token usage and project completion state across sessions"""
    
    def __init__(self, state_dir: str = "secrets"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.token_state_file = self.state_dir / "token_state.json"
        self.project_state_file = self.state_dir / "project_state.json"
        self.execution_log_file = self.state_dir / "execution_log.json"
        
        self.token_state = self._load_token_state()
        self.project_state = self._load_project_state()
        
    def _load_token_state(self) -> Dict[str, Any]:
        """Load token usage state from JSON file"""
        default_state = {
            "current_token_index": 0,
            "token_usage": {},  # token_hash -> {usage_count, last_used, projects_completed}
            "tokens_blacklisted": [],  # List of token hashes that are rate limited or failed
            "last_rotation": None,
            "rotation_count": 0
        }
        
        if not self.token_state_file.exists():
            return default_state
        
        try:
            with open(self.token_state_file, 'r') as f:
                loaded_state = json.load(f)
                # Merge with default to handle new fields
                return {**default_state, **loaded_state}
        except (json.JSONDecodeError, FileNotFoundError):
            return default_state
    
    def _load_project_state(self) -> Dict[str, Any]:
        """Load project completion state from JSON file"""
        default_state = {
            "completed_projects": {},  # project_name -> {status, completion_time, token_used, attempt_count}
            "failed_projects": {},     # project_name -> {last_failure, failure_count, last_error}
            "in_progress": {},         # project_name -> {start_time, token_index, pid}
            "project_queue": [],       # List of projects pending execution
            "last_batch_execution": None,
            "total_executions": 0
        }
        
        if not self.project_state_file.exists():
            return default_state
        
        try:
            with open(self.project_state_file, 'r') as f:
                loaded_state = json.load(f)
                return {**default_state, **loaded_state}
        except (json.JSONDecodeError, FileNotFoundError):
            return default_state
    
    def _save_token_state(self) -> None:
        """Save token state to JSON file"""
        try:
            with open(self.token_state_file, 'w') as f:
                json.dump(self.token_state, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save token state: {e}")
    
    def _save_project_state(self) -> None:
        """Save project state to JSON file"""
        try:
            with open(self.project_state_file, 'w') as f:
                json.dump(self.project_state, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save project state: {e}")
    
    def _log_execution(self, action: str, details: Dict[str, Any]) -> None:
        """Log execution details for debugging and analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        try:
            log_data = []
            if self.execution_log_file.exists():
                with open(self.execution_log_file, 'r') as f:
                    log_data = json.load(f)
            
            log_data.append(log_entry)
            
            # Keep only last 1000 entries to prevent file from growing too large
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
            
            with open(self.execution_log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to log execution: {e}")
    
    def _hash_token(self, token: str) -> str:
        """Create a hash of the token for tracking without storing the actual token"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def initialize_tokens(self, tokens: List[str]) -> None:
        """Initialize token tracking with provided tokens"""
        for i, token in enumerate(tokens):
            token_hash = self._hash_token(token)
            if token_hash not in self.token_state["token_usage"]:
                self.token_state["token_usage"][token_hash] = {
                    "index": i,
                    "usage_count": 0,
                    "last_used": None,
                    "projects_completed": [],
                    "rate_limited": False,
                    "last_error": None
                }
        self._save_token_state()
    
    def get_next_available_token_index(self, tokens: List[str], manual_index: Optional[int] = None) -> int:
        """Get the next available token index, considering usage and blacklist"""
        if manual_index is not None:
            if 0 <= manual_index < len(tokens):
                token_hash = self._hash_token(tokens[manual_index])
                if token_hash not in self.token_state["tokens_blacklisted"]:
                    return manual_index
                else:
                    print(f"Warning: Requested token index {manual_index} is blacklisted, finding alternative...")
            else:
                print(f"Warning: Invalid token index {manual_index}, finding alternative...")
        
        # Find the least used, non-blacklisted token
        available_tokens = []
        for i, token in enumerate(tokens):
            token_hash = self._hash_token(token)
            if token_hash not in self.token_state["tokens_blacklisted"]:
                usage_info = self.token_state["token_usage"].get(token_hash, {"usage_count": 0})
                available_tokens.append((i, usage_info["usage_count"]))
        
        if not available_tokens:
            # All tokens are blacklisted, reset blacklist and use first token
            print("Warning: All tokens are blacklisted, resetting blacklist...")
            self.token_state["tokens_blacklisted"] = []
            self._save_token_state()
            return 0
        
        # Sort by usage count and return the least used
        available_tokens.sort(key=lambda x: x[1])
        return available_tokens[0][0]
    
    def record_token_usage(self, token_index: int, tokens: List[str], project_name: str, success: bool = True, error: str = None) -> None:
        """Record token usage for a project"""
        if token_index >= len(tokens):
            return
        
        token = tokens[token_index]
        token_hash = self._hash_token(token)
        
        if token_hash not in self.token_state["token_usage"]:
            self.token_state["token_usage"][token_hash] = {
                "index": token_index,
                "usage_count": 0,
                "last_used": None,
                "projects_completed": [],
                "rate_limited": False,
                "last_error": None
            }
        
        usage_info = self.token_state["token_usage"][token_hash]
        usage_info["usage_count"] += 1
        usage_info["last_used"] = datetime.now().isoformat()
        usage_info["projects_completed"].append({
            "project": project_name,
            "timestamp": datetime.now().isoformat(),
            "success": success
        })
        
        if not success and error:
            usage_info["last_error"] = error
            # Check if token should be blacklisted (rate limiting, auth errors, etc.)
            if "rate limit" in error.lower() or "forbidden" in error.lower() or "unauthorized" in error.lower():
                if token_hash not in self.token_state["tokens_blacklisted"]:
                    self.token_state["tokens_blacklisted"].append(token_hash)
                    print(f"Token index {token_index} blacklisted due to: {error}")
        
        self._save_token_state()
        
        self._log_execution("token_usage", {
            "token_index": token_index,
            "token_hash": token_hash,
            "project_name": project_name,
            "success": success,
            "error": error
        })
    
    def is_project_completed(self, project_name: str) -> bool:
        """Check if a project has been successfully completed"""
        return project_name in self.project_state["completed_projects"]
    
    def get_incomplete_projects(self, all_projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get list of projects that haven't been completed successfully"""
        incomplete = []
        for project in all_projects:
            project_name = project["name"]
            if not self.is_project_completed(project_name):
                # Also check if it's not currently in progress
                if project_name not in self.project_state["in_progress"]:
                    incomplete.append(project)
        return incomplete
    
    def mark_project_started(self, project_name: str, token_index: int) -> None:
        """Mark a project as started"""
        self.project_state["in_progress"][project_name] = {
            "start_time": datetime.now().isoformat(),
            "token_index": token_index,
            "pid": None  # Could be set to process ID if needed
        }
        self._save_project_state()
        
        self._log_execution("project_started", {
            "project_name": project_name,
            "token_index": token_index
        })
    
    def mark_project_completed(self, project_name: str, token_index: int, success: bool = True, 
                             duration: float = 0, error: str = None, pr_url: str = None) -> None:
        """Mark a project as completed"""
        timestamp = datetime.now().isoformat()
        
        # Remove from in-progress
        if project_name in self.project_state["in_progress"]:
            del self.project_state["in_progress"][project_name]
        
        if success:
            self.project_state["completed_projects"][project_name] = {
                "completion_time": timestamp,
                "token_index": token_index,
                "duration": duration,
                "pr_url": pr_url,
                "status": "success"
            }
        else:
            if project_name not in self.project_state["failed_projects"]:
                self.project_state["failed_projects"][project_name] = {
                    "failure_count": 0,
                    "first_failure": timestamp,
                    "attempts": []
                }
            
            self.project_state["failed_projects"][project_name]["failure_count"] += 1
            self.project_state["failed_projects"][project_name]["last_failure"] = timestamp
            self.project_state["failed_projects"][project_name]["last_error"] = error
            self.project_state["failed_projects"][project_name]["attempts"].append({
                "timestamp": timestamp,
                "token_index": token_index,
                "error": error,
                "duration": duration
            })
        
        self.project_state["total_executions"] += 1
        self._save_project_state()
        
        self._log_execution("project_completed", {
            "project_name": project_name,
            "token_index": token_index,
            "success": success,
            "duration": duration,
            "error": error,
            "pr_url": pr_url
        })
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state"""
        return {
            "token_state": {
                "current_index": self.token_state["current_token_index"],
                "total_tokens": len(self.token_state["token_usage"]),
                "blacklisted_tokens": len(self.token_state["tokens_blacklisted"]),
                "rotation_count": self.token_state["rotation_count"]
            },
            "project_state": {
                "completed_projects": len(self.project_state["completed_projects"]),
                "failed_projects": len(self.project_state["failed_projects"]),
                "in_progress": len(self.project_state["in_progress"]),
                "total_executions": self.project_state["total_executions"]
            }
        }
    
    def reset_state(self, reset_tokens: bool = False, reset_projects: bool = False) -> None:
        """Reset tracking state (useful for testing or starting fresh)"""
        if reset_tokens:
            self.token_state = self._load_token_state().__class__.__dict__['_load_token_state'](self)
            self.token_state_file.unlink(missing_ok=True)
            
        if reset_projects:
            self.project_state = self._load_project_state().__class__.__dict__['_load_project_state'](self)
            self.project_state_file.unlink(missing_ok=True)
        
        if reset_tokens or reset_projects:
            print("State tracking files reset successfully")
    
    def cleanup_stale_progress(self, max_age_hours: int = 24) -> None:
        """Clean up stale in-progress entries (from crashed/interrupted executions)"""
        current_time = datetime.now()
        stale_projects = []
        
        for project_name, progress_info in self.project_state["in_progress"].items():
            start_time = datetime.fromisoformat(progress_info["start_time"])
            age_hours = (current_time - start_time).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                stale_projects.append(project_name)
        
        for project_name in stale_projects:
            del self.project_state["in_progress"][project_name]
            print(f"Cleaned up stale in-progress entry for project: {project_name}")
        
        if stale_projects:
            self._save_project_state()