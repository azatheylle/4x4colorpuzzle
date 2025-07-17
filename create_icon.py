"""
Simple Icon Creator for 4x4 Color Puzzle
Creates a basic icon using Python PIL (if available) or instructions for manual creation
"""

def create_simple_icon():
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 64x64 icon
        size = 64
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))  # Transparent background
        draw = ImageDraw.Draw(img)
        
        # Draw a simple 2x2 grid representing the 4x4 puzzle
        colors = [
            (255, 255, 0, 255),    # Yellow
            (0, 0, 255, 255),      # Blue  
            (255, 0, 0, 255),      # Red
            (0, 255, 0, 255),      # Green
        ]
        
        # Draw colored squares in corners
        square_size = size // 3
        positions = [
            (5, 5),                           # Top-left (Yellow)
            (size - square_size - 5, 5),     # Top-right (Blue)
            (5, size - square_size - 5),     # Bottom-left (Red)
            (size - square_size - 5, size - square_size - 5)  # Bottom-right (Green)
        ]
        
        for i, (color, pos) in enumerate(zip(colors, positions)):
            x, y = pos
            draw.rectangle([x, y, x + square_size, y + square_size], fill=color, outline=(0, 0, 0, 255))
        
        # Draw "4x4" text in center
        try:
            # Try to use a reasonable font
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        text = "4x4"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2
        
        # Draw text with outline for visibility
        draw.text((text_x-1, text_y-1), text, font=font, fill=(255, 255, 255, 255))
        draw.text((text_x+1, text_y-1), text, font=font, fill=(255, 255, 255, 255))
        draw.text((text_x-1, text_y+1), text, font=font, fill=(255, 255, 255, 255))
        draw.text((text_x+1, text_y+1), text, font=font, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))
        
        # Save as PNG first
        img.save('icon.png')
        print("✅ Created icon.png")
        
        # Try to save as ICO
        try:
            # Create multiple sizes for the ICO
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            images = []
            for ico_size in sizes:
                resized = img.resize(ico_size, Image.Resampling.LANCZOS)
                images.append(resized)
            
            images[0].save('icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
            print("✅ Created icon.ico")
            
        except Exception as e:
            print(f"⚠️  Could not create ICO file: {e}")
            print("You can convert icon.png to ICO using online converters")
        
        return True
        
    except ImportError:
        print("❌ PIL/Pillow not installed")
        return False

def print_manual_instructions():
    print("\n📝 MANUAL ICON CREATION INSTRUCTIONS:")
    print("1. Create a 64x64 pixel image")
    print("2. Use these colors in corners:")
    print("   • Top-left: Yellow square")
    print("   • Top-right: Blue square") 
    print("   • Bottom-left: Red square")
    print("   • Bottom-right: Green square")
    print("3. Add '4x4' text in the center")
    print("4. Save as 'icon.png'")
    print("5. Convert to 'icon.ico' using:")
    print("   - https://convertio.co/png-ico/")
    print("   - https://www.icoconverter.com/")
    print("   - Or any online PNG to ICO converter")

if __name__ == "__main__":
    print("🎨 4x4 Color Puzzle Icon Creator")
    print("=" * 40)
    
    success = create_simple_icon()
    
    if not success:
        print_manual_instructions()
    
    print("\n🔧 NEXT STEPS:")
    print("1. Place icon.ico in your project folder")
    print("2. Rebuild your executable with: build_exe.bat")
    print("3. Your game will now have a custom icon!")
