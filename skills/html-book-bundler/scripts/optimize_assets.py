#!/usr/bin/env python3
"""
Advanced In-Place Asset Optimizer for HTML Book Bundler.
Converts images to WebP and updates references in chapter HTML files.
Requires: pip install Pillow
"""

import argparse
import sys
import re
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is required. Run: pip install Pillow")
    sys.exit(1)

def update_html_references(directory: Path, replacements: dict):
    """Scan all HTML files and update image extensions."""
    if not replacements:
        return
    
    # Sort keys by length descending to avoid partial matches (e.g. image10.jpg vs image1.jpg)
    sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
    
    for html_file in directory.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        original_content = content
        
        for old_name in sorted_keys:
            new_name = replacements[old_name]
            # Match only exact filenames in src/href/url
            # e.g. src="image.jpg" -> src="image.webp"
            content = content.replace(f'"{old_name}"', f'"{new_name}"')
            content = content.replace(f'"./{old_name}"', f'"./{new_name}"')
            content = content.replace(f"'{old_name}'", f"'{new_name}'")
            content = content.replace(f"'./{old_name}'", f"'./{new_name}'")
            # Handle url(image.jpg)
            content = content.replace(f'({old_name})', f'({new_name})')
            content = content.replace(f'(./{old_name})', f'(./{new_name})')
            
        if content != original_content:
            html_file.write_text(content, encoding="utf-8")
            print(f"  UPDATED: {html_file.name} references.")

def optimize_image(input_path: Path, max_width=1400, quality=75):
    """Convert a single image to WebP in-place."""
    try:
        output_path = input_path.with_suffix(".webp")
        with Image.open(input_path) as img:
            # 1. Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 2. Save as WebP
            img.save(output_path, "WEBP", quality=quality, method=6)
            
            orig_size = input_path.stat().st_size / 1024
            new_size = output_path.stat().st_size / 1024
            savings = (1 - new_size/orig_size) * 100
            print(f"  OPTIMIZED: {input_path.name} -> WebP ({new_size:.1f}KB, -{savings:.1f}%)")
            return output_path.name
    except Exception as e:
        print(f"  FAIL: {input_path.name}: {e}")
        return None

def main():
    p = argparse.ArgumentParser(description="In-place image optimizer for HTML bundles.")
    p.add_argument("--dir", required=True, help="Directory containing chapters and assets")
    p.add_argument("--max-width", type=int, default=1400)
    p.add_argument("--quality", type=int, default=75)
    p.add_argument("--keep", action="store_true", help="Keep original files")
    args = p.parse_args()

    root_dir = Path(args.dir)
    if not root_dir.exists():
        print(f"Error: directory not found: {root_dir}")
        sys.exit(1)

    print(f"Starting in-place optimization in: {root_dir}")
    
    # 1. Find all images (recursively in subdirectories like assets/)
    replacements = {}
    original_files = []
    
    EXTS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    
    for f in root_dir.rglob("*"):
        if f.suffix.lower() in EXTS:
            new_name = optimize_image(f, args.max_width, args.quality)
            if new_name:
                # Store relative path for replacement (e.g. assets/cover.jpg -> assets/cover.webp)
                rel_old = f.relative_to(root_dir).as_posix()
                rel_new = Path(rel_old).with_suffix(".webp").as_posix()
                replacements[rel_old] = rel_new
                original_files.append(f)

    # 2. Update HTML files
    if replacements:
        print("Updating HTML references...")
        update_html_references(root_dir, replacements)

    # 3. Clean up
    if not args.keep:
        print("Cleaning up original files...")
        for f in original_files:
            try:
                f.unlink()
            except Exception:
                pass

    print("\nOptimization complete.")

if __name__ == "__main__":
    main()
