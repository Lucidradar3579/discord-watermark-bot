#!/usr/bin/env python3
import discord
from discord.ext import commands
import os
import asyncio
import json
import tempfile
import requests
from datetime import datetime
from bot.watermark import WatermarkProcessor
from bot.user_manager import UserManager
from bot.logger import BotLogger
from bot.normal_content import NormalContentManager

# Your Discord User ID as bot owner
BOT_OWNER_ID = 841757046625534002

# Bot setup with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize components
watermark_processor = WatermarkProcessor()
user_manager = UserManager()
normal_content_manager = NormalContentManager()
logger = BotLogger()

def is_owner(user_id):
    """Check if user is the bot owner"""
    return user_id == BOT_OWNER_ID

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot owner ID: {BOT_OWNER_ID}')
    
    # Add persistent view to handle buttons after restart
    bot.add_view(RevealView(""))
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="test", description="Test if you have bot owner permissions")
async def test_command(interaction: discord.Interaction):
    """Test command to verify bot owner permissions"""
    user_id = interaction.user.id
    print(f"Test command - User ID: {user_id}, Bot Owner ID: {BOT_OWNER_ID}")
    
    if is_owner(user_id):
        await interaction.response.send_message(f"✅ Success! You are recognized as the bot owner.\nYour ID: {user_id}\nBot Owner ID: {BOT_OWNER_ID}", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Not authorized.\nYour ID: {user_id}\nBot Owner ID: {BOT_OWNER_ID}", ephemeral=True)

@bot.tree.command(name="setup", description="Bot setup command")
async def setup_command(interaction: discord.Interaction):
    """Setup command for bot owner"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("✅ Setup successful! You have bot owner privileges.", ephemeral=True)

@bot.tree.command(name="upload", description="Upload and watermark content")
async def upload_command(interaction: discord.Interaction):
    """Upload and watermark content"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Create upload modal
    modal = UploadModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="reveal", description="Reveal content - choose basic or booster type")
async def reveal_command(interaction: discord.Interaction):
    """Unified reveal command with type selection"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Create reveal type selection with dropdown
    embed = discord.Embed(
        title="Content Reveal System",
        description="Select reveal type from the dropdown below:",
        color=0x00ff00
    )
    
    view = RevealTypeDropdownView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add_admin", description="Add someone as bot admin")
async def add_admin_command(interaction: discord.Interaction, user: discord.Member):
    """Add a bot admin"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    if user_manager.is_admin(user.id):
        await interaction.response.send_message(f"{user.mention} is already a bot admin.", ephemeral=True)
        return
    
    user_manager.add_admin(user.id)
    await interaction.response.send_message(f"{user.mention} has been added as a bot admin.", ephemeral=True)

