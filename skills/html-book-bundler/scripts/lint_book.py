#!/usr/bin/env python3
"""
Advanced Integrity Linter for Single-File HTML Books.
Performs deep analysis of both the Shell and bundled Base64 chapters.
"""

import argparse
import base64
import json
import pathlib
import re
import sys
from typing import List, Dict

class BookLinter:
    def __init__(self, file_path: str, max_size_mb: float):
        self.file_path = pathlib.Path(file_path)
        self.max_size_mb = max_size_mb
        self.errors = []
        self.warnings = []
        self.stats = {}

    def run(self):
        if not self.file_path.exists():
            self.errors.append(f"File not found: {self.file_path}")
            return False

        content = self.file_path.read_text(encoding="utf-8", errors="replace")
        self.stats['total_size_mb'] = self.file_path.stat().st_size / (1024 * 1024)

        # 1. Shell Analysis
        self._audit_shell(content)

        # 2. Payload Analysis (Base64 extraction)
        b64_chapters = re.findall(r'\"(PCFET0NUW[^\"]+)\"', content)
        self.stats['chapter_count'] = len(b64_chapters)
        
        for i, b64_str in enumerate(b64_chapters):
            try:
                chapter_html = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                self._audit_chapter(i + 1, chapter_html)
            except Exception as e:
                self.errors.append(f"Chapter {i+1}: Failed to decode Base64 ({str(e)})")

        return len(self.errors) == 0

    def _audit_shell(self, content: str):
        # External Dependencies
        ext = re.findall(r"(?:src|href)\s*=\s*['\"](https?://[^'\"]+)['\"]", content)
        if ext:
            self.errors.append(f"External dependencies found in Shell: {set(ext)}")

        # Core APIs
        if "URL.createObjectURL" in content and "URL.revokeObjectURL" not in content:
            self.warnings.append("Memory Management: createObjectURL found without revokeObjectURL.")
        
        if "localStorage" not in content:
            self.warnings.append("UX: No localStorage detected. Reading progress will not be saved.")

        if "prefers-reduced-motion" not in content:
            self.warnings.append("A11y: prefers-reduced-motion media query missing in Shell.")

    def _audit_chapter(self, index: int, html: str):
        prefix = f"Chapter {index}"
        
        # Isolation Checks
        if "charset=\"utf-8\"" not in html.lower():
            self.errors.append(f"{prefix}: Missing UTF-8 charset declaration.")
        
        if "viewport" not in html.lower():
            self.warnings.append(f"{prefix}: Missing viewport meta tag.")

        # JS Sandbox Check
        if "window.parent" in html or "top.location" in html or "parent.location" in html:
            self.errors.append(f"{prefix}: JS Sandbox Violation! Chapter attempts to access parent frame.")

        # Accessibility
        imgs_no_alt = re.findall(r'<img(?![^>]*\balt=)[^>]*>', html)
        if imgs_no_alt:
            self.warnings.append(f"{prefix}: Found {len(imgs_no_alt)} images without alt text.")

        # Data Integrity
        checkboxes = re.findall(r'type=["\']checkbox["\']', html)
        if checkboxes:
            ids = re.findall(r'id=["\']([^"\']+)["\']', html)
            if len(set(ids)) < len(checkboxes):
                self.errors.append(f"{prefix}: Checkboxes found but unique IDs are missing. Persistence will fail.")

        # Asset Size Bloat
        if len(html) > 1024 * 1024: # 1MB per chapter
            self.warnings.append(f"{prefix}: Size is large ({len(html)/1024:.1f} KB). Check for unoptimized images.")

    def report(self):
        print(f"\n{'='*40}")
        print(f"BOOK AUDIT REPORT: {self.file_path.name}")
        print(f"{'='*40}")
        print(f"Total Chapters: {self.stats.get('chapter_count', 0)}")
        print(f"Total Size:     {self.stats.get('total_size_mb', 0):.2f} MB")
        
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for e in self.errors: print(f"  [X] {e}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for w in self.warnings: print(f"  [!] {w}")

        if not self.errors and not self.warnings:
            print("\nPERFECT: All quality gates passed.")
        elif not self.errors:
            print("\nPASS: No critical errors found.")
        else:
            print("\nFAIL: Critical integrity issues detected.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--max-size", type=float, default=15.0)
    args = p.parse_args()

    linter = BookLinter(args.file, args.max_size)
    success = linter.run()
    linter.report()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
