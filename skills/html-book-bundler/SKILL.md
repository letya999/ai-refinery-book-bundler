---
name: html-book-bundler
description: Converts book chapters (HTML, FB2, EPUB, OCR output) into a single self-contained offline HTML app with sidebar navigation, search, and rich visual components.
---

# HTML Book Bundler (v4.0)

Transforms raw chapter HTML files into a single `.html` file that works 100% offline with no external dependencies. The output is a mobile-first reading app: sidebar chapter list, search, progress bar, smooth transitions, and base64-encoded chapter content loaded in an isolated iframe.

## Architecture

```
chapters/*.html  →  bundle.cjs  →  book.html
                        ↓
               chapter_processor.cjs  (enrichment before base64)
                        ↓
               assets/theme.css       (shared styles injected into every chapter)
               templates/default.html (shell: sidebar + iframe + JS navigation)
```

### What the shell does
- Left sidebar: chapter list with search filter
- Top nav: prev/next buttons + chapter title + progress bar
- Chapter content loaded via `Blob URL` into a sandboxed `<iframe>`
- Reading position saved to `localStorage`
- Cross-chapter links intercepted via `postMessage` from iframe to shell

### What `chapter_processor.cjs` does (before base64 encoding)
Applied universally to every chapter regardless of source:

1. **`autoCollapseLongParas()`** — wraps `<p>` blocks > 480 chars in `<details class="long-para">` with a preview summary
2. **`autoInjectInsights()`** — extracts clean Cyrillic sentences (45-160 chars) from early paragraphs and injects them as `<blockquote class="insight">` pullquotes after the 4th and 10th `</p>`
3. **`styleFirstPara()`** — adds `class="lead-para"` to the first `<p>` for larger opening text
4. **Hero auto-generation** — if chapter has no `.wrap` container, generates one with kicker + h1 + lead from `<title>` and first `<p class="lead">`
5. **Shared theme injection** — `theme.css` is injected as a `<style>` block before the chapter's own styles (so chapter styles override theme via cascade)

### What `theme.css` provides
Base CSS variables, layout (`.wrap`, `.hero`, `.sec`), stats grid, card grid, accordion, translator, table, badge, scrollbar, responsive breakpoints, and styles for the universal enrichment components: `details.long-para`, `blockquote.insight`, `.lead-para`.

## Usage

### 1. Assemble a book from HTML chapters
```bash
node skills/html-book-bundler/scripts/bundle.cjs \
  --input ./chapters \
  --output my-book.html \
  --title "Book Name"
```

Chapters must be named `chapter1.html`, `chapter2.html`, ... (or any names that sort correctly). The bundler reads them in `localeCompare` numeric order.

A local `theme.css` in the chapters directory takes precedence over `assets/theme.css`.

### 2. Ingest from FB2 or EPUB
```bash
python skills/html-book-bundler/scripts/ingest.py \
  --input ./book.fb2 \
  --output ./chapters
```

Then run step 1.

### 3. From PDF (via OCR)
- Use Windows OCR (PowerShell) or any OCR tool to produce a JSON of `[{page, text}, ...]`
- Write a book-specific `convert_book.py` script that:
  - Defines chapter page ranges
  - Splits pages into chapters, cleans OCR artifacts
  - Calls `split_long_para()` to break page-per-paragraph OCR blobs at sentence boundaries
  - Adds per-chapter stats, callouts, and visual blocks (`CHAPTER_VISUALS` dict)
  - Writes styled `chapterN.html` files with full CSS
- Then run step 1

### 4. Audit the output
```bash
python skills/html-book-bundler/scripts/audit_single_file_html.py --file my-book.html
python skills/html-book-bundler/scripts/lint_book.py --file my-book.html
```

### 5. Run tests
```bash
node skills/html-book-bundler/tests/test_bundler.cjs
```

## Visual Components (CSS-only, no dependencies)

These are available in `theme.css` and can be used in chapter HTML:

| Class | Description |
|---|---|
| `.stats` / `.stat` | Stats grid with big number + label |
| `.card` / `.grid` | Card grid with hover lift |
| `.translator` | Two-column comparison (good/bad) |
| `.acc-item` / `.acc-head` / `.acc-body` | JS accordion |
| `blockquote.insight` | Pullquote with accent left border |
| `details.long-para` | Collapsible long paragraph |
| `.lead-para` | Larger opening paragraph |

### Chapter-specific visual types (for book scripts)

These are not in `theme.css` — add their CSS in the chapter's own `<style>` block:

| Type | Class | Use when |
|---|---|---|
| `red_flags` | `.red-flags`, `.rf-item`, `.rf-num` | Numbered warning list |
| `checklist` | `.checklist`, `.cl-item.yes/.no` | Yes/No comparison list |
| `timeline` | `.vis-timeline`, `.tl-step`, `.tl-arrow` | Sequential steps |
| `status_badge` | `.status-badge`, `.sb-icon/.sb-label/.sb-sub` | Single bold statement |
| `truth_scale` | `.truth-scale`, `.ts-col.myth/.reality` | Myth vs reality two columns |
| `compare_grid` | `.compare-grid`, `.cg-col.excuse/.truth` | Excuse vs truth two columns |

## Security

- **CSP**: `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:` — no external requests possible
- **iframe sandbox**: `allow-scripts allow-same-origin` — chapter content isolated
- **No external fonts, CDN, or network calls** — fully offline

## Lessons Learned (from this project)

### OCR-sourced text
- OCR output is one page = one paragraph. Call `split_long_para()` at sentence boundaries every ~600 chars before any classification
- Running book headers appear on every OCR page — strip them with regex before processing
- Q&A-structured books (excuse → letter → reply pattern) benefit from `_is_qa_para()` detection to separate intro narrative from Q&A sections
- Collapse the intro section (first 2 paras visible, rest in `<details>`) to reduce visual wall-of-text

### Visual variety
- Every chapter having the same visual type (e.g. always compare-grid) makes the book monotonous
- Use a `CHAPTER_VISUALS` dict mapping chapter index → visual type config
- Match visual type semantically: warnings → red_flags, cycles → timeline, binary judgements → status_badge
- Keep compare_grid only where the specific excuse vs. truth structure is the core message

### CSS injection architecture
- Inject `theme.css` as a `<style>` block BEFORE the chapter's own styles (inside `prepareChapter`, before base64 encoding)
- This ensures cascade works correctly: chapter styles override the base theme
- Do NOT inject CSS into the shell HTML after the fact — the iframe is sandboxed

### Sidebar scrolling with many chapters
- `.side` needs explicit `height: 100vh; overflow: hidden` for `.list { flex:1; overflow-y: auto }` to activate scrolling
- Without bounded parent height, `flex: 1` has no reference and overflow never kicks in
