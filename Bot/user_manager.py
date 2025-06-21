import json
import os
from typing import List, Set

class UserManager:
    def __init__(self):
        self.admins_file = "data/admins.json"
        self.load_admins()
    
    def load_admins(self):
        """Load admin list from file"""
        try:
            if os.path.exists(self.admins_file):
                with open(self.admins_file, 'r') as f:
                    data = json.load(f)
                    self.admins = set(data.get('admins', []))
            else:
                # Initialize with empty admin list
                self.admins = set()
                self.save_admins()
        except Exception as e:
            print(f"Error loading admins: {e}")
            self.admins = set()
    
    def save_admins(self):
        """Save admin list to file"""
        try:
            os.makedirs(os.path.dirname(self.admins_file), exist_ok=True)
            with open(self.admins_file, 'w') as f:
                json.dump({'admins': list(self.admins)}, f, indent=2)
        except Exception as e:
            print(f"Error saving admins: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin"""
        return user_id in self.admins
    
    def add_admin(self, user_id: int) -> bool:
        """Add a user to admin list. Returns True if added, False if already admin"""
        if user_id not in self.admins:
            self.admins.add(user_id)
            self.save_admins()
            return True
        return False
    
    def remove_admin(self, user_id: int) -> bool:
        """Remove a user from admin list. Returns True if removed, False if not admin"""
        if user_id in self.admins:
            self.admins.remove(user_id)
            self.save_admins()
            return True
        return False
    
    def get_admins(self) -> List[int]:
        """Get list of all admin user IDs"""
        return list(self.admins)
    
    def get_admin_count(self) -> int:
        """Get number of admins"""
        return len(self.admins)
