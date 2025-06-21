"""
Channel settings storage for persistent configuration
"""

import os
import json

class ChannelSettings:
    def __init__(self):
        self.data_file = 'data/channel_settings.json'
        self.ensure_data_dir()
        self.settings = {}
        self.load_settings()
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
    
    def load_settings(self):
        """Load channel settings from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.settings = json.load(f)
        except Exception as e:
            print(f"Error loading channel settings: {e}")
            self.settings = {}
    
    def save_settings(self):
        """Save channel settings to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving channel settings: {e}")
    
    def get_channel_id(self, channel_type: str) -> str:
        """Get saved channel ID for a specific type"""
        return self.settings.get(channel_type, "")
    
    def set_channel_id(self, channel_type: str, channel_id: str):
        """Save channel ID for a specific type"""
        self.settings[channel_type] = channel_id
        self.save_settings()
    
    def get_all_settings(self) -> dict:
        """Get all saved settings"""
        return self.settings.copy()