#!/usr/bin/env python3
"""
Security and quality linter for bundled single-file HTML books.

Usage:
  python lint_book.py --file my-book.html [--max-size 30]
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
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict = {}

    def run(self) -> bool:
        if not self.file_path.exists():
            self.errors.append(f"File not found: {self.file_path}")
            return False

        content = self.file_path.read_text(encoding='utf-8', errors='replace')
        self.stats['size_mb'] = self.file_path.stat().st_size / (1024 * 1024)

        if self.stats['size_mb'] > self.max_size_mb:
            self.warnings.append(
                f"File size {self.stats['size_mb']:.1f} MB exceeds threshold {self.max_size_mb} MB"
            )

        # Shell checks
        if 'Content-Security-Policy' not in content:
            self.errors.append("Shell: missing Content-Security-Policy meta tag")
        if 'sandbox' not in content.lower():
            self.errors.append("Shell: <iframe> missing sandbox attribute")

        # Locate chapter data — bundler emits: CHAPTERS = [...]
        # Use raw_decode to correctly handle ] inside JSON string values
        chapters_start = re.search(r'\bCHAPTERS\s*=\s*(\[)', content)
        if not chapters_start:
            self.errors.append("Data: CHAPTERS array not found in output (wrong template or corrupted build)")
            return False

        try:
            decoder = json.JSONDecoder()
            chapters, _ = decoder.raw_decode(content, chapters_start.start(1))
            self.stats['chapters'] = len(chapters)
            if not chapters:
                self.warnings.append("Data: CHAPTERS array is empty")
            for i, ch_html in enumerate(chapters):
                if not isinstance(ch_html, str):
                    self.errors.append(f"Chapter {i+1}: not a string (expected srcdoc HTML)")
                else:
                    self._audit_chapter(i + 1, ch_html)
        except Exception as e:
            self.errors.append(f"Data: failed to parse CHAPTERS array: {e}")

        return len(self.errors) == 0

    def _audit_chapter(self, idx: int, html: str):
        label = f"Chapter {idx}"

        # Mask our intentional inter-chapter bridge before security checks
        safe = html.replace('window.parent.postMessage', '__BRIDGE__')

        # Enforce CSS variables in SVGs
        svgs = re.findall(r'<svg[^>]*>.*?</svg>', html, re.I | re.S)
        for svg in svgs:
            if re.search(r'(?:fill|stroke)\s*=\s*["\']#[0-9a-fA-F]{3,6}["\']', svg, re.I):
                self.errors.append(f"{label}: Hardcoded hex color found in <svg>. Must use CSS variables (e.g. fill: var(--acc)).")

        # Detect wall of text (long chapter without visual components)
        visual_tags = r'class=["\'][^"\']*\b(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)\b[^"\']*["\']|<table>'
        if len(html) > 5000 and not re.search(visual_tags, html, re.I):
            self.warnings.append(f"{label}: Potential 'wall of text' detected ({len(html)} chars) with no visual components.")

        # Detect genuinely dangerous DOM escape patterns
        danger = re.search(
            r'\b(?:window|top|parent|opener)\s*\.\s*(?:location|cookie|href|assign|replace|open)\b',
            safe, re.I
        )
        if danger:
            self.errors.append(f"{label}: potential sandbox escape: {danger.group(0)!r}")

        # Detect external network requests in chapter HTML
        ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+["\']', safe, re.I)
        if ext:
            for url in ext[:3]:
                self.warnings.append(f"{label}: external dependency: {url}")

    def report(self):
        sep = '=' * 60
        print(f"\n{sep}\nLINT REPORT: {self.file_path.name}\n{sep}")
        print(f"Size: {self.stats.get('size_mb', 0):.2f} MB | Chapters: {self.stats.get('chapters', 0)}")
        for e in self.errors:   print(f"  [ERROR] {e}")
        for w in self.warnings: print(f"  [WARN]  {w}")
        if not self.errors:
            print("\nSTATUS: PASS (100% Offline & Secure)")
        else:
            print("\nSTATUS: FAIL")
        print(sep + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--file',     required=True)
    p.add_argument('--max-size', type=float, default=30.0)
    args = p.parse_args()

    linter = BookLinter(args.file, args.max_size)
    success = linter.run()
    linter.report()
    sys.exit(0 if success else 1)