@bot.tree.command(name="trace", description="Trace who downloaded specific watermarked content")
async def trace_command(interaction: discord.Interaction, watermark_id: str):
    """Trace downloads for specific watermarked content"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Get processed file info
    processed_file = watermark_processor.get_processed_file(watermark_id)
    if not processed_file:
        await interaction.response.send_message("Watermark ID not found.", ephemeral=True)
        return
    
    # Load claims to see who downloaded
    claims_file = 'data/reveal_claims.json'
    claimed_users = []
    
    try:
        if os.path.exists(claims_file):
            with open(claims_file, 'r') as f:
                all_claims = json.load(f)
                claimed_users = all_claims.get(watermark_id, [])
    except:
        claimed_users = []
    
    # Create trace report
    embed = discord.Embed(
        title=f"Trace Report: {watermark_id}",
        description=f"**File:** {processed_file.get('original_filename', 'Unknown')}\n**Description:** {processed_file.get('description', 'No description')}",
        color=0xff0000
    )
    
    if claimed_users:
        user_list = []
        for user_id_str in claimed_users:
            try:
                user_id = int(user_id_str)
                user = bot.get_user(user_id) or await bot.fetch_user(user_id)
                user_list.append(f"• {user.display_name} ({user.mention}) - ID: {user_id}")
            except:
                user_list.append(f"• Unknown User - ID: {user_id_str}")
        
        embed.add_field(
            name=f"Downloaded by {len(claimed_users)} user(s):",
            value="\n".join(user_list[:10]) + (f"\n... and {len(user_list)-10} more" if len(user_list) > 10 else ""),
            inline=False
        )
    else:
        embed.add_field(
            name="Downloads:",
            value="No downloads recorded",
            inline=False
        )
    
    # Add upload info
    upload_date = processed_file.get('created_at', 'Unknown')
    if upload_date != 'Unknown' and 'T' in upload_date:
        try:
            dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            upload_date = dt.strftime('%d-%m-%Y at %H:%M UTC')
        except:
            upload_date = upload_date.split('T')[0]
    
    embed.add_field(
        name="Upload Date:",
        value=upload_date,
        inline=True
    )
    
    embed.add_field(
        name="Total Downloads:",
        value=str(len(claimed_users)),
        inline=True
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="trace_all", description="Show download statistics for all content")
async def trace_all_command(interaction: discord.Interaction):
    """Show download statistics for all watermarked content"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Get all processed files
    all_files = watermark_processor.get_all_processed_files()
    if not all_files:
        await interaction.response.send_message("No watermarked content found.", ephemeral=True)
        return
    
    # Load all claims
    claims_file = 'data/reveal_claims.json'
    all_claims = {}
    try:
        if os.path.exists(claims_file):
            with open(claims_file, 'r') as f:
                all_claims = json.load(f)
    except:
        all_claims = {}
    
    # Create summary report
    embed = discord.Embed(
        title="Complete Trace Report",
        description="Download statistics for all watermarked content:",
        color=0x0099ff
    )
    
    total_files = len(all_files)
    total_downloads = sum(len(claims) for claims in all_claims.values())
    
    embed.add_field(name="Total Files:", value=str(total_files), inline=True)
    embed.add_field(name="Total Downloads:", value=str(total_downloads), inline=True)
    embed.add_field(name="Average Downloads:", value=f"{total_downloads/total_files:.1f}" if total_files > 0 else "0", inline=True)
    
    # Show top downloaded content
    file_stats = []
    for watermark_id, file_info in all_files.items():
        download_count = len(all_claims.get(watermark_id, []))
        filename = file_info.get('original_filename', 'Unknown')[:30]
        file_stats.append((download_count, watermark_id, filename))
    
    file_stats.sort(reverse=True)  # Sort by download count
    
    if file_stats:
        top_files = []
        for i, (count, wid, filename) in enumerate(file_stats[:10]):
            top_files.append(f"{i+1}. **{filename}** ({wid})\n   Downloads: {count}")
        
        embed.add_field(
            name="Most Downloaded Content:",
            value="\n".join(top_files) if top_files else "No downloads yet",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="send_dm", description="Send watermarked content directly to a specific user")
async def send_dm_command(interaction: discord.Interaction, user: discord.Member, watermark_id: str):
    """Send watermarked content directly to a user via DM"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Get processed file info
    processed_file = watermark_processor.get_processed_file(watermark_id)
    if not processed_file:
        await interaction.response.send_message("Watermark ID not found.", ephemeral=True)
        return
    
    # Create DM message
    upload_date = processed_file.get('created_at', 'Unknown')
    if upload_date != 'Unknown' and 'T' in upload_date:
        try:
            dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            upload_date = dt.strftime('%d-%m-%Y')
        except:
            upload_date = upload_date.split('T')[0]
    
    dm_message = f"""**{processed_file.get('original_filename', 'Content')}** (Admin Delivery)

Date: {upload_date}
{processed_file.get('description', '')}

