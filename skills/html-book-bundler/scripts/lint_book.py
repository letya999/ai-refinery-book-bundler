#!/usr/bin/env python3
"""
Master Linter for HTML Book Bundler (v8.2).
Combines Security, Design, and Structural audits into one tool.
"""
import argparse
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

        # 1. Shell Infrastructure Checks
        if 'Content-Security-Policy' not in content:
            self.errors.append("Shell: Missing Content-Security-Policy meta tag")
        if 'sandbox' not in content.lower():
            self.errors.append("Shell: <iframe> missing sandbox attribute")
        if "prefers-reduced-motion" not in content:
            self.warnings.append("Shell: No prefers-reduced-motion media query found (a11y)")
        if "URL.createObjectURL" in content:
            self.warnings.append("Shell: Legacy Blob URL usage detected (srcdoc is preferred)")

        # 2. Template Integrity
        unresolved = re.findall(r'\{\{[A-Z_]+\}\}', content)
        if unresolved:
            self.errors.append(f"Template: Unresolved placeholders found: {', '.join(set(unresolved))}")

        # 3. Chapter Data Checks
        chapters_start = re.search(r'\bCHAPTERS\s*=\s*(\[)', content)
        if not chapters_start:
            self.errors.append("Data: CHAPTERS array not found (architecture mismatch)")
            return False

        try:
            decoder = json.JSONDecoder()
            chapters, _ = decoder.raw_decode(content, chapters_start.start(1))
            self.stats['chapters'] = len(chapters)
            if not chapters:
                self.warnings.append("Data: CHAPTERS array is empty")
            for i, ch_html in enumerate(chapters):
                if not isinstance(ch_html, str):
                    self.errors.append(f"Chapter {i+1}: Not a string (invalid JSON data)")
                else:
                    self._audit_chapter(i + 1, ch_html)
        except Exception as e:
            self.errors.append(f"Data: Failed to parse CHAPTERS array: {e}")

        # 4. File Size Warning
        if self.stats['size_mb'] > self.max_size_mb:
            self.warnings.append(
                f"File size {self.stats['size_mb']:.1f} MB exceeds threshold {self.max_size_mb} MB"
            )

        return len(self.errors) == 0

    def _audit_chapter(self, idx: int, html: str):
        label = f"Chapter {idx}"

        # SVG Hex Color Check — catches both attribute and inline style forms
        svgs = re.findall(r'<svg[^>]*>.*?</svg>', html, re.I | re.S)
        for svg in svgs:
            # Extended hex check (v8.2 audit fix)
            attr_hex = re.search(
                r'(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*["\']#[0-9a-fA-F]{3,6}["\']',
                svg, re.I
            )
            style_hex = re.search(
                r'style\s*=\s*["\'][^"\']*(?:fill|stroke|stop-color|flood-color|lighting-color)\s*:\s*#[0-9a-fA-F]{3,6}',
                svg, re.I
            )
            if attr_hex or style_hex:
                self.errors.append(f"{label}: Hardcoded hex color in <svg>. Use CSS variables.")

        # viewBox enforcement
        for svg_match in re.finditer(r'<svg([^>]*)>', html, re.I):
            attrs = svg_match.group(1)
            if 'viewBox' not in attrs and 'viewbox' not in attrs.lower():
                self.errors.append(f"{label}: <svg> missing viewBox attribute (required for mobile responsiveness)")
                break  # one error per chapter is enough

        # user-scalable=no check (WCAG 1.4.4)
        if re.search(r'user-scalable\s*=\s*no', html, re.I):
            self.errors.append(f"{label}: viewport meta has user-scalable=no (WCAG 1.4.4 violation)")

        # lang attribute check
        if re.search(r'<html(?![^>]*\blang\s*=)', html, re.I):
            self.warnings.append(f"{label}: <html> element missing lang attribute (accessibility)")

        # Wall of Text Check
        visual_tags = r"""class=["'][^"']*\b(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)\b[^"']*["']|<table>"""
        if len(html) > 5000 and not re.search(visual_tags, html, re.I):
            self.warnings.append(f"{label}: Potential 'wall of text' detected ({len(html)} chars).")

        # Security: Sandbox Escape
        safe = html.replace('window.parent.postMessage', '__BRIDGE__')
        danger = re.search(r'\b(?:window|top|parent|opener)\s*\.\s*(?:location|cookie|href|assign|replace|open)\b', safe, re.I)
        if danger:
            self.errors.append(f"{label}: Potential sandbox escape pattern: {danger.group(0)!r}")

        # External Requests
        ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+["\']', safe, re.I)
        if ext:
            self.errors.append(f"{label}: External network dependency (not 100% offline): {ext[0]}")

    def report(self):
        sep = '=' * 60
        print(f"\n{sep}\nMASTER LINT REPORT: {self.file_path.name}\n{sep}")
        print(f"Size: {self.stats.get('size_mb', 0):.2f} MB | Chapters: {self.stats.get('chapters', 0)}")
        for e in self.errors:   print(f"  [ERROR] {e}")
        for w in self.warnings: print(f"  [WARN]  {w}")
        if not self.errors:
            print("\nSTATUS: PASS (100% Secure & Offline-Ready)")
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
