import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import config


class SessionStorage:
    """Manages persistent storage of session cookies, view state, and metadata."""
    
    def __init__(self, file_path: str = None):
        self.file_path = file_path or config.SESSION_STATE_FILE
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load session state from JSON file. Return empty dict if file doesn't exist."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._init_empty()
        return self._init_empty()
    
    def _init_empty(self) -> Dict[str, Any]:
        """Initialize empty session structure."""
        return {
            "cookies": {},
            "view_state": "",
            "view_state_generator": "",
            "event_validation": "",
            "previous_page": "",
            "last_check_time": None,
            "last_notification_time": None,
            "last_notification_type": None,  # "no_slots", "slots_found", "expired"
        }
    
    def _save(self):
        """Save session state to JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def set_cookies(self, cookies: Dict[str, str]):
        """Store cookies from browser/response."""
        self.data["cookies"] = cookies
        self._save()
    
    def get_cookies(self) -> Dict[str, str]:
        """Retrieve stored cookies."""
        return self.data.get("cookies", {})
    
    def set_view_state(self, view_state: str, view_state_generator: str = "", 
                      event_validation: str = "", previous_page: str = ""):
        """Store ASP.NET view state and related hidden fields."""
        self.data["view_state"] = view_state
        if view_state_generator:
            self.data["view_state_generator"] = view_state_generator
        if event_validation:
            self.data["event_validation"] = event_validation
        if previous_page:
            self.data["previous_page"] = previous_page
        self._save()
    
    def get_view_state(self) -> Dict[str, str]:
        """Retrieve all ASP.NET view state fields."""
        return {
            "view_state": self.data.get("view_state", ""),
            "view_state_generator": self.data.get("view_state_generator", ""),
            "event_validation": self.data.get("event_validation", ""),
            "previous_page": self.data.get("previous_page", ""),
        }
    
    def set_last_check_time(self, timestamp: datetime = None):
        """Record when the last check was performed."""
        self.data["last_check_time"] = (timestamp or datetime.now()).isoformat()
        self._save()
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get timestamp of last check."""
        iso_str = self.data.get("last_check_time")
        if iso_str:
            return datetime.fromisoformat(iso_str)
        return None
    
    def set_last_notification(self, notification_type: str, timestamp: datetime = None):
        """Record when and what type of notification was last sent."""
        self.data["last_notification_time"] = (timestamp or datetime.now()).isoformat()
        self.data["last_notification_type"] = notification_type
        self._save()
    
    def get_last_notification(self) -> tuple[Optional[datetime], Optional[str]]:
        """Get timestamp and type of last notification."""
        iso_str = self.data.get("last_notification_time")
        notif_type = self.data.get("last_notification_type")
        if iso_str:
            return datetime.fromisoformat(iso_str), notif_type
        return None, None
    
    def is_session_valid(self) -> bool:
        """Check if session has cookies and view state."""
        return bool(self.data.get("cookies")) and bool(self.data.get("view_state"))
    
    def clear(self):
        """Clear all session data."""
        self.data = self._init_empty()
        self._save()
