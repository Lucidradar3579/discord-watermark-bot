"""
Normal content management for public reveals without watermarks
"""

import os
import json
import discord
from datetime import datetime
from typing import Dict, List, Optional

class NormalContentManager:
    def __init__(self):
        self.data_file = 'data/normal_content.json'
        self.content_dir = 'normal_content'
        self.ensure_directories()
        self.content_data = {}
        self.load_content_data()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs('data', exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
    
    def load_content_data(self):
        """Load normal content database"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.content_data = json.load(f)
        except Exception as e:
            print(f"Error loading normal content data: {e}")
            self.content_data = {}
    
    def save_content_data(self):
        """Save normal content database"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.content_data, f, indent=2)
        except Exception as e:
            print(f"Error saving normal content data: {e}")
    
    def generate_content_id(self) -> str:
        """Generate a unique content ID"""
        import random
        import string
        return 'NC-' + ''.join(random.choices(string.digits, k=6))
    
    async def add_content(self, file_path: str, filename: str, description: str, uploader_id: int) -> Dict:
        """Add normal content without watermarking"""
        try:
            content_id = self.generate_content_id()
            
            # Copy file to normal content directory
            import shutil
            saved_filename = f"{content_id}_{filename}"
            saved_path = os.path.join(self.content_dir, saved_filename)
            shutil.copy2(file_path, saved_path)
            
            # Store content info
            content_info = {
                'content_id': content_id,
                'original_filename': filename,
                'saved_filename': saved_filename,
                'description': description,
                'uploader_id': uploader_id,
                'upload_date': datetime.utcnow().isoformat(),
                'file_size': os.path.getsize(saved_path)
            }
            
            self.content_data[content_id] = content_info
            self.save_content_data()
            
            return {
                'status': 'success',
                'content_id': content_id,
                'filename': filename
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_content(self, content_id: str) -> Optional[Dict]:
        """Get content information by ID"""
        return self.content_data.get(content_id)
    
    def get_all_content(self) -> Dict:
        """Get all normal content"""
        return self.content_data
    
    def delete_content(self, content_id: str) -> bool:
        """Delete content and its file"""
        try:
            if content_id in self.content_data:
                content_info = self.content_data[content_id]
                file_path = os.path.join(self.content_dir, content_info['saved_filename'])
                
                # Delete file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Remove from database
                del self.content_data[content_id]
                self.save_content_data()
                return True
            return False
        except Exception as e:
            print(f"Error deleting content {content_id}: {e}")
            return False
    
    def get_content_file_path(self, content_id: str) -> Optional[str]:
        """Get the file path for content"""
        content_info = self.get_content(content_id)
        if content_info:
            file_path = os.path.join(self.content_dir, content_info['saved_filename'])
            if os.path.exists(file_path):
                return file_path
        return None