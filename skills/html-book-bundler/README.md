# HTML Book Bundler v5.0

Bundles book chapters into a single offline-first HTML reading app. No server, no internet, no dependencies — open the output file in any browser.

**Output features:**
- Left sidebar with chapter list and full-text search
- Bookmarks with persistent localStorage storage
- Scroll position saved and restored per chapter
- Dark/light theme toggle (auto-detects system preference)
- Keyboard navigation (ArrowLeft/ArrowRight)
- Mobile-responsive with overlay sidebar

## Quick start

```bash
# 1. Put your chapters in a directory
ls chapters/
# chapter1.html  chapter2.html  chapter3.html

# 2. Bundle
node scripts/bundle.cjs --input ./chapters --output book.html --title "My Book"

# 3. Open in browser
# book.html — single file, works offline
```

## Ingest from FB2 / EPUB / DOCX

```bash
python scripts/ingest.py --input book.fb2 --output ./chapters
# then bundle as above
```

## Supported input formats

| Format | Support | Tool |
|--------|---------|------|
| HTML chapters | Native | `bundle.cjs` |
| FB2 / FB2.ZIP | Full | `ingest.py` |
| EPUB | Full | `ingest.py` |
| DOCX | Full | `ingest.py` (needs `python-docx`) |
| PDF | Full | `pdf_parser_general.py` (needs `PyMuPDF`) |

## File structure

```
html-book-bundler/
  scripts/
    bundle.cjs              # Main bundler CLI
    chapter_processor.cjs   # Chapter enrichment pipeline
    ingest.py               # FB2/EPUB/DOCX ingester
    pdf_parser_general.py   # Style-aware PDF extractor
    extract_pdf_visuals.py  # Extracts images/tables from PDF
    lint_book.py            # Security and quality linter
    audit_single_file_html.py
    dev_server.cjs          # Live-reload dev server
    optimize_assets.py      # Image compression
  templates/
    default.html            # Shell HTML template
  assets/
    theme.css               # Shared CSS (dark/light, components)
  lang/
    ru.json                 # Russian UI strings
    en.json                 # English UI strings
  tests/
    test_bundler.cjs        # 17 integration tests
  examples/
    scripts/                # Template scripts for complex books
    chapter1.html           # Example chapters
    chapter2.html
    chapter3.html
    example-book.html       # Pre-built example output
  SKILL.md                  # Full documentation
  INPUT_SPEC.md             # Chapter HTML specification
  requirements.txt          # Optional Python dependencies (PyMuPDF, python-docx)
  package.json
```

## Tests

```bash
node tests/test_bundler.cjs
# 17 tests: build, placeholders, srcdoc, CSP, i18n, titles, numeric sort, search, --help, error exit, a11y
```

## Dev server

```bash
node scripts/dev_server.cjs --input ./chapters --output preview.html
# Open http://localhost:3000 — rebuilds and reloads on file change
```

## Linting

```bash
python scripts/lint_book.py --file book.html
# Checks: CSP, sandbox, chapter count, sandbox escape patterns, external URLs
```

## Architecture

Chapters are stored as raw UTF-8 strings in the `CHAPTERS` JS array inside the output HTML. The shell loads chapters via `iframe.srcdoc` — no base64 overhead, no Blob URL lifecycle, same-origin for direct DOM access.

Search uses a bundle-time inverted index (`SIDX`) with prefix matching and AND intersection. No external library, ~50 lines.

See [SKILL.md](SKILL.md) for full documentation and [INPUT_SPEC.md](INPUT_SPEC.md) for chapter format reference.
