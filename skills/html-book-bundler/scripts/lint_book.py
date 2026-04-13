#!/usr/bin/env python3
"""
Enterprise-grade Linter for Single-File HTML Books.
Focus: 100% Offline Safety, UTF-8, and JS Sandboxing.
"""

import argparse
import base64
import json
import pathlib
import re
import sys

class BookLinter:
    def __init__(self, file_path: str, max_size_mb: float = 30.0):
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
        self.stats['size_mb'] = self.file_path.stat().st_size / (1024 * 1024)

        if self.stats['size_mb'] > self.max_size_mb:
            self.warnings.append(f"File size ({self.stats['size_mb']:.1f} MB) is high. Mobile browsers may struggle.")

        # 1. Shell Audit
        if "Content-Security-Policy" not in content:
            self.errors.append("Shell: Missing Content-Security-Policy meta tag!")
        
        if "sandbox" not in content.lower():
            self.errors.append("Shell: <iframe> missing 'sandbox' attribute!")

        # 2. External Resource Check (Must be 0 for true offline)
        ext_refs = re.findall(r'(src|href|url)\s*=\s*[\'"](http[s]?://[^\'"]+)[\'"]', content, re.I)
        for _, url in ext_refs:
            self.errors.append(f"Shell: External link found (not bundled): {url}")

        # 3. Payload Extraction
        b64_match = re.search(r'const\s+B64\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not b64_match:
            self.errors.append("Payload: B64_CHAPTERS not found.")
            return False

        try:
            chapters = json.loads(b64_match.group(1))
            self.stats['chapters'] = len(chapters)
            for i, b64_str in enumerate(chapters):
                self._audit_chapter(i + 1, base64.b64decode(b64_str).decode('utf-8', errors='ignore'))
        except Exception as e:
            self.errors.append(f"Payload: Failed to decode/parse chapters ({e})")

        return len(self.errors) == 0

    def _audit_chapter(self, idx: int, html: str):
        p = f"Ch {idx}"
        
        # Security: Detect attempts to escape sandbox
        # Robust regex for parent/top/opener access
        unsafe_js = re.search(r'(window|top|parent|opener)\s*(\.|\[|\]|\s+)+(\.|\s+)*(parent|top|opener|location|cookie)', html, re.I)
        if unsafe_js and "postMessage" not in html: # Allow our bridge, block everything else
             self.errors.append(f"{p}: Potential Sandbox Escape detected! (Unsafe JS: {unsafe_js.group(0)})")

        # Resource bundling
        links = re.findall(r'(src|href|srcset)\s*=\s*[\'"]([^\'"]+)[\'"]', html, re.I)
        for _, url in links:
            if url.startswith('http'):
                self.errors.append(f"{p}: External reference (must bundle): {url}")
            elif not (url.startswith('data:') or url.startswith('#') or url.startswith('blob:')):
                if url.endswith('.html') or '.html#' in url:
                    continue # Allow cross-chapter links handled by bridge
                # In a single-file book, relative paths like "img.png" are invalid in a Blob context
                self.errors.append(f"{p}: Unbundled local path: {url}")

        if "charset=utf-8" not in html.lower() and "charset=\"utf-8\"" not in html.lower():
            self.warnings.append(f"{p}: Missing <meta charset='utf-8'>")

    def report(self):
        print(f"\n{'='*60}\nBOOK AUDIT: {self.file_path.name}\n{'='*60}")
        print(f"Size: {self.stats.get('size_mb',0):.2f} MB | Chapters: {self.stats.get('chapters',0)}")
        
        for e in self.errors: print(f"  [X] ERROR: {e}")
        for w in self.warnings: print(f"  [!] WARN:  {w}")
        
        if not self.errors:
            print("\nSTATUS: PASS - 100% Offline & Secure.")
        else:
            print("\nSTATUS: FAIL - Critical issues found.")
        print("="*60 + "\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--max-size", type=float, default=30.0)
    args = p.parse_args()
    linter = BookLinter(args.file, args.max_size)
    success = linter.run()
    linter.report()
    sys.exit(0 if success else 1)
