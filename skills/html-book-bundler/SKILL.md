---
name: html-book-bundler
description: Converts book chapters (HTML, FB2, EPUB, DOCX, OCR output) into a single self-contained offline HTML app with sidebar navigation, full-text search, bookmarks, scroll persistence, and dark/light theme.
---

# HTML Book Bundler (v5.0)

Transforms raw chapter HTML files into a single `.html` file that works 100% offline with no external dependencies. The output is a mobile-first reading app: sidebar chapter list, full-text search, bookmarks, scroll persistence, keyboard navigation, dark/light theme toggle, and chapter content loaded via `iframe.srcdoc`.

## Architecture

```
chapters/*.html  →  bundle.cjs  →  book.html
      ↓                ↓
  ingest.py       chapter_processor.cjs  (enrichment pipeline)
  (FB2/EPUB/DOCX)      ↓
                  assets/theme.css       (shared styles injected into every chapter)
                  lang/ru.json           (i18n strings, --lang flag)
                  lang/en.json
                  templates/default.html (shell: sidebar + iframe + JS navigation)
```

### What the shell does
- Left sidebar: chapter list with search filter and collapsible bookmarks panel
- Top nav: prev/next buttons + chapter title + progress bar
- Chapter content loaded via `iframe.srcdoc` (UTF-8, no base64, no Blob URL lifecycle)
- Full-text search with inverted index (SIDX), prefix matching, AND intersection
- Scroll position saved/restored per chapter (ratio-based, survives window resize)
- Theme toggle (dark/light) propagated into iframe via `contentDocument.documentElement`
- Keyboard navigation: ArrowLeft/ArrowRight
- Mobile: hamburger opens sidebar over overlay
- All UI strings from `const LANG = {{LANG_JSON}}` (ru/en or custom)

### What `chapter_processor.cjs` does (before srcdoc)
Applied universally to every chapter regardless of source:

1. **`autoCollapseLongParas()`** — wraps `<p>` blocks > 480 chars in `<details class="long-para">` with a preview summary
2. **`autoInjectInsights()`** — extracts clean sentences (45-160 chars, Unicode `[\p{L}\p{N}...]`) from early paragraphs and injects `<blockquote class="insight">` pullquotes after 4th and 10th `</p>` (language-agnostic)
3. **`styleFirstPara()`** — adds `class="lead-para"` to the first `<p>` for larger opening text
4. **navScript injection** — intercepts `<a href="chapterN.html">` (and `001.html` padded pattern) and routes them via `window.parent.postMessage` for cross-chapter navigation
5. **Shared theme injection** — `theme.css` is injected as a `<style>` block before the chapter's own styles

### Why `srcdoc` (v5.0 change from base64+Blob)
- **No size overhead**: base64 adds 33% to binary assets; `srcdoc` stores chapters as raw UTF-8 strings
- **No 2MB limit**: Chrome's `data:` URI limit blocked large chapters; `srcdoc` has no such restriction
- **No Blob URL lifecycle**: no `URL.createObjectURL` / `URL.revokeObjectURL` needed
- **Same-origin access**: `fr.contentDocument` directly accessible for scroll tracking and theme propagation — no postMessage round-trips

### What `theme.css` provides
CSS variables (dark + light), layout (`.wrap`, `.hero`, `.sec`), stats grid, card grid, accordion, translator, table, badge, scrollbar, responsive breakpoints, `env(safe-area-inset-*)` mobile notch, `max-width: 72ch` reading width, `prefers-reduced-motion` support, `prefers-color-scheme: light` auto-detection.

## Usage

### 1. Assemble a book from HTML chapters
```bash
node skills/html-book-bundler/scripts/bundle.cjs \
  --input ./chapters \
  --output my-book.html \
  --title "Book Name" \
  --lang ru
```

Chapters must be named `chapter1.html`, `chapter2.html`, ... The bundler reads them in `localeCompare` numeric order. A local `theme.css` in the chapters directory takes precedence over `assets/theme.css`.

### 2. Ingest from FB2, EPUB, or DOCX
```bash
python skills/html-book-bundler/scripts/ingest.py \
  --input ./book.fb2 \
  --output ./chapters
# Supports: .fb2  .fb2.zip  .epub  .docx
# Add --force to overwrite existing output directory
```

Then run step 1.

### 3. From PDF (via OCR)
- Use Windows OCR (PowerShell) or any OCR tool to produce JSON of `[{page, text}, ...]`
- Write a book-specific `convert_book.py` that:
  - Defines chapter page ranges
  - Splits pages into chapters, cleans OCR artifacts
  - Calls `split_long_para()` at sentence boundaries every ~600 chars
  - Adds per-chapter stats, callouts, and visual blocks (`CHAPTER_VISUALS` dict)
  - Writes styled `chapterN.html` files with full CSS
- Then run step 1

### 4. Dev server (live-reload)
```bash
node skills/html-book-bundler/scripts/dev_server.cjs \
  --input ./chapters \
  --output ./preview.html \
  --port 3000
```

### 5. Audit and lint
```bash
python skills/html-book-bundler/scripts/audit_single_file_html.py --file my-book.html
python skills/html-book-bundler/scripts/lint_book.py --file my-book.html
```