This content was sent directly by {interaction.user.display_name}."""
    
    try:
        # Send watermarked file
        processed_filename = processed_file.get('processed_filename', '')
        if processed_filename:
            watermarked_file_path = os.path.join('output', processed_filename)
            if os.path.exists(watermarked_file_path):
                with open(watermarked_file_path, 'rb') as f:
                    file = discord.File(f, filename=processed_filename)
                    await user.send(content=dm_message, file=file)
            else:
                await user.send(dm_message + "\n\nFile not available on server.")
        else:
            await user.send(dm_message + "\n\nNo file available.")
        
        # Record this manual delivery in claims
        claims_file = 'data/reveal_claims.json'
        os.makedirs('data', exist_ok=True)
        
        all_claims = {}
        if os.path.exists(claims_file):
            try:
                with open(claims_file, 'r') as f:
                    all_claims = json.load(f)
            except:
                all_claims = {}
        
        if watermark_id not in all_claims:
            all_claims[watermark_id] = []
        
        user_id_str = str(user.id)
        if user_id_str not in all_claims[watermark_id]:
            all_claims[watermark_id].append(user_id_str)
        
        try:
            with open(claims_file, 'w') as f:
                json.dump(all_claims, f, indent=2)
        except Exception as e:
            print(f"Failed to save manual delivery record: {e}")
        
        # Defer after we know we're processing
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"Successfully sent {processed_file.get('original_filename', 'content')} to {user.display_name} via DM.", ephemeral=True)
        
    except discord.Forbidden:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Cannot send DM to {user.display_name}. They may have DMs disabled.", ephemeral=True)
        else:
            await interaction.followup.send(f"Cannot send DM to {user.display_name}. They may have DMs disabled.", ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Failed to send content to {user.display_name}: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"Failed to send content to {user.display_name}: {str(e)}", ephemeral=True)

@bot.tree.command(name="bulk_dm", description="Send content to multiple users via dropdown selection")
async def bulk_dm_command(interaction: discord.Interaction):
    """Send watermarked content to multiple users"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    # Get all processed files
    all_files = watermark_processor.get_all_processed_files()
    if not all_files:
        await interaction.response.send_message("No watermarked content available for bulk sending.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="Bulk DM Delivery",
        description="Select content to send to multiple users:",
        color=0xff9500
    )
    
    view = BulkDMSelectView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="settings", description="Bot settings and configuration")
async def settings_command(interaction: discord.Interaction):
    """Bot settings command"""
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="Bot Settings & Status",
        description="Current bot configuration and statistics:",
        color=0x2f3136
    )
    
    # Get statistics
    all_files = watermark_processor.get_all_processed_files()
    all_content = normal_content_manager.get_all_content()
    
    # Load claims for statistics
    claims_file = 'data/reveal_claims.json'
    all_claims = {}
    try:
        if os.path.exists(claims_file):
            with open(claims_file, 'r') as f:
                all_claims = json.load(f)
    except:
        all_claims = {}
    
    total_downloads = sum(len(claims) for claims in all_claims.values())
    
    embed.add_field(
        name="📊 Content Statistics",
        value=f"Watermarked Files: {len(all_files)}\nBasic Content: {len(all_content)}\nTotal Downloads: {total_downloads}",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Bot Features",
        value="✅ Watermarking (300-1080px)\n✅ Enhanced Marvel Branding\n✅ One-per-user Reveals\n✅ Download Tracking\n✅ Individual DM Delivery\n✅ Bulk DM System",
        inline=True
    )
    
    embed.add_field(
        name="👑 Bot Owner",
        value=f"Owner ID: {BOT_OWNER_ID}\nYour ID: {interaction.user.id}\nStatus: {'✅ Verified Owner' if interaction.user.id == BOT_OWNER_ID else '❌ Not Owner'}",
        inline=False
    )
    
    embed.add_field(
        name="📋 Available Commands",
        value="/upload - Upload & watermark content\n/reveal - Create basic/booster reveals\n/trace - Track downloads\n/trace_all - Full statistics\n/send_dm - Individual delivery\n/bulk_dm - Bulk delivery\n/add_admin - Manage admins\n/settings - This panel",
        inline=False
    )
    
    embed.add_field(
        name="⚠️ Channel Setup",
        value="To set reveal channels, use the bot in the desired channels:\n• Use `/reveal` in your booster reveal channel\n• The bot will remember channel locations automatically\n• No manual channel configuration needed",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="check_admin", description="Check if a user is a bot admin")
async def check_admin_command(interaction: discord.Interaction, user: discord.Member = None):
    """Check admin status"""
    
    target_user = user if user else interaction.user
    
    if is_owner(target_user.id) or user_manager.is_admin(target_user.id):
        await interaction.response.send_message(f"{target_user.mention} is a bot admin.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{target_user.mention} is not a bot admin.", ephemeral=True)

