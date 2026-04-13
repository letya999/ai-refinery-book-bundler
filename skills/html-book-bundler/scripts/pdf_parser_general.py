#!/usr/bin/env python3
"""
General PDF to Structured HTML Parser (v1.0)
Part of html-book-bundler skill.

This script uses PyMuPDF (fitz) to extract text with style information.
It is designed to be a base for book-specific converters.

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
        # Default ignores: page numbers
        if re.match(r'^\d{1,3}$', text): return True
        for pattern in self.ignore_patterns:
            if pattern.match(text): return True
        return False

    def extract_blocks(self, page_num: int) -> List[Dict[str, Any]]:
        """Extract text blocks with font size and bold flag."""
        page = self.doc[page_num - 1]
        raw = page.get_text("dict")
        blocks = []
        for b in raw.get("blocks", []):
            if b.get("type") != 0: continue # Skip images
            
            lines_data = []
            max_size = 0
            is_bold = False
            
            for line in b.get("lines", []):
                line_parts = []
                for span in line.get("spans", []):
                    text = span["text"]
                    if not text.strip(): continue
                    
                    size = span["size"]
                    flags = span["flags"]
                    bold = bool(flags & (1 << 4))
                    
                    max_size = max(max_size, size)
                    if bold: is_bold = True
                    line_parts.append({"text": text, "bold": bold, "size": size})
                
                if line_parts:
                    lines_data.append(line_parts)
            
            if not lines_data: continue
            
            plain = " ".join(p["text"] for line in lines_data for p in line).strip()
            if self.is_ignored(plain): continue
            
            blocks.append({
                "plain": plain,
                "size": max_size,
                "bold": is_bold,
                "lines": lines_data
            })
        return blocks

    def blocks_to_html(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert style-aware blocks to basic HTML tags."""
        html_parts = []
        for b in blocks:
            size, plain, lines = b["size"], b["plain"], b["lines"]
            
            # Heuristic for tags based on size (can be overridden in config)
            if size >= 18: tag = "h1"
            elif size >= 14: tag = "h2"
            elif size >= 12 or (b["bold"] and size >= 11): tag = "h3"
            else: tag = "p"
            
            # Format inline styles
            content_parts = []
            for line in lines:
                for span in line:
                    txt = html_lib.escape(span["text"])
                    if span["bold"] and tag == "p":
                        content_parts.append(f"<b>{txt}</b>")
                    else:
                        content_parts.append(txt)
                content_parts.append(" ")
            
            content = "".join(content_parts).strip()
            if content:
                html_parts.append(f"<{tag}>{content}</{tag}>")
        
        return "\n".join(html_parts)

    def clean_ocr(self, text: str) -> str:
        """Standard OCR cleanup: soft hyphens, multiple spaces."""
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text) # Join hyphenated words
        text = re.sub(r'[ \t]+', ' ', text) # Collapse horizontal whitespace
        return text

    def run(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        if not self.chapters_meta:
            print("No chapters defined in config. Extracting whole book as one file.")
            self.chapters_meta = [("Full Book", 1, len(self.doc))]

        for idx, ch in enumerate(self.chapters_meta, 1):
            title = ch[0]
            start_p = ch[1]
            end_p = ch[2]
            
            print(f"Processing Chapter {idx}: {title} (pages {start_p}-{end_p})...")
            
            chapter_blocks = []
            for p_num in range(start_p, end_p + 1):
                chapter_blocks.extend(self.extract_blocks(p_num))
            
            body_html = self.blocks_to_html(chapter_blocks)
            
            # Basic template
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
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(full_html)

def main():
    parser = argparse.ArgumentParser(description="General PDF to HTML converter")
    parser.add_argument("--input", required=True, help="Input PDF file")
    parser.add_argument("--output", default="./chapters", help="Output directory")
    parser.add_argument("--config", help="JSON config file with chapter ranges and ignores")
    
    args = parser.parse_args()
    
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    # Example config structure if file is missing
    # {
    #   "ignore": ["Book Title", "Author Name"],
    #   "chapters": [ ["Intro", 1, 5], ["Chapter 1", 6, 20] ]
    # }

    processor = PDFParser(args.input, config)
    processor.run(args.output)
    print(f"Done! Chapters saved to {args.output}")

if __name__ == "__main__":
    main()
