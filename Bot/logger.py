import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import discord

class BotLogger:
    def __init__(self):
        self.delivery_log_file = "data/delivery_log.json"
        self.log_channel = None
        self.load_logs()
    
    def load_logs(self):
        """Load delivery logs from file"""
        try:
            if os.path.exists(self.delivery_log_file):
                with open(self.delivery_log_file, 'r') as f:
                    self.logs = json.load(f)
            else:
                self.logs = []
        except Exception as e:
            print(f"Error loading logs: {e}")
            self.logs = []
    
    def save_logs(self):
        """Save logs to file"""
        try:
            os.makedirs(os.path.dirname(self.delivery_log_file), exist_ok=True)
            # Keep only the last 1000 logs to prevent file from growing too large
            self.logs = self.logs[-1000:]
            with open(self.delivery_log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    def set_log_channel(self, channel: discord.TextChannel):
        """Set the Discord channel for logging"""
        self.log_channel = channel
    
    async def log_upload(self, uploader: discord.User, watermark_id: str, filename: str, description: str):
        """Log content upload"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'upload',
            'uploader': f"{uploader.display_name} ({uploader.id})",
            'watermark_id': watermark_id,
            'filename': filename,
            'description': description
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Send to log channel if available
        if self.log_channel:
            embed = discord.Embed(
                title="📤 Content Uploaded",
                color=0x2f3136,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Uploader", value=uploader.display_name, inline=True)
            embed.add_field(name="Watermark ID", value=watermark_id, inline=True)
            embed.add_field(name="Filename", value=filename, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            
            try:
                await self.log_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending upload log to channel: {e}")
    
    async def log_delivery(self, recipient: discord.User, watermark_id: str, status: str, sender: discord.User):
        """Log content delivery"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'delivery',
            'recipient': f"{recipient.display_name} ({recipient.id})",
            'watermark_id': watermark_id,
            'status': status,
            'sender': f"{sender.display_name} ({sender.id})"
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Send to log channel if available
        if self.log_channel:
            status_emoji = "✅" if "success" in status else "❌"
            embed = discord.Embed(
                title=f"{status_emoji} Content Delivery",
                color=discord.Color.green() if "success" in status else discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Recipient", value=recipient.display_name, inline=True)
            embed.add_field(name="Watermark ID", value=watermark_id, inline=True)
            embed.add_field(name="Status", value=status.replace("_", " ").title(), inline=True)
            embed.add_field(name="Sent by", value=sender.display_name, inline=True)
            
            try:
                await self.log_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending delivery log to channel: {e}")
    
    async def log_interaction(self, user: discord.User, interaction_type: str, details: str):
        """Log user interaction with watermarked content"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'interaction',
            'user': f"{user.display_name} ({user.id})",
            'interaction_type': interaction_type,
            'details': details
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Send to log channel if available
        if self.log_channel:
            embed = discord.Embed(
                title="👀 Content Interaction",
                color=0x2f3136,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=user.display_name, inline=True)
            embed.add_field(name="Type", value=interaction_type.replace("_", " ").title(), inline=True)
            embed.add_field(name="Details", value=details[:100] + ("..." if len(details) > 100 else ""), inline=False)
            
            try:
                await self.log_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending interaction log to channel: {e}")
    
    async def log_admin_action(self, admin: discord.User, action: str):
        """Log admin actions"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'admin_action',
            'admin': f"{admin.display_name} ({admin.id})",
            'details': action
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Send to log channel if available
        if self.log_channel:
            embed = discord.Embed(
                title="⚙️ Admin Action",
                color=0x2f3136,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Admin", value=admin.display_name, inline=True)
            embed.add_field(name="Action", value=action, inline=False)
            
            try:
                await self.log_channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending admin log to channel: {e}")
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs"""
        return self.logs[-limit:] if self.logs else []
    
    def get_logs_by_watermark_id(self, watermark_id: str) -> List[Dict]:
        """Get all logs for a specific watermark ID"""
        return [log for log in self.logs if log.get('watermark_id') == watermark_id]
    
    def get_logs_by_user(self, user_id: int) -> List[Dict]:
        """Get all logs for a specific user"""
        user_id_str = str(user_id)
        return [log for log in self.logs 
                if user_id_str in log.get('recipient', '') or 
                   user_id_str in log.get('user', '') or 
                   user_id_str in log.get('uploader', '')]