class UploadModal(discord.ui.Modal, title="Upload Content"):
    def __init__(self):
        super().__init__()

    filename = discord.ui.TextInput(
        label="File URL",
        placeholder="Paste the direct link to your image or video file...",
        style=discord.TextStyle.short,
        max_length=500,
        required=True
    )
    
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Brief description of the content...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Download the file
            response = requests.get(self.filename.value, timeout=30)
            response.raise_for_status()
            
            # Get file extension
            file_ext = os.path.splitext(self.filename.value)[1].lower()
            if not file_ext:
                content_type = response.headers.get('content-type', '')
                if 'image/jpeg' in content_type:
                    file_ext = '.jpg'
                elif 'image/png' in content_type:
                    file_ext = '.png'
                elif 'video/mp4' in content_type:
                    file_ext = '.mp4'
                else:
                    file_ext = '.bin'
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            # Generate filename
            original_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            
            try:
                # Process the file with watermark
                result = await watermark_processor.process_file(
                    temp_path, 
                    original_filename, 
                    self.description.value or "No description"
                )
                
                watermark_id = result.get('watermark_id', 'Unknown')
                
                await interaction.followup.send(f"File uploaded and watermarked successfully!\nWatermark ID: `{watermark_id}`\nUse `/reveal {watermark_id}` to create a booster reveal.", ephemeral=True)
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except requests.RequestException as e:
            await interaction.followup.send(f"Failed to download file: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Upload failed: {str(e)}", ephemeral=True)

class RevealView(discord.ui.View):
    def __init__(self, watermark_id: str):
        super().__init__(timeout=None)
        self.watermark_id = watermark_id
        
        # Load existing claims
        claims_file = 'data/reveal_claims.json'
        try:
            if os.path.exists(claims_file):
                with open(claims_file, 'r') as f:
                    all_claims = json.load(f)
                    self.claimed_users = set(all_claims.get(watermark_id, []))
            else:
                self.claimed_users = set()
        except:
            self.claimed_users = set()

    def _save_claims(self):
        claims_file = 'data/reveal_claims.json'
        os.makedirs('data', exist_ok=True)
        
        all_claims = {}
        if os.path.exists(claims_file):
            try:
                with open(claims_file, 'r') as f:
                    all_claims = json.load(f)
            except:
                all_claims = {}
        
        all_claims[self.watermark_id] = list(self.claimed_users)
        
        try:
            with open(claims_file, 'w') as f:
                json.dump(all_claims, f, indent=2)
        except Exception as e:
            print(f"Failed to save claims: {e}")

    @discord.ui.button(label="🎁 Claim Your Copy", style=discord.ButtonStyle.primary, custom_id="persistent_reveal_button")
    async def reveal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ONE COPY PER USER - prevents duplicate claims"""
        try:
            # Extract watermark_id from custom_id for persistent buttons
            if button.custom_id and button.custom_id.startswith('reveal_'):
                watermark_id = button.custom_id.replace('reveal_', '')
            else:
                watermark_id = self.watermark_id
                
            await interaction.response.defer(ephemeral=True)
            
            # Load current claims for this specific content
            claims_file = 'data/reveal_claims.json'
            all_claims = {}
            if os.path.exists(claims_file):
                try:
                    with open(claims_file, 'r') as f:
                        all_claims = json.load(f)
                except:
                    all_claims = {}
            
            user_id_str = str(interaction.user.id)
            claimed_users = set(all_claims.get(watermark_id, []))
            
            if user_id_str in claimed_users:
                await interaction.followup.send("You already have this content.", ephemeral=True)
                return
            
            # Add user to claims
            claimed_users.add(user_id_str)
            all_claims[watermark_id] = list(claimed_users)
            
            # Save claims
            os.makedirs('data', exist_ok=True)
            try:
                with open(claims_file, 'w') as f:
                    json.dump(all_claims, f, indent=2)
            except Exception as e:
                print(f"Failed to save claims: {e}")
            
            processed_file = watermark_processor.get_processed_file(watermark_id)
            if not processed_file:
                await interaction.followup.send("Content not found.", ephemeral=True)
                return
            
            # Create DM message
            upload_date = processed_file.get('created_at', 'Unknown')
            if upload_date != 'Unknown' and 'T' in upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    upload_date = dt.strftime('%d-%m-%Y')
                except:
                    upload_date = upload_date.split('T')[0]
            
            dm_message = f"""**{processed_file.get('original_filename', 'Content')}**

