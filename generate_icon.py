#!/usr/bin/env python3
"""
Lending Pro Freeware — macOS App Icon Generator
Generates icon.icns from a programmatic design using Pillow.
Run once before building with PyInstaller.
"""
import os
import struct
import zlib

def create_png_bytes(size, bg_color, label):
    """Create a simple PNG icon using only stdlib (no Pillow needed)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGBA', (size, size), bg_color)
        draw = ImageDraw.Draw(img)
        # Draw rounded rectangle background (gradient-like)
        margin = size // 10
        draw.rounded_rectangle([margin, margin, size-margin, size-margin],
                               radius=size//5, fill=(37, 99, 235))
        # Draw "₱" symbol
        try:
            font_size = size // 2
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) // 2 - bbox[0]
        y = (size - text_h) // 2 - bbox[1]
        draw.text((x, y), label, font=font, fill='white')
        import io
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()
    except ImportError:
        return None

def generate_icns():
    """Generate a macOS .icns file for Lending Pro Freeware."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    iconset_dir = os.path.join(script_dir, 'AppIcon.iconset')
    icns_path = os.path.join(script_dir, 'icon.icns')

    try:
        from PIL import Image, ImageDraw, ImageFont
        os.makedirs(iconset_dir, exist_ok=True)

        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Navy blue gradient background (rounded rect)
            margin = size // 10
            r = size // 5
            draw.rounded_rectangle([margin, margin, size-margin, size-margin],
                                   radius=r, fill=(30, 78, 178))
            # Lighter blue overlay for depth
            draw.rounded_rectangle([margin+2, margin+2, size-margin-2, size//2+margin//2],
                                   radius=r, fill=(59, 130, 246, 100))
            # Draw ₱ symbol
            label = '₱'
            try:
                font_size = int(size * 0.52)
                font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)
            except:
                font = None

            if font:
                bbox = draw.textbbox((0, 0), label, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = (size - tw) // 2 - bbox[0]
                y = (size - th) // 2 - bbox[1]
                # Shadow
                draw.text((x+size//40, y+size//40), label, font=font, fill=(0, 0, 0, 60))
                draw.text((x, y), label, font=font, fill='white')

            # Save 1x
            fname = f'icon_{size}x{size}.png'
            img.save(os.path.join(iconset_dir, fname))
            if size <= 512:
                # Save 2x (retina) of half size
                fname2 = f'icon_{size//2}x{size//2}@2x.png'
                img.save(os.path.join(iconset_dir, fname2))

        # Convert using iconutil
        ret = os.system(f'iconutil -c icns "{iconset_dir}" -o "{icns_path}"')
        if ret == 0:
            print(f'✅ Icon generated: {icns_path}')
            import shutil
            shutil.rmtree(iconset_dir, ignore_errors=True)
        else:
            print(f'⚠️  iconutil failed. Iconset saved at: {iconset_dir}')

    except ImportError:
        print('⚠️  Pillow not installed. Trying to install...')
        os.system('pip install Pillow')
        print('Re-run this script after installation.')

if __name__ == '__main__':
    generate_icns()
