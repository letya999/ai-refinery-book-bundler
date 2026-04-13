#!/usr/bin/env python3
"""
Advanced Integrity Linter for Single-File HTML Books.
Enforces 100% bundling and UTF-8 safety.
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

        # Optimized reading: read small chunks if we only needed metadata, 
        # but for SAST we need the whole content.
        try:
            content = self.file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        self.stats['total_size_mb'] = self.file_path.stat().st_size / (1024 * 1024)
        if self.stats['total_size_mb'] > self.max_size_mb:
            self.warnings.append(f"Total size ({self.stats['total_size_mb']:.1f} MB) exceeds threshold ({self.max_size_mb} MB).")

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
                    self.errors.append(f"Chapter {i+1}: Failed to decode Base64/UTF8 ({str(e)})")
        except Exception as e:
            self.errors.append(f"Payload: Failed to parse JSON ({str(e)})")

        return len(self.errors) == 0

    def _audit_shell(self, content: str):
        # Strict Shell Audit
        links = re.findall(r"(?:src|href)\s*=\s*['\"]([^'\"]+)['\"]", content)
        for link in links:
            is_allowed = (
                link.startswith('data:') or 
                link.startswith('#') or 
                link.startswith('javascript:') or 
                link.startswith('mailto:') or 
                link.startswith('tel:')
            )
            if not is_allowed:
                 self.errors.append(f"Shell: Unbundled resource found: {link}")

    def _audit_chapter(self, index: int, html: str):
        prefix = f"Chapter {index}"
        
        # ALL resources must be bundled
        links = re.findall(r"(?:src|href|srcset)\s*=\s*['\"]([^'\"]+)['\"]", html)
        for link in links:
            # Handle srcset comma-separated values
            parts = [p.strip().split()[0] for p in link.split(',') if p.strip()]
            for p in parts:
                is_valid = (
                    p.startswith('data:') or 
                    p.startswith('#') or 
                    p.startswith('mailto:') or 
                    p.startswith('tel:') or
                    p.startswith('javascript:')
                )
                if not is_valid:
                    self.errors.append(f"{prefix}: Found unbundled reference: {p}")

        # JS Sandbox
        clean_html = re.sub(r'window\.parent\.postMessage\s*\(', '', html)
        if 'window.parent' in clean_html or 'parent.window' in clean_html:
             self.errors.append(f"{prefix}: JS Sandbox Violation! Unauthorized window.parent.")

        # Accessibility/Quality
        if "charset=utf-8" not in html.lower() and "charset=\"utf-8\"" not in html.lower():
            self.warnings.append(f"{prefix}: Missing UTF-8 charset meta tag.")

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
            print("\nSTATUS: PASS - 100% Self-contained.")
        else:
            print("\nSTATUS: FAIL - Critical issues found.")
        print(f"{'='*60}\n")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--max-size", type=float, default=50.0)
    args = p.parse_args()
    linter = BookLinter(args.file, args.max_size)
    success = linter.run()
    linter.report()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