Date: {upload_date}
{processed_file.get('description', '')}"""
            
            # Send watermarked file
            processed_filename = processed_file.get('processed_filename', '')
            if processed_filename:
                watermarked_file_path = os.path.join('output', processed_filename)
                if os.path.exists(watermarked_file_path):
                    with open(watermarked_file_path, 'rb') as f:
                        file = discord.File(f, filename=processed_filename)
                        await interaction.user.send(content=dm_message, file=file)
                else:
                    await interaction.user.send(dm_message + "\n\nFile not available.")
            else:
                await interaction.user.send(dm_message + "\n\nNo file available.")
            
            await interaction.followup.send("Sent to your DMs.", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("Can't send DM. Check your privacy settings.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("Error sending reveal info.", ephemeral=True)

# Dropdown menu system for reveals
class RevealTypeDropdownView(discord.ui.View):
    """View with dropdown to select reveal type"""
    def __init__(self):
        super().__init__(timeout=None)
        dropdown = RevealTypeDropdown()
        self.add_item(dropdown)

class RevealTypeDropdown(discord.ui.Select):
    """Dropdown to select reveal type"""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Booster Reveal",
                description="Watermarked content sent to DMs via button",
                value="booster",
                emoji="🎯"
            ),
            discord.SelectOption(
                label="Basic Reveal", 
                description="Content posted directly to public channel",
                value="basic",
                emoji="📢"
            )
        ]
        
        super().__init__(placeholder="Choose reveal type...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if self.values[0] == "booster":
                # Handle booster reveal selection
                processed_files = watermark_processor.get_all_processed_files()
                
                if not processed_files:
                    await interaction.followup.send("No watermarked content available for booster reveal.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="Select Content for Booster Reveal",
                    description="Choose which watermarked content to reveal:",
                    color=0x00ff00
                )
                
                view = BoosterRevealSelectView()
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
            elif self.values[0] == "basic":
                # Handle basic reveal selection
                all_content = normal_content_manager.get_all_content()
                
                if not all_content:
                    await interaction.followup.send("No basic content available for reveal.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="Select Content for Basic Reveal",
                    description="Choose which content to reveal:",
                    color=0x00ff00
                )
                
                view = BasicRevealSelectView()
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send("Failed to process reveal type selection.", ephemeral=True)

class BoosterRevealSelectView(discord.ui.View):
    """View with dropdown to select watermarked content for booster reveal"""
    def __init__(self):
        super().__init__(timeout=None)
        dropdown = BoosterRevealDropdown()
        self.add_item(dropdown)

class BoosterRevealDropdown(discord.ui.Select):
    """Dropdown to select watermarked content for booster reveal"""
    def __init__(self):
        # Get all watermarked content
        all_files = watermark_processor.get_all_processed_files()
        
        options = []
        if all_files:
            for watermark_id, file_info in list(all_files.items())[:25]:  # Discord limit
                filename = file_info.get('original_filename', 'Unknown file')[:50]
                description = file_info.get('description', 'No description')[:50]
                
                options.append(discord.SelectOption(
                    label=f"{filename}",
                    description=f"{watermark_id} - {description}",
                    value=watermark_id
                ))
        
        if not options:
            options.append(discord.SelectOption(
                label="No content available",
                description="Upload watermarked content first",
                value="none"
            ))
        
        super().__init__(placeholder="Choose watermarked content for booster reveal...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if self.values[0] == "none":
                await interaction.followup.send("No watermarked content available. Upload content first.", ephemeral=True)
                return
            
            watermark_id = self.values[0]
            
            # Get file info
            file_info = watermark_processor.get_processed_file(watermark_id)
            if not file_info:
                await interaction.followup.send("Content not found.", ephemeral=True)
                return
            
            # Create reveal embed for booster channel with custom message
            embed = discord.Embed(
                description="<:E_:1382852913071653046> **Hello Enhanced <@&809060225432813619> ! **<:E_:1382852913071653046>\n> Here's a look at our next character for ***Marvel*** ***Enhanced***!\n> Click \"Click to Reveal\" to receive the reveal through DMs.",
                color=0xff9500
            )
            
            # Create persistent reveal button with watermark ID
            view = RevealView(watermark_id)
            # Set custom_id with watermark_id for persistence
            view.children[0].custom_id = f"reveal_{watermark_id}"
            
            # Send to current channel (this automatically sets it as the booster reveal channel)
            channel = interaction.channel
            await channel.send(embed=embed, view=view)
            await interaction.followup.send(f"Booster reveal for {file_info.get('original_filename', 'file')} posted to {channel.mention}", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Error posting booster reveal: {str(e)}", ephemeral=True)

class BasicRevealSelectView(discord.ui.View):
    """View with dropdown to select basic content for reveal"""
    def __init__(self):
        super().__init__(timeout=None)
        dropdown = BasicRevealDropdown()
        self.add_item(dropdown)

class BasicRevealDropdown(discord.ui.Select):
    """Dropdown to select basic content for reveal"""
    def __init__(self):
        # Get all basic content
        all_content = normal_content_manager.get_all_content()
        
        options = []
        if all_content:
            for content_id, content_info in list(all_content.items())[:25]:  # Discord limit
                filename = content_info.get('filename', 'Unknown file')[:50]
                description = content_info.get('description', 'No description')[:50]
                
                options.append(discord.SelectOption(
                    label=f"{filename}",
                    description=f"{content_id} - {description}",
                    value=content_id
                ))
        
        if not options:
            options.append(discord.SelectOption(
                label="No content available",
                description="Upload basic content first",
                value="none"
            ))
        
        super().__init__(placeholder="Choose basic content for reveal...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if self.values[0] == "none":
                await interaction.followup.send("No basic content available. Upload content first.", ephemeral=True)
                return
            
            content_id = self.values[0]
            
            # Get content info
            content_info = normal_content_manager.get_content(content_id)
            if not content_info:
                await interaction.followup.send("Content not found.", ephemeral=True)
                return
            
            # Get file path
            file_path = normal_content_manager.get_content_file_path(content_id)
            if not file_path or not os.path.exists(file_path):
                await interaction.followup.send("Content file not found on server.", ephemeral=True)
                return
            
            # Send to current channel
            try:
                with open(file_path, 'rb') as f:
                    file = discord.File(f, filename=content_info.get('filename', 'content'))
                    
                    # Create simple message for basic reveal
                    message = f"**{content_info.get('filename', 'Content')}**\n{content_info.get('description', '')}"
                    
                    # Send to current channel (this automatically sets it as the basic reveal channel)
                    channel = interaction.channel
                    await channel.send(content=message, file=file)
                
                await interaction.followup.send(f"Basic reveal for {content_info.get('filename', 'file')} posted to {channel.mention}", ephemeral=True)
                
            except Exception as e:
                await interaction.followup.send(f"Error posting basic reveal: {str(e)}", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"Error processing basic reveal: {str(e)}", ephemeral=True)

# Bulk DM system
class BulkDMSelectView(discord.ui.View):
    """View for selecting content for bulk DM"""
    def __init__(self):
        super().__init__(timeout=None)
        dropdown = BulkDMContentDropdown()
        self.add_item(dropdown)

class BulkDMContentDropdown(discord.ui.Select):
    """Dropdown to select content for bulk DM"""
    def __init__(self):
        all_files = watermark_processor.get_all_processed_files()
        
        options = []
        if all_files:
            for watermark_id, file_info in list(all_files.items())[:25]:
                filename = file_info.get('original_filename', 'Unknown file')[:50]
                description = file_info.get('description', 'No description')[:50]
                
                options.append(discord.SelectOption(
                    label=f"{filename}",
                    description=f"{watermark_id} - {description}",
                    value=watermark_id
                ))
        
        if not options:
            options.append(discord.SelectOption(
                label="No content available",
                description="Upload content first",
                value="none"
            ))
        
        super().__init__(placeholder="Choose content for bulk DM...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            if self.values[0] == "none":
                await interaction.followup.send("No content available.", ephemeral=True)
                return
            
            watermark_id = self.values[0]
            file_info = watermark_processor.get_processed_file(watermark_id)
            
            if not file_info:
                await interaction.followup.send("Content not found.", ephemeral=True)
                return
            
            # Show bulk DM modal for user input
            modal = BulkDMModal(watermark_id, file_info.get('original_filename', 'content'))
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

class BulkDMModal(discord.ui.Modal):
    def __init__(self, watermark_id: str, filename: str):
        super().__init__(title="Bulk DM Delivery")
        self.watermark_id = watermark_id
        self.filename = filename

    user_list = discord.ui.TextInput(
        label="User IDs or Mentions",
        placeholder="Enter user IDs or mentions separated by spaces or commas...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parse user input
            user_input = self.user_list.value.replace(',', ' ').replace('<@', '').replace('>', '').replace('!', '')
            user_ids = []
            
            for item in user_input.split():
                try:
                    user_id = int(item.strip())
                    user_ids.append(user_id)
                except:
                    continue
            
            if not user_ids:
                await interaction.followup.send("No valid user IDs found in input.", ephemeral=True)
                return
            
            # Get processed file info
            processed_file = watermark_processor.get_processed_file(self.watermark_id)
            if not processed_file:
                await interaction.followup.send("Content not found.", ephemeral=True)
                return
            
            # Prepare DM message
            upload_date = processed_file.get('created_at', 'Unknown')
            if upload_date != 'Unknown' and 'T' in upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    upload_date = dt.strftime('%d-%m-%Y')
                except:
                    upload_date = upload_date.split('T')[0]
            
            dm_message = f"""**{processed_file.get('original_filename', 'Content')}** (Bulk Delivery)

