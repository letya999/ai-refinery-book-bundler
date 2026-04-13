#!/usr/bin/env python3
"""
Audit single-file HTML book quality gates (v5.0 - srcdoc architecture).

Usage:
  python audit_single_file_html.py --file ./book.html [--max-size-mb 30]

Checks:
- No external http(s) dependencies in src/href (hard fail)
- CHAPTERS array present (srcdoc architecture)
- iframe sandbox attribute present
- CSP meta tag present
- prefers-reduced-motion media query present
- File size within threshold (warning)
- No legacy Blob URL usage (warning if found, srcdoc should replace it)
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True, help="Path to built single-file HTML")
    p.add_argument("--max-size-mb", type=float, default=30.0, help="Warn if file exceeds this size")
    args = p.parse_args()

    path = pathlib.Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    text = path.read_text(encoding="utf-8", errors="replace")
    size_mb = path.stat().st_size / (1024 * 1024)

    errors: list[str] = []
    warns: list[str] = []

    # Hard fail: external dependencies in src/href attributes
    ext_urls = re.findall(r'(?:src|href)\s*=\s*[\'\"](https?://[^\'\"]+)[\'\"]', text, flags=re.IGNORECASE)
    if ext_urls:
        errors.append("External dependencies detected (book is not fully offline):")
        for url in sorted(set(ext_urls))[:10]:
            errors.append(f"  - {url}")

    # Hard fail: missing CSP
    if "Content-Security-Policy" not in text:
        errors.append("Missing Content-Security-Policy meta tag")

    # Hard fail: iframe without sandbox
    if re.search(r'<iframe', text, re.IGNORECASE) and 'sandbox' not in text.lower():
        errors.append("iframe present but sandbox attribute missing")

    # Hard fail: CHAPTERS array (srcdoc architecture marker)
    if not re.search(r'\bCHAPTERS\s*=\s*\[', text):
        errors.append("CHAPTERS array not found — output may be from old architecture or corrupted build")

    # Warnings
    if size_mb > args.max_size_mb:
        warns.append(f"Large file size: {size_mb:.2f} MB (threshold: {args.max_size_mb:.2f} MB) — consider --optimize")

    if "prefers-reduced-motion" not in text:
        warns.append("No prefers-reduced-motion media query found (accessibility)")

    if "URL.createObjectURL" in text:
        warns.append("URL.createObjectURL found — srcdoc architecture should not need Blob URLs")

    if "{{" in text:
        remaining = re.findall(r'\{\{[A-Z_]+\}\}', text)
        if remaining:
            warns.append(f"Unresolved template placeholders: {', '.join(set(remaining))}")

    # Report
    print(f"Audit: {path.name}")
    print(f"Size:  {size_mb:.2f} MB")

    if errors:
        print("\nFAIL")
        for e in errors:
            print(f"  [ERROR] {e}")
    else:
        print("\nPASS: no errors")

    if warns:
        print("\nWarnings:")
        for w in warns:
            print(f"  [WARN]  {w}")
    else:
        print("No warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
