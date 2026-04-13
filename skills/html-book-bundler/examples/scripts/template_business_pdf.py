#!/usr/bin/env python3
"""
TEMPLATE: Business/Technical PDF Converter
Based on: Иван Селиховкин "Управление ИТ-проектами по-простому"

Use this for books with:
- Stats, Timelines, Grids
- Systematic chapter layouts (Chapter I, II...)
- Running headers (author name, website)
"""

import fitz
import re
import os
import html as html_lib
from pathlib import Path

# --- CONFIGURATION ---
PDF_PATH  = "book.pdf"
OUT_DIR   = "chapters"

# Map chapter titles to page ranges (start, end)
CHAPTERS = [
    ("Intro", 5, 5),
    ("Chapter I. Key Concepts", 6, 10),
    # ... add more
]

# Map chapter index to rich visual blocks
CHAPTER_VISUALS = {
    1: { "type": "stats", "items": [("A", "Detail 1"), ("B", "Detail 2")] },
    2: { "type": "timeline", "steps": ["Step 1", "Step 2", "Step 3"] },
}

# --- REGEX FOR CLEANUP ---
# Patterns to ignore (headers, footers, page numbers)
IGNORE_PATTERNS = [
    re.compile(r'^Author\s+Name.*$', re.I),
    re.compile(r'^\d{1,3}$'), # Page numbers
    re.compile(r'www\.site\.com', re.I)
]

def is_ignored(text: str) -> bool:
    for p in IGNORE_PATTERNS:
        if p.match(text): return True
    return False

def extract_page_blocks(doc: fitz.Document, page_num: int) -> list[dict]:
    page = doc[page_num - 1]
    raw = page.get_text("dict")
    blocks = []
    for b in raw.get("blocks", []):
        if b.get("type") != 0: continue
        lines_text = []
        max_size = 0
        is_bold = False
        for line in b.get("lines", []):
            line_parts = []
            for span in line.get("spans", []):
                t = span["text"]
                if not t.strip(): continue
                size, flags = span["size"], span["flags"]
                bold = bool(flags & (1 << 4))
                max_size = max(max_size, size)
                if bold: is_bold = True
                line_parts.append((t, bold, size))
            if line_parts: lines_text.append(line_parts)
        if not lines_text: continue
        plain = " ".join(part[0] for line in lines_text for part in line).strip()
        if is_ignored(plain) and len(plain) < 100: continue
        blocks.append({"lines": lines_text, "plain": plain, "size": max_size, "bold": is_bold})
    return blocks

# ... (rest of the logic: blocks_to_html, build_chapter_html)
# Refer to the original convert_pm_book.py for full implementation details.