Date: {upload_date}
{processed_file.get('description', '')}

This content was sent via bulk delivery by {interaction.user.display_name}."""
            
            # Send to all users
            successful_sends = []
            failed_sends = []
            
            for user_id in user_ids:
                try:
                    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
                    
                    # Send file
                    processed_filename = processed_file.get('processed_filename', '')
                    if processed_filename:
                        watermarked_file_path = os.path.join('output', processed_filename)
                        if os.path.exists(watermarked_file_path):
                            with open(watermarked_file_path, 'rb') as f:
                                file = discord.File(f, filename=processed_filename)
                                await user.send(content=dm_message, file=file)
                        else:
                            await user.send(dm_message + "\n\nFile not available.")
                    else:
                        await user.send(dm_message + "\n\nNo file available.")
                    
                    successful_sends.append(user.display_name)
                    
                    # Record delivery
                    claims_file = 'data/reveal_claims.json'
                    os.makedirs('data', exist_ok=True)
                    
                    all_claims = {}
                    if os.path.exists(claims_file):
                        try:
                            with open(claims_file, 'r') as f:
                                all_claims = json.load(f)
                        except:
                            all_claims = {}
                    
                    if self.watermark_id not in all_claims:
                        all_claims[self.watermark_id] = []
                    
                    user_id_str = str(user_id)
                    if user_id_str not in all_claims[self.watermark_id]:
                        all_claims[self.watermark_id].append(user_id_str)
                    
                    try:
                        with open(claims_file, 'w') as f:
                            json.dump(all_claims, f, indent=2)
                    except:
                        pass
                    
                except discord.Forbidden:
                    failed_sends.append(f"User {user_id} (DMs disabled)")
                except discord.NotFound:
                    failed_sends.append(f"User {user_id} (not found)")
                except Exception as e:
                    failed_sends.append(f"User {user_id} ({str(e)})")
            
            # Report results
            result_message = f"Bulk delivery completed for {self.filename}:\n"
            result_message += f"✅ Successful: {len(successful_sends)} users\n"
            result_message += f"❌ Failed: {len(failed_sends)} users"
            
            if successful_sends:
                result_message += f"\n\nSuccessful deliveries: {', '.join(successful_sends[:10])}"
                if len(successful_sends) > 10:
                    result_message += f" (+{len(successful_sends)-10} more)"
            
            if failed_sends:
                result_message += f"\n\nFailed deliveries:\n" + '\n'.join(failed_sends[:5])
                if len(failed_sends) > 5:
                    result_message += f"\n(+{len(failed_sends)-5} more failures)"
            
            await interaction.followup.send(result_message[:2000], ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Bulk delivery failed: {str(e)}", ephemeral=True)

# Get bot token from environment
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)
    
    print(f"Starting bot with owner ID: {BOT_OWNER_ID}")
    bot.run(BOT_TOKEN)