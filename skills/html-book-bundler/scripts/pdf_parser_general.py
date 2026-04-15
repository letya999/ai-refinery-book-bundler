#!/usr/bin/env python3
"""
General PDF to Structured HTML Parser (v1.1)
Part of html-book-bundler skill.

This script uses PyMuPDF (fitz) to extract text with style information
and detects tables using built-in TableFinder.

Usage:
    python pdf_parser_general.py --input book.pdf --config config.json --output ./chapters
"""

import fitz
import re
import os
import json
import argparse
import html as html_lib
from pathlib import Path
from typing import List, Dict, Any, Optional

class PDFParser:
    def __init__(self, pdf_path: str, config: Dict[str, Any] = None):
        self.doc = fitz.open(pdf_path)
        self.config = config or {}
        self.chapters_meta = self.config.get("chapters", [])
        self.ignore_patterns = [re.compile(p, re.I) for p in self.config.get("ignore", [])]
        
    def is_ignored(self, text: str) -> bool:
        text = text.strip()
        if not text: return True
        if re.match(r'^\d{1,3}$', text): return True
        for pattern in self.ignore_patterns:
            if pattern.match(text): return True
        return False

    def extract_page_content(self, page_num: int) -> str:
        """Extract text blocks and tables from a page."""
        page = self.doc[page_num - 1]
        
        # 1. Find tables
        tables = []
        try:
            tabs = page.find_tables()
            for t in tabs:
                html_table = "<table>\n"
                for row in t.extract():
                    html_table += "  <tr>"
                    for cell in row:
                        val = html_lib.escape(str(cell or ""))
                        html_table += f"<td>{val}</td>"
                    html_table += "</tr>\n"
                html_table += "</table>"
                
                tables.append({
                    "bbox": t.bbox,
                    "html": f"\n<!-- TABLE_START -->\n{html_table}\n<!-- TABLE_END -->\n"
                })
        except Exception as e:
            print(f"  Warning: table detection failed on p.{page_num}: {e}")

        # 2. Extract text blocks
        raw = page.get_text("dict")
        page_items = []
        
        for b in raw.get("blocks", []):
            if b.get("type") != 0: continue
            
            # Check if block overlaps with any table
            block_bbox = b["bbox"]
            is_inside_table = False
            for t in tables:
                # If block center is inside table bbox, skip it
                cx = (block_bbox[0] + block_bbox[2]) / 2
                cy = (block_bbox[1] + block_bbox[3]) / 2
                tx0, ty0, tx1, ty1 = t["bbox"]
                if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                    is_inside_table = True
                    break
            
            if is_inside_table: continue

            max_size = 0
            is_bold = False
            content_parts = []
            
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    txt = span["text"]
                    if not txt.strip(): continue
                    
                    size = span["size"]
                    flags = span["flags"]
                    bold = bool(flags & (1 << 4))
                    
                    max_size = max(max_size, size)
                    if bold: is_bold = True
                    
                    escaped = html_lib.escape(txt)
                    content_parts.append(f"<b>{escaped}</b>" if bold else escaped)
                content_parts.append(" ")

            plain = "".join(content_parts).strip()
            if not plain or self.is_ignored(re.sub(r'<[^>]+>', '', plain)): continue

            # Heuristic for tag
            if max_size >= 18: tag = "h1"
            elif max_size >= 14: tag = "h2"
            elif max_size >= 12 or (is_bold and max_size >= 11): tag = "h3"
            else: tag = "p"
            
            page_items.append({
                "y": block_bbox[1],
                "html": f"<{tag}>{plain}</{tag}>"
            })

        # 3. Add tables to items
        for t in tables:
            page_items.append({
                "y": t["bbox"][1],
                "html": t["html"]
            })

        # Sort by vertical position
        page_items.sort(key=lambda x: x["y"])
        return "\n".join(item["html"] for item in page_items)

    def run(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        if not self.chapters_meta:
            print("No chapters defined in config. Extracting whole book as one file.")
            self.chapters_meta = [("Full Book", 1, len(self.doc))]

        for idx, ch in enumerate(self.chapters_meta, 1):
            title, start_p, end_p = ch[0], ch[1], ch[2]
            print(f"Processing Chapter {idx}: {title} (pages {start_p}-{end_p})...")
            
            chapter_html = []
            for p_num in range(start_p, end_p + 1):
                chapter_html.append(self.extract_page_content(p_num))
            
            body_html = "\n".join(chapter_html)
            
            full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body>
<section class="hero">
  <h1>{title}</h1>
</section>
<div class="content-body">
{body_html}
</div>
</body>
</html>"""
            
            out_file = Path(output_dir) / f"chapter{idx}.html"
            out_file.write_text(full_html, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Style-aware PDF to HTML with Table detection")
    parser.add_argument("--input", required=True, help="Input PDF file")
    parser.add_argument("--output", default="./chapters", help="Output directory")
    parser.add_argument("--config", help="JSON config file")
    args = parser.parse_args()
    
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)

    processor = PDFParser(args.input, config)
    processor.run(args.output)
    print(f"Done! Chapters saved to {args.output}")

if __name__ == "__main__":
    main()
