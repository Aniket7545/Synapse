# state_management.py
"""
State Management for Project Synapse
Handles state persistence and updates throughout workflow
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class StateManager:
    """Manages workflow state persistence and updates"""
    
    def __init__(self, storage_path: str = "logs/states"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, scenario_id: str, state: Dict[str, Any]) -> bool:
        """Save state to persistent storage"""
        try:
            state_file = self.storage_path / f"{scenario_id}.json"
            state_copy = state.copy()
            state_copy["last_updated"] = datetime.now().isoformat()
            
            with open(state_file, 'w') as f:
                json.dump(state_copy, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Failed to save state: {e}")
            return False
    
    def load_state(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Load state from persistent storage"""
        try:
            state_file = self.storage_path / f"{scenario_id}.json"
            
            if state_file.exists():
                with open(state_file, 'r') as f:
                    return json.load(f)
            
            return None
        except Exception as e:
            print(f"Failed to load state: {e}")
            return None
    
    def update_state(self, scenario_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in state"""
        current_state = self.load_state(scenario_id) or {}
        current_state.update(updates)
        return self.save_state(scenario_id, current_state)