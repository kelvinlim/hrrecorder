#!/usr/bin/env python3
"""
Convert macOS .icns file to Windows .ico file
"""
from PIL import Image
import os

def convert_icns_to_ico(icns_path, ico_path):
    """Convert .icns to .ico format"""
    try:
        # Try to open the icns file
        img = Image.open(icns_path)
        
        # Get the largest size available
        print(f"Original image size: {img.size}")
        
        # Create multiple sizes for Windows .ico (256, 128, 64, 48, 32, 16)
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        
        # Save as .ico with multiple resolutions
        img.save(ico_path, format='ICO', sizes=sizes)
        print(f"Successfully created {ico_path}")
        print(f"Icon contains sizes: {sizes}")
        
    except Exception as e:
        print(f"Error converting icon: {e}")
        print("\nTrying alternative method...")
        
        # Alternative: Read icns and extract PNG data
        try:
            # Some .icns files need special handling
            # Try extracting as PNG first
            with Image.open(icns_path) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize to standard sizes and save
                img.save(ico_path, format='ICO', sizes=sizes)
                print(f"Successfully created {ico_path} using alternative method")
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")
            return False
    
    return True

if __name__ == "__main__":
    icns_file = "hrrecorder.icns"
    ico_file = "hrrecorder.ico"
    
    if not os.path.exists(icns_file):
        print(f"Error: {icns_file} not found!")
        exit(1)
    
    success = convert_icns_to_ico(icns_file, ico_file)
    
    if success and os.path.exists(ico_file):
        size = os.path.getsize(ico_file)
        print(f"\nSuccess! Created {ico_file} ({size} bytes)")
    else:
        print("\nFailed to create .ico file")
        exit(1)
