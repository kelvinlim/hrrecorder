import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

def create_icon_image(size):
    # Create a new image with a transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a rounded square (squircle-ish) background
    # Color: Medical Blue/Teal or Dark Grey? Let's go with a nice dark grey background
    # so the red heart pops. Actually specs said "Red Heart design".
    # Let's do a Red Rounded Square for the container, like many macOS apps.
    
    padding = size * 0.1
    rect = [padding, padding, size - padding, size - padding]
    corner_radius = size * 0.2
    
    # Gradient-ish fill? For simplicity, solid color for now: #FF3B30 (Apple Red)
    draw.rounded_rectangle(rect, radius=corner_radius, fill="#FF3B30")
    
    # Draw a White Heart in the center
    # Heart shape params
    # We can draw a heart using bezier curves or polygon
    # Simple heart shape
    
    center_x = size / 2
    center_y = size / 2
    heart_size = size * 0.5
    
    # Heart path points (approximate)
    # Top left hump, top right hump, bottom tip
    # We'll use a path for better quality
    
    # Simplified heart math or drawing two circles and a triangle?
    # Let's draw a white ECG line instead on the red background? 
    # Or a White Heart?
    # Let's do a White Heart shape.
    
    # Using a simple polygon for 'heart' is jagged. 
    # Let's use text heart if font is available? No, risky.
    # Let's draw circles and a rotated square.
    
    circle_radius = heart_size * 0.3
    # Left circle
    draw.ellipse([center_x - heart_size/2, center_y - heart_size/2, 
                  center_x - heart_size/2 + 2*circle_radius, center_y - heart_size/2 + 2*circle_radius], 
                 fill="white")
    # Right circle
    draw.ellipse([center_x + heart_size/2 - 2*circle_radius, center_y - heart_size/2, 
                  center_x + heart_size/2, center_y - heart_size/2 + 2*circle_radius], 
                 fill="white")
    # Triangle (inverted)
    triangle_h = heart_size * 0.6
    draw.polygon([
        (center_x - heart_size/2 + 3, center_y - heart_size/4 + circle_radius/1.2), # Left
        (center_x + heart_size/2 - 3, center_y - heart_size/4 + circle_radius/1.2), # Right
        (center_x, center_y + heart_size/2) # Bottom tip
    ], fill="white")

    # Add an ECG line zig-zag in Red (the background color) across the white heart?
    # Or just keep it as a simple Red Icon with White Heart. 
    # Let's add an ECG line overlay across the heart in Red.
    
    qs = heart_size / 4
    line_y = center_y 
    line_width = max(1, int(size * 0.03))
    
    points = [
        (center_x - heart_size/2, line_y),
        (center_x - qs, line_y),
        (center_x - qs/2, line_y - qs), # Up
        (center_x, line_y + qs),       # Down
        (center_x + qs/2, line_y - qs*1.5), # Big Up
        (center_x + qs, line_y),
        (center_x + heart_size/2, line_y)
    ]
    # Draw line
    draw.line(points, fill="#FF3B30", width=line_width, joint="curve")

    return img

def main():
    iconset_name = 'hrrecorder.iconset'
    if os.path.exists(iconset_name):
        shutil.rmtree(iconset_name)
    os.makedirs(iconset_name)

    # Standard macOS icon sizes
    sizes = [
        (16, 1), (16, 2),
        (32, 1), (32, 2),
        (128, 1), (128, 2),
        (256, 1), (256, 2),
        (512, 1), (512, 2)
    ]

    for points, scale in sizes:
        pixels = points * scale
        filename = f"icon_{points}x{points}"
        if scale == 2:
            filename += "@2x"
        filename += ".png"
        
        img = create_icon_image(pixels)
        img.save(os.path.join(iconset_name, filename))
        print(f"Created {filename}")

    # Convert to icns
    subprocess.run(['iconutil', '-c', 'icns', iconset_name], check=True)
    print("Created hrrecorder.icns")
    
    # Cleanup
    shutil.rmtree(iconset_name)

if __name__ == "__main__":
    main()
