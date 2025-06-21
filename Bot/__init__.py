"""
Discord Sneak Peek Bot

A comprehensive Discord bot for watermarking and distributing game content
with unique tracking IDs to prevent unauthorized leaks.

This package contains:
- commands.py: Discord bot commands and handlers
- watermark.py: Image and video watermarking functionality  
- user_manager.py: Admin whitelist management
- logger.py: Comprehensive logging and tracking system
"""

__version__ = "1.0.0"
__author__ = "Sneak Peek Bot"
__description__ = "Discord bot for watermarked content distribution with leak prevention"

# Package information
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi']
WATERMARK_ID_FORMAT = r'^SP-[A-Z0-9]{5}$'

# Import main classes for easy access
from .watermark import WatermarkProcessor
from .user_manager import UserManager
from .logger import BotLogger

__all__ = [
    'WatermarkProcessor',
    'UserManager', 
    'BotLogger',
    'SUPPORTED_IMAGE_FORMATS',
    'SUPPORTED_VIDEO_FORMATS',
    'WATERMARK_ID_FORMAT'
]
