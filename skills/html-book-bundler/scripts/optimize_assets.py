#!/usr/bin/env python3
"""
Asset Optimizer for HTML Book Bundler
Provides automated compression for images to reduce bundle size.
Requires 'Pillow' library. Run: pip install Pillow
"""

import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is required for image optimization.")
    print("Please install it using: pip install Pillow")
    exit(1)

def optimize_image(input_path, output_path, max_width=1200, quality=80):
    try:
        with Image.open(input_path) as img:
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to webp/jpeg for better compression if it's not already
            if img.format not in ['JPEG', 'WEBP']:
                img = img.convert("RGB")
                
            # Save optimized
            img.save(output_path, optimize=True, quality=quality)
            
            orig_size = input_path.stat().st_size / 1024
            new_size = output_path.stat().st_size / 1024
            savings = (1 - new_size/orig_size) * 100
            
            print(f"Optimized: {input_path.name} -> {new_size:.1f}KB (Saved {savings:.1f}%)")
    except Exception as e:
        print(f"Failed to optimize {input_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Optimize image assets for bundle.")
    parser.add_argument("--input", required=True, help="Directory containing raw images")
    parser.add_argument("--output", required=True, help="Directory to save optimized images")
    parser.add_argument("--max-width", type=int, default=1200, help="Maximum image width")
    parser.add_argument("--quality", type=int, default=80, help="Image quality (1-100)")
    args = parser.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for file in in_dir.iterdir():
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            # Force output to .jpg for simplicity and broad compatibility
            out_file = out_dir / (file.stem + '.jpg')
            optimize_image(file, out_file, args.max_width, args.quality)

if __name__ == "__main__":
    main()
