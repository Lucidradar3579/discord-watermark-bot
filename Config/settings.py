import os

# Bot Configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'your_bot_token_here')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Channel Configuration
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0')) if os.getenv('LOG_CHANNEL_ID') else None

# File Processing Configuration
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi']

# Watermark Configuration
WATERMARK_OPACITY = float(os.getenv('WATERMARK_OPACITY', '0.7'))
WATERMARK_FONT_SIZE_RATIO = float(os.getenv('WATERMARK_FONT_SIZE_RATIO', '30'))  # Divisor for image size

# Rate Limiting
DM_DELAY_SECONDS = float(os.getenv('DM_DELAY_SECONDS', '1.0'))

# Logging Configuration
MAX_LOG_ENTRIES = int(os.getenv('MAX_LOG_ENTRIES', '1000'))

# Web Server Configuration - GCE compatibility
WEB_SERVER_PORT = int(os.getenv('PORT', '5000'))

# Bot Owner Configuration
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '841757046625534002'))

# Ensure port is always set for deployment
if not os.getenv('PORT'):
    os.environ['PORT'] = str(WEB_SERVER_PORT)

# Validation
if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
    print("⚠️  Warning: DISCORD_BOT_TOKEN environment variable not set or using placeholder value!")
    print("   Please set your Discord bot token in the DISCORD_BOT_TOKEN environment variable.")
    print("   Example: export DISCORD_BOT_TOKEN='your_actual_bot_token'")

if LOG_CHANNEL_ID is None:
    print("ℹ️  Info: LOG_CHANNEL_ID not set. Logging to Discord channel will be disabled.")
    print("   To enable Discord logging, set LOG_CHANNEL_ID environment variable to your log channel ID.")
    print("   Example: export LOG_CHANNEL_ID='123456789012345678'")

print(f"✅ Bot configuration loaded:")
print(f"   - Command Prefix: {COMMAND_PREFIX}")
print(f"   - Max File Size: {MAX_FILE_SIZE_MB}MB")
print(f"   - Log Channel ID: {LOG_CHANNEL_ID or 'Not set'}")
print(f"   - DM Delay: {DM_DELAY_SECONDS}s")
print(f"   - Web Server Port: {WEB_SERVER_PORT}")
print(f"   - Bot Owner ID: {BOT_OWNER_ID or 'Not set'}")
