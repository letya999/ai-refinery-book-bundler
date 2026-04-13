#!/usr/bin/env python3
"""
Advanced Asset Optimizer for HTML Book Bundler.
Uses WebP for maximum compression and transparency preservation.
Requires: pip install Pillow
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is required. Run: pip install Pillow")
    sys.exit(1)

def optimize_image(input_path, output_path, max_width=1400, quality=75):
    try:
        with Image.open(input_path) as img:
            # 1. Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 2. Determine format and transparency
            has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
            
            # 3. Save as WebP (Lossy for photos, Lossless-ish for graphics)
            # WebP is much lighter in Base64 than PNG/JPG
            img.save(output_path, "WEBP", quality=quality, method=6)
            
            orig_size = input_path.stat().st_size / 1024
            new_size = output_path.stat().st_size / 1024
            savings = (1 - new_size/orig_size) * 100
            print(f"DONE: {input_path.name} -> WebP ({new_size:.1f}KB, -{savings:.1f}%)")
            return True
    except Exception as e:
        print(f"FAIL: {input_path.name}: {e}")
        return False

def main():
    p = argparse.ArgumentParser(description="Optimize images to WebP for bundle.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--max-width", type=int, default=1400)
    p.add_argument("--quality", type=int, default=75)
    args = p.parse_args()

    in_dir, out_dir = Path(args.input), Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in in_dir.iterdir():
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.tiff']:
            # All optimized assets become .webp for consistent bundling
            out_f = out_dir / (f.stem + '.webp')
            if optimize_image(f, out_f, args.max_width, args.quality):
                count += 1
    print(f"\nOptimization complete. {count} images processed.")

if __name__ == "__main__":
    main()