### 6. Run tests
```bash
node skills/html-book-bundler/tests/test_bundler.cjs
# 17 tests: build, placeholders, srcdoc, CSP, i18n, titles, numeric sort, search, --help, error exit, a11y
```

## CLI Reference

```
node bundle.cjs --input <dir> --output <file.html> [options]

Required:
  --input  <dir>      Directory containing chapter HTML files
  --output <file>     Output HTML file path

Options:
  --title  <string>   Book title (default: output filename)
  --lang   <code>     UI language: ru | en  (default: ru)
  --dev               Inject live-reload script
  --optimize          Run optimize_assets.py before bundling
  --template <file>   Custom HTML template (default: templates/default.html)
  --help              Show usage
```

## Visual Components (CSS-only, no dependencies)

Available in `theme.css` — use in chapter HTML:

| Class | Description |
|---|---|
| `.stats` / `.stat` | Stats grid with big number + label |
| `.card` / `.grid` | Card grid with hover lift |
| `.translator` | Two-column comparison (good/bad) |
| `.acc-item` / `.acc-head` / `.acc-body` | Accordion (details/summary pattern) |
| `blockquote.insight` | Pullquote with accent left border |
| `details.long-para` | Collapsible long paragraph |
| `.lead-para` | Larger opening paragraph |
| `.sec` | Section container with subtle background |
| `.badge` | Status badge |

### Chapter-specific visual types (for book scripts)

Add CSS in the chapter's own `<style>` block:

| Type | Class | Use when |
|---|---|---|
| `red_flags` | `.red-flags`, `.rf-item`, `.rf-num` | Numbered warning list |
| `checklist` | `.checklist`, `.cl-item.yes/.no` | Yes/No comparison list |
| `timeline` | `.vis-timeline`, `.tl-step`, `.tl-arrow` | Sequential steps |
| `status_badge` | `.status-badge`, `.sb-icon/.sb-label/.sb-sub` | Single bold statement |
| `truth_scale` | `.truth-scale`, `.ts-col.myth/.reality` | Myth vs reality columns |
| `compare_grid` | `.compare-grid`, `.cg-col.excuse/.truth` | Excuse vs truth columns |

## Security

- **CSP**: `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:` — no external requests
- **iframe sandbox**: `allow-scripts allow-same-origin` — chapter content isolated from shell
- **No CDN, no external fonts, no network calls** — fully offline
- **All inter-frame communication** via `window.parent.postMessage` for navigation; scroll/theme use direct `contentDocument` access (same-origin srcdoc)

## i18n

Add language files in `lang/`:
```json
{
  "code": "en",
  "dir": "ltr",
  "chapter": "Chapter",
  "loading": "Loading...",
  "search_placeholder": "Search the book...",
  "prev": "← Back",
  "next": "Forward →",
  "bookmark_add": "☆",
  "bookmark_remove": "★",
  "bookmarks_title": "Bookmarks",
  "no_bookmarks": "No bookmarks yet",
  "theme_to_light": "☀",
  "theme_to_dark": "☾",
  "chapter_label": "Chapter {n}"
}
```

Pass `--lang <code>` to `bundle.cjs`. Falls back to `ru.json` if file not found.

## Lessons Learned

### Architecture
- `iframe.srcdoc` vs base64+Blob: srcdoc wins on all dimensions for text content (no overhead, no limits, same-origin, lifecycle-free)
- Template placeholder replacement: use `str.split(placeholder).join(value)` — handles multiple occurrences and avoids regex escaping issues with JSON content
- Lint regex for JSON arrays: `re.search(r'\[')` + `json.JSONDecoder.raw_decode()` — never use `[\s\S]*?` which stops at first `]` inside string values

### OCR-sourced text
- OCR output is one page = one paragraph. Call `split_long_para()` at sentence boundaries every ~600 chars before any classification
- Running book headers appear on every OCR page — strip them with regex before processing
- Q&A-structured books benefit from `_is_qa_para()` detection to separate narrative from Q&A sections

### Visual variety
- Every chapter having the same visual type makes the book monotonous
- Use a `CHAPTER_VISUALS` dict mapping chapter index → visual type config
- Match visual type semantically: warnings → red_flags, cycles → timeline, binary judgements → status_badge

### CSS injection architecture
- Inject `theme.css` as a `<style>` block BEFORE the chapter's own styles (inside `prepareChapter`)
- Chapter styles override the base theme via cascade
- Do NOT inject CSS into the shell HTML after the fact — the iframe is sandboxed

### Language-agnostic text quality
- Use Unicode property escapes `[\p{L}\p{N}...]` instead of Cyrillic-specific ranges
- This makes `autoInjectInsights()` work for English, German, French, etc.

### Sidebar scrolling with many chapters
- `.side` needs explicit `height: 100vh; overflow: hidden` for `.list { flex:1; overflow-y: auto }` to activate
- Without bounded parent height, `flex: 1` has no reference and overflow never kicks in

### Cross-chapter links
- navScript must map BOTH `chapterN.html` AND `NNN.html` (padded) patterns
- `ingest.py` outputs `chapter1.html`; some EPUB spines use zero-padded names
