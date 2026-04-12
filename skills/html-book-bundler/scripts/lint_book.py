#!/usr/bin/env python3
"""
Advanced Integrity Linter for Single-File HTML Books.
Enforces 100% bundling of all local and external resources.
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

        # 2. Payload Analysis
        b64_match = re.search(r'const\s+B64\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not b64_match:
            self.errors.append("Payload: Could not find B64_CHAPTERS array.")
            return False

        try:
            b64_chapters = json.loads(b64_match.group(1))
            self.stats['chapter_count'] = len(b64_chapters)
            for i, b64_str in enumerate(b64_chapters):
                try:
                    chapter_html = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                    self._audit_chapter(i + 1, chapter_html)
                except Exception as e:
                    self.errors.append(f"Chapter {i+1}: Failed to decode Base64 ({str(e)})")
        except Exception as e:
            self.errors.append(f"Payload: Failed to parse JSON ({str(e)})")

        return len(self.errors) == 0

    def _audit_shell(self, content: str):
        # Allow system protocols in Shell
        links = re.findall(r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", content)
        for link in links:
            is_allowed = (
                link.startswith('data:') or 
                link.startswith('#') or 
                link.startswith('javascript:') or 
                link.startswith('mailto:') or 
                link.startswith('tel:')
            )
            if not is_allowed and link.startswith('http'):
                 self.errors.append(f"Shell: Unbundled external resource found: {link}")
            elif not is_allowed:
                 self.errors.append(f"Shell: Unbundled local resource found: {link}")

    def _audit_chapter(self, index: int, html: str):
        prefix = f"Chapter {index}"
        
        # ALL resources must be bundled as Data URIs or be internal anchors/system protocols
        links = re.findall(r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", html)
        for link in links:
            is_valid = (
                link.startswith('data:') or 
                link.startswith('#') or 
                link.startswith('mailto:') or 
                link.startswith('tel:') or
                link.startswith('javascript:')
            )
            if not is_valid:
                self.errors.append(f"{prefix}: Found unbundled/external reference: {link}")

        # JS Sandbox (Allowed postMessage navigation only)
        clean_html = re.sub(r'window\.parent\.postMessage\s*\(', '', html)
        if 'window.parent' in clean_html or 'parent.window' in clean_html:
             self.errors.append(f"{prefix}: JS Sandbox Violation! Unauthorized access to window.parent.")

        # Data Integrity
        checkboxes = re.findall(r'<input[^>]+type=["\']checkbox["\']', html)
        if checkboxes:
            ids = re.findall(r'id=["\']([^"\']+)["\']', html)
            if len(set(ids)) < len(checkboxes):
                self.errors.append(f"{prefix}: Checkboxes missing unique IDs.")

    def report(self):
        print(f"\n{'='*60}")
        print(f"BOOK INTEGRITY REPORT: {self.file_path.name}")
        print(f"{'='*60}")
        print(f"Chapters: {self.stats.get('chapter_count', 0)} | Total Size: {self.stats.get('total_size_mb', 0):.2f} MB")
        
        if self.errors:
            print(f"\nCRITICAL ERRORS ({len(self.errors)}):")
            for e in self.errors: print(f"  [X] {e}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for w in self.warnings: print(f"  [!] {w}")

        if not self.errors:
            print("\nSTATUS: PASS - Book is 100% self-contained.")
        else:
            print("\nSTATUS: FAIL - Integrity issues detected.")
        print(f"{'='*60}\n")

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
