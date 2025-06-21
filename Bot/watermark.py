import os
import uuid
import json
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from datetime import datetime
import asyncio
from typing import Dict, Optional

class WatermarkProcessor:
    def __init__(self):
        self.processed_files_db = "data/processed_files.json"
        self.output_dir = "output"
        self.ensure_directories()
        self.load_processed_files()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
    
    def load_processed_files(self):
        """Load processed files database"""
        try:
            if os.path.exists(self.processed_files_db):
                with open(self.processed_files_db, 'r') as f:
                    self.processed_files = json.load(f)
            else:
                self.processed_files = {}
        except Exception as e:
            print(f"Error loading processed files database: {e}")
            self.processed_files = {}
    
    def save_processed_files(self):
        """Save processed files database"""
        try:
            with open(self.processed_files_db, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            print(f"Error saving processed files database: {e}")
    
    def generate_watermark_id(self) -> str:
        """Generate a unique watermark ID"""
        # Format: ES-##### (5-7 random numbers)
        import random
        num_digits = random.randint(5, 7)
        random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(num_digits)])
        return f"ES-{random_numbers}"
    
    async def process_file(self, file_path: str, description: str) -> Dict:
        """Process a file with watermark"""
        try:
            watermark_id = self.generate_watermark_id()
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Determine file type and process accordingly
            if file_extension in ['.jpg', '.jpeg', '.png']:
                result = await self.process_image(file_path, watermark_id, description)
            elif file_extension in ['.mp4', '.mov', '.avi']:
                result = await self.process_video(file_path, watermark_id, description)
            else:
                return {'status': 'error', 'error': 'Unsupported file format'}
            
            if result['success']:
                # Store in database
                self.processed_files[watermark_id] = {
                    'original_filename': os.path.basename(file_path),
                    'processed_filename': result.get('processed_filename', ''),
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'file_type': file_extension,
                    'watermark_id': watermark_id
                }
                self.save_processed_files()
                
                return {
                    'status': 'success',
                    'watermark_id': watermark_id,
                    'processed_filename': result.get('processed_filename', '')
                }
            else:
                return result
                
        except Exception as e:
            print(f"Error processing file: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def process_image(self, image_path: str, watermark_id: str, description: str) -> Dict:
        """Process an image with watermark"""
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a transparent overlay
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Calculate watermark position and size
                width, height = img.size
                
                # Try to load a font, fall back to default if not available
                try:
                    # Use corner watermark size as default - massive text
                    font_size = max(300, min(width, height) // 2)  # Massive default size
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                
                # Add main watermark ID
                watermark_text = watermark_id
                if font:
                    text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                else:
                    text_width = len(watermark_text) * 10
                    text_height = 15
                
                # Position: bottom-right corner with padding
                x = width - text_width - 20
                y = height - text_height - 20
                
                # Draw text background - maximum visibility
                bg_padding = 30
                draw.rectangle(
                    [x - bg_padding, y - bg_padding, x + text_width + bg_padding, y + text_height + bg_padding],
                    fill=(0, 0, 0, 200)  # Almost black background
                )
                
                # Draw watermark text - bright white and massive
                draw.text((x, y), watermark_text, fill=(255, 255, 255, 255), font=font)  # Pure white text
                
                # Corner watermarks same size as main watermark
                corner_font_size = font_size  # Same massive size
                try:
                    corner_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", corner_font_size)
                except:
                    corner_font = font
                
                # Create continuous watermark pattern across entire image
                
                # Pattern watermarks same size as main watermark
                pattern_font_size = font_size  # Same massive size
                try:
                    pattern_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", pattern_font_size)
                except:
                    pattern_font = font
                
                # Get text dimensions
                pattern_bbox = draw.textbbox((0, 0), watermark_id, font=pattern_font)
                pattern_width = pattern_bbox[2] - pattern_bbox[0]
                pattern_height = pattern_bbox[3] - pattern_bbox[1]
                
                # Add more spacing between watermarks to prevent text overlap
                spacing = 20
                
                # Calculate how many watermarks fit horizontally
                watermarks_per_row = (width + spacing) // (pattern_width + spacing)
                
                # Calculate how many rows we need to cover the image
                rows_needed = (height + spacing) // (pattern_height + spacing) + 1
                
                # Create continuous pattern with commas - much more visible
                for row in range(rows_needed):
                    y_pos = row * (pattern_height + spacing)
                    
                    # Create a continuous line of watermarks with commas
                    x_pos = 0
                    for col in range(watermarks_per_row + 2):  # Extra watermarks to ensure full coverage
                        if x_pos < width:
                            # Draw watermark with higher opacity for visibility
                            draw.text((x_pos, y_pos), watermark_id, fill=(255, 255, 255, 60), font=pattern_font)  # More visible
                            x_pos += pattern_width + spacing  # Add spacing to prevent overlap
                
                # Add much more prominent watermark in corners for visibility
                corner_font_size = max(35, min(width, height) // 20)  # Much larger corners
                try:
                    corner_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", corner_font_size)
                except:
                    corner_font = pattern_font
                
                corner_bbox = draw.textbbox((0, 0), watermark_id, font=corner_font)
                corner_width = corner_bbox[2] - corner_bbox[0]
                corner_height = corner_bbox[3] - corner_bbox[1]
                
                # Four corners with backgrounds for maximum visibility and no overlap
                corner_padding = 15
                
                # Top-left corner with background
                draw.rectangle([5, 5, corner_width + 25, corner_height + 25], fill=(0, 0, 0, 160))
                draw.text((15, 15), watermark_id, fill=(255, 255, 255, 255), font=corner_font)
                
                # Top-right corner with background
                draw.rectangle([width - corner_width - 25, 5, width - 5, corner_height + 25], fill=(0, 0, 0, 160))
                draw.text((width - corner_width - 15, 15), watermark_id, fill=(255, 255, 255, 255), font=corner_font)
                
                # Bottom-left corner with background
                draw.rectangle([5, height - corner_height - 25, corner_width + 25, height - 5], fill=(0, 0, 0, 160))
                draw.text((15, height - corner_height - 15), watermark_id, fill=(255, 255, 255, 255), font=corner_font)
                
                # Bottom-right corner with background
                draw.rectangle([width - corner_width - 25, height - corner_height - 25, width - 5, height - 5], fill=(0, 0, 0, 160))
                draw.text((width - corner_width - 15, height - corner_height - 15), watermark_id, fill=(255, 255, 255, 255), font=corner_font)
                
                # Center watermark same size as main watermark
                center_font_size = font_size  # Same massive size
                try:
                    center_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", center_font_size)
                except:
                    center_font = corner_font
                
                center_bbox = draw.textbbox((0, 0), watermark_id, font=center_font)
                center_width = center_bbox[2] - center_bbox[0]
                center_height = center_bbox[3] - center_bbox[1]
                center_x = (width - center_width) // 2
                center_y = (height - center_height) // 2
                
                # Large background for center watermark
                bg_padding = 30
                draw.rectangle(
                    [center_x - bg_padding, center_y - bg_padding, center_x + center_width + bg_padding, center_y + center_height + bg_padding],
                    fill=(0, 0, 0, 140)
                )
                
                # Center watermark with high opacity for maximum visibility
                draw.text((center_x, center_y), watermark_id, fill=(255, 255, 255, 255), font=center_font)
                
                # Composite the overlay onto the original image
                watermarked = Image.alpha_composite(img, overlay)
                
                # Save the watermarked image
                output_filename = f"{watermark_id}_{os.path.basename(image_path)}"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Check original file format to preserve transparency
                original_format = Image.open(image_path).format
                file_extension = os.path.splitext(image_path)[1].lower()
                
                if file_extension == '.png' and original_format == 'PNG':
                    # Keep PNG format with transparency
                    watermarked.save(output_path, 'PNG', optimize=True)
                else:
                    # Convert to RGB for JPEG
                    if watermarked.mode == 'RGBA':
                        rgb_img = Image.new('RGB', watermarked.size, (255, 255, 255))
                        rgb_img.paste(watermarked, mask=watermarked.split()[-1])
                        watermarked = rgb_img
                    
                    # Change extension to .jpg for non-PNG files
                    base_name = os.path.splitext(output_filename)[0]
                    output_filename = f"{base_name}.jpg"
                    output_path = os.path.join(self.output_dir, output_filename)
                    watermarked.save(output_path, 'JPEG', quality=95, optimize=True)
                
                return {'success': True, 'processed_filename': output_filename}
                
        except Exception as e:
            print(f"Error processing image: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_path: str, watermark_id: str, description: str) -> Dict:
        """Process a video with watermark"""
        try:
            output_filename = f"{watermark_id}_{os.path.basename(video_path)}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Define codec and create VideoWriter with better compatibility
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Calculate text properties - massive size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(12.0, min(width, height) / 50)  # Massive font scale
            thickness = max(20, int(font_scale * 10))  # Very thick text
            
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add watermarks to frame
                # Bottom-right watermark
                text_size = cv2.getTextSize(watermark_id, font, font_scale, thickness)[0]
                x = width - text_size[0] - 20
                y = height - 20
                
                # Add background rectangle
                cv2.rectangle(frame, (x - 10, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
                cv2.putText(frame, watermark_id, (x, y), font, font_scale, (255, 255, 255), thickness)
                
                # Top-left watermark
                cv2.putText(frame, watermark_id, (10, 30), font, font_scale * 0.7, (255, 255, 255), max(1, thickness - 1))
                
                # Top-right watermark
                top_right_x = width - text_size[0] - 10
                cv2.putText(frame, watermark_id, (top_right_x, 30), font, font_scale * 0.7, (255, 255, 255), max(1, thickness - 1))
                
                # Center watermark (every 20 frames for more frequent visibility)
                if frame_count % 20 == 0:
                    center_text = f"{watermark_id}"
                    center_size = cv2.getTextSize(center_text, font, font_scale * 2.0, thickness + 2)[0]  # Much larger center
                    center_x = (width - center_size[0]) // 2
                    center_y = (height + center_size[1]) // 2
                    
                    # More prominent background
                    center_overlay = frame.copy()
                    cv2.rectangle(center_overlay, (center_x - 30, center_y - 50), (center_x + center_size[0] + 30, center_y + 30), (0, 0, 0), -1)
                    cv2.addWeighted(center_overlay, 0.6, frame, 0.4, 0, frame)  # More visible background
                    cv2.putText(frame, center_text, (center_x, center_y), font, font_scale * 2.0, (255, 255, 255), thickness + 2)
                
                # Create overlay for transparent watermarks covering entire screen
                overlay = frame.copy()
                
                # Grid pattern with proper spacing to avoid text overlap
                grid_rows = 8   # Fewer rows to prevent overlap
                grid_cols = 10  # Fewer columns to prevent overlap
                
                for row in range(grid_rows):
                    for col in range(grid_cols):
                        # Calculate position for each watermark
                        x_pos = (col * width) // grid_cols + (width // grid_cols // 2)
                        y_pos = (row * height) // grid_rows + (height // grid_rows // 2)
                        
                        # Massive, highly visible watermarks in grid
                        if (row + col) % 3 == 0:
                            scale = font_scale * 1.5  # Massive
                        elif (row + col) % 3 == 1:
                            scale = font_scale * 1.3  # Very large
                        else:
                            scale = font_scale * 1.4  # Very large
                        
                        # Add watermark to overlay with higher thickness
                        cv2.putText(overlay, watermark_id, (x_pos, y_pos), font, scale, (255, 255, 255), max(2, thickness))
                
                # Much larger corner watermarks for maximum visibility
                corner_scale = font_scale * 1.2  # Much larger corners
                text_size = cv2.getTextSize(watermark_id, font, corner_scale, thickness + 1)[0]
                
                cv2.putText(overlay, watermark_id, (15, 35), font, corner_scale, (255, 255, 255), thickness + 1)
                cv2.putText(overlay, watermark_id, (width - text_size[0] - 15, 35), font, corner_scale, (255, 255, 255), thickness + 1)
                cv2.putText(overlay, watermark_id, (15, height - 15), font, corner_scale, (255, 255, 255), thickness + 1)
                cv2.putText(overlay, watermark_id, (width - text_size[0] - 15, height - 15), font, corner_scale, (255, 255, 255), thickness + 1)
                
                # Edge watermarks for extra coverage - larger and more frequent
                edge_scale = font_scale * 0.7  # Much larger edge watermarks
                edge_spacing = 60  # Closer spacing for more coverage
                
                # Top and bottom edges
                for x in range(edge_spacing, width - edge_spacing, edge_spacing):
                    cv2.putText(overlay, watermark_id, (x, 25), font, edge_scale, (255, 255, 255), max(2, thickness-1))
                    cv2.putText(overlay, watermark_id, (x, height - 15), font, edge_scale, (255, 255, 255), max(2, thickness-1))
                
                # Left and right edges
                for y in range(edge_spacing, height - edge_spacing, edge_spacing):
                    cv2.putText(overlay, watermark_id, (10, y), font, edge_scale, (255, 255, 255), 1)
                    edge_text_size = cv2.getTextSize(watermark_id, font, edge_scale, 1)[0]
                    cv2.putText(overlay, watermark_id, (width - edge_text_size[0] - 10, y), font, edge_scale, (255, 255, 255), 1)
                
                # Apply overlay with 0.6 transparency
                cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                
                out.write(frame)
                frame_count += 1
            
            # Release everything
            cap.release()
            out.release()
            
            return {'success': True, 'processed_filename': output_filename}
            
        except Exception as e:
            print(f"Error processing video: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_processed_file(self, watermark_id: str) -> Optional[Dict]:
        """Get processed file information by watermark ID"""
        return self.processed_files.get(watermark_id)
    
    def get_all_processed_files(self) -> Dict:
        """Get all processed files"""
        return self.processed_files.copy()
