#!/usr/bin/env python3
"""
Audit single-file HTML book quality gates.

Usage:
  python skills/html-book-bundler/scripts/audit_single_file_html.py --file ./book.html

Checks:
- no external http(s) dependencies in src/href
- warn if createObjectURL is used without revokeObjectURL
- warn if prefers-reduced-motion is missing
- warn if file is very large
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True, help="Path to built single-file HTML")
    p.add_argument("--max-size-mb", type=float, default=12.0, help="Warn if file exceeds this size")
    args = p.parse_args()

    path = pathlib.Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    text = path.read_text(encoding="utf-8", errors="replace")

    # Hard fail: external dependencies.
    ext = re.findall(r"(?:src|href)\s*=\s*['\"](https?://[^'\"]+)['\"]", text, flags=re.IGNORECASE)

    errors = []
    warns = []

    if ext:
        errors.append("External dependencies detected:")
        for url in sorted(set(ext)):
            errors.append(f"  - {url}")

    has_create = "URL.createObjectURL" in text
    has_revoke = "URL.revokeObjectURL" in text
    if has_create and not has_revoke:
        warns.append("createObjectURL is used but revokeObjectURL is missing (possible memory leak).")

    if "prefers-reduced-motion" not in text:
        warns.append("No prefers-reduced-motion media query found.")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > args.max_size_mb:
        warns.append(f"Large file size: {size_mb:.2f} MB (threshold: {args.max_size_mb:.2f} MB).")

    print(f"Audit file: {path}")
    print(f"Size: {size_mb:.2f} MB")

    if errors:
        print("\nFAIL")
        for e in errors:
            print(e)
    else:
        print("\nPASS: no external dependencies in src/href")

    if warns:
        print("\nWARNINGS")
        for w in warns:
            print(f"- {w}")
    else:
        print("\nNo warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
