---
name: html-book-bundler
description: Engineering self-contained, multi-volume, mobile-first HTML books with universal ingestion (EPUB, FB2) and advanced adaptive typography.
---

# HTML Book Bundler (v3.0 - Enterprise Edition)

A top-tier publishing pipeline that transforms standard e-books (FB2, EPUB) and raw HTML into highly optimized, adaptive, and 100% offline web applications.

## 1. Core Innovations

### A. The Universal Ingester (`ingest.py`)
Automatically parses `FB2` and `EPUB` archives, extracts structural semantic HTML, and safely unloads binary assets (images) into an isolated `assets/` directory.

### B. Smart Volume Splitting (Многотомник)
Never crash a mobile browser again. The bundler (`bundle.cjs`) tracks Base64 payload weight. If a book exceeds the defined threshold (default: 15MB), it seamlessly splits it into multiple HTML files (`book_vol1.html`, `book_vol2.html`).
- Global Manifest ensures cross-volume navigation is completely invisible to the user.
- Shared `LocalStorage` syncs reading progress and scroll position across all volumes.

### C. Mobile-First App Shell
- **Thumb-Friendly:** "Next Chapter" huge action buttons at the bottom of the content.
- **Fluid Typography:** CSS `clamp()` dynamically scales fonts to match the exact screen width (from iPhone SE to 4K monitors).
- **Responsive Wrappers:** Automatically detects huge tables and injects `overflow-x: auto` wrappers.

## 2. Workflows

### 1. Ingestion (Convert FB2/EPUB to Raw HTML)
```bash
# Requires: pip install lxml (for FB2)
python scripts/ingest.py --input ./book.fb2 --output ./staging_chapters
```

### 2. Assembly & Splitting
```bash
# Packs HTML into offline bundles. Split if > 15MB.
node scripts/bundle.cjs --input ./staging_chapters --output my_book.html --max-size 15
```

### 3. Security Audit
```bash
python scripts/lint_book.py --file my_book.html
```

## 3. Security Constraints (Enforced)
- **Zero Network:** Strict `Content-Security-Policy: default-src 'none'` blocks any tracking or remote exploitation.
- **Iframe Sandboxing:** The reader frame strictly utilizes `sandbox="allow-scripts allow-same-origin"` to prevent cross-origin contamination.
