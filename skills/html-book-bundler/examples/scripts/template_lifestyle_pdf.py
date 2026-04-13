#!/usr/bin/env python3
"""
TEMPLATE: Lifestyle/Narrative PDF Converter
Based on: "He's Just Not That Into You" (Грег Берендт)

Use this for books with:
- Red flags, checklists, truth scales
- Q&A sections (Letters to Author, Stories)
- Heavy classification (Myths vs Reality)
"""

import json
import re
import os
import html as html_lib

# --- CONFIGURATION ---
PAGES_JSON = "book_text_raw.json"
OUT_DIR    = "chapters"

# Signal strength (alarm level)
_SIGNAL = {1:1, 2:4, 3:3, 4:5, 5:5, 6:3, 7:5, 8:5, 9:5, 10:4, 11:1}

# Insights pullquotes
CHAPTER_INSIGHTS = {
    1: ['Key Insight #1', 'Key Insight #2'],
    # ...
}

# Rich visual configurations
CHAPTER_VISUALS = {
    1: { 'type': 'red_flags', 'title': 'Red Flags', 'items': ['Flag 1', 'Flag 2'] },
    2: { 'type': 'checklist', 'title': 'Checklist', 'items': [('yes', 'Do X'), ('no', 'Avoid Y')] },
}

# --- REGEX FOR CLEANUP ---
def clean_text(raw: str) -> str:
    text = raw
    # Strip running headers
    text = re.sub(r'(?m)^(He\'s\s+Just\s+Not\s+That\s+Into\s+You)\s*', '', text)
    # Strip page numbers
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    # Join OCR soft hyphens
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()

# --- CLASSIFICATION LOGIC ---
def _classify_para(para: str) -> str:
    """Classify paragraph into specialized HTML blocks (Letters, Excuses, Stories)."""
    para_esc = html_lib.escape(para)
    
    if re.search(r'[Дд]орого[йи]\s+[Гг]рег', para):
        return (f'<div class="letter-q"><div class="letter-label">Letter to Greg</div>'
                f'<p>{para_esc}</p></div>')
    
    # ... more classification (Story, Workbook, Excuse Title)
    return f'<p>{para_esc}</p>'

# ... (refer to original convert_book.py for full implementation of infographics and building logic)
