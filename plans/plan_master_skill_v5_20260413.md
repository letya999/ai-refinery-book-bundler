# Master Plan: HTML Book Bundler v5.0
# Sources: 14-point list + 10 strategic questions + 3 research agents (GitHub, Context7, codebase audit)

---

## PHASE 1 — Critical Bug Fixes (correctness blockers)

### 1.1 `autoInjectInsights` — undefined injection
**File:** `skills/html-book-bundler/scripts/chapter_processor.cjs`
**Bug:** `candidates[1]` can be `undefined` if only one sentence found → writes `<p>undefined</p>` into HTML.
**Fix:** Guard with `if (quote)` before injection: `const quote = insertAt[pCount]; if (quote) return ...`

### 1.2 `bundle.cjs` — silent crash on missing args
**File:** `skills/html-book-bundler/scripts/bundle.cjs`
**Bug:** `args.indexOf('--input')` returns -1 when flag absent → `args[-1+1]` = `args[0]` → wrong path, no error.
**Fix:** Validate required args at startup; print usage and exit(1) if missing.
Add `--help` flag output:
```
Usage: node bundle.cjs --input <dir> --output <file.html> [--title "Title"] [--lang <code>]
```

### 1.3 `ingest.py` — output filenames break cross-chapter links
**File:** `skills/html-book-bundler/scripts/ingest.py`
**Bug:** Outputs `001.html`, `002.html` etc. But `chapter_processor.cjs` navScript builds chapterMap keyed on `chapter1.html`, `chapter2.html` — cross-chapter links from ingested books NEVER resolve.
**Fix:** Change ingest.py output to `chapter1.html`, `chapter2.html` pattern (or make navScript detect both patterns).

### 1.4 `ingest.py` EPUB — nav document included as chapter
**File:** `skills/html-book-bundler/scripts/ingest.py`
**Bug:** EPUB3 navigation document (`nav.xhtml` / `.ncx`) appears in manifest and is included as a visible chapter.
**Fix:** Skip items with `properties="nav"` and items with media-type `application/x-dtbncx+xml`.

### 1.5 `dev_server.cjs` — live-reload completely non-functional
**File:** `skills/html-book-bundler/scripts/dev_server.cjs`
**Bug:** SSE sends `reload` events to connected clients, but the built book HTML has no EventSource listener — browser never refreshes.
**Fix:** When in dev mode, inject a tiny `<script>new EventSource('/events').onmessage=()=>location.reload()</script>` at the end of the built HTML. Add `--dev` flag to `bundle.cjs` to enable this injection.

---

## PHASE 2 — Architecture Upgrade

### 2.1 Replace base64+Blob with `srcdoc`
**Files:** `bundle.cjs`, `chapter_processor.cjs`, `default.html`
**Research finding:** `iframe.srcdoc = htmlString` takes raw HTML, no encoding, no size inflation (+33% for base64), no Chrome 2MB iframe limit for data URIs, no Blob URL management. Directly supported offline.
**Change:**
- `chapter_processor.cjs`: return raw UTF-8 string instead of base64
- `bundle.cjs`: collect strings, JSON.stringify into `const CHAPTERS = [...]`
- `default.html` JS: `fr.srcdoc = CHAPTERS[i]` instead of base64 decode + Blob URL
- Remove all `URL.createObjectURL` / `URL.revokeObjectURL` logic
- Keep `CHAPTERS` variable name (replaces `B64`)
- Update `lint_book.py` and `test_bundler.cjs` to check for `CHAPTERS =`

### 2.2 MiniSearch full-text search
**Files:** `bundle.cjs`, `default.html`
**Research finding:** MiniSearch (7KB minified+gzip, zero deps) is best for offline books. Build inverted index at bundle time, serialize to JSON, embed as `const SEARCH_IDX = {...}`. Runtime: `MiniSearch.loadJSON(SEARCH_IDX)` — 0ms indexing delay.
**Change:**
- Download MiniSearch minified source, embed inline in `default.html` (or in a `vendor/` file inlined at build time)
- `bundle.cjs`: after collecting chapter texts, build MiniSearch index with fields `{title, body}`, serialize with `miniSearch.toJSON()`
- Remove 800-char truncated substring search
- `default.html`: replace current `IDX.filter()` with `miniSearch.search(query)` returning ranked results with excerpts
- Search results show chapter title + matched excerpt, not just chapter index

---

## PHASE 3 — Universal Language Support (i18n)

### 3.1 Externalize all Russian UI strings
**Files:** `default.html`, `chapter_processor.cjs`, `ingest.py`
**Problem (from audit):** 9+ hardcoded Russian strings throughout: "Глава", "← Назад", "Вперед →", "Загрузка...", "Всего X глав", "Поиск по книге...", `lang="ru"`, `html lang="ru"`.
**Fix:** Add `--lang` flag to `bundle.cjs` (default: `ru`). Load strings from a `lang/<code>.json` file:
```json
{
  "chapter": "Chapter",
  "prev": "← Back",
  "next": "Next →",
  "loading": "Loading...",
  "total_chapters": "{{n}} chapters",
  "search_placeholder": "Search...",
  "lang_attr": "en"
}
```
Create `lang/ru.json` and `lang/en.json`. Replace all hardcoded strings in `default.html` with `{{LANG_*}}` placeholders. `bundle.cjs` loads the JSON and does template replacement.

### 3.2 Fix Cyrillic-only filter in `autoInjectInsights`
**File:** `chapter_processor.cjs`
**Bug:** `isCleanText()` checks >72% Cyrillic chars — English books get zero insights.
**Fix:** Replace with universal text quality check: sentence length 45-200 chars, ≥70% word characters (letters + spaces), no HTML tags, not ALL_CAPS. Language-agnostic.

---

## PHASE 4 — Developer Experience

### 4.1 `package.json` with npm scripts
**File:** `skills/html-book-bundler/package.json` (new)
```json
{
  "name": "html-book-bundler",
  "version": "5.0.0",
  "description": "Bundles book chapters into a single offline-first HTML reading app",
  "main": "scripts/bundle.cjs",
  "scripts": {
    "build": "node scripts/bundle.cjs",
    "test": "node tests/test_bundler.cjs",
    "audit": "python scripts/audit_single_file_html.py --file",
    "lint": "python scripts/lint_book.py --file",
    "dev": "node scripts/dev_server.cjs",
    "ingest": "python scripts/ingest.py"
  },
  "engines": { "node": ">=18" }
}
```

### 4.2 `README.md` in skill root
**File:** `skills/html-book-bundler/README.md` (new)
Content:
- What it is (3 sentences)
- 3 quick-start examples (FB2→book, EPUB→book, chapters→book)
- Architecture diagram (text)
- All CLI flags documented
- Input format spec: what chapter HTML must contain
- How to add custom visual types
- How to run tests

### 4.3 `requirements.txt` for Python scripts
**File:** `skills/html-book-bundler/requirements.txt` (new)
```
PyMuPDF>=1.23.0   # extract_pdf_visuals.py
python-docx>=1.0.0  # ingest_docx.py (new in Phase 7)
```
Plus note that `ingest.py` (FB2/EPUB) uses stdlib only.

### 4.4 Connect `optimize_assets.py` to pipeline
**File:** `bundle.cjs`
**Fix:** Add `--optimize` flag. When set, run `python optimize_assets.py <inputDir>` before processing chapters. Document in README.

---

## PHASE 5 — CSS / Theme Quality

### 5.1 Unify CSS variable naming
**Files:** `default.html`, `theme.css`
**Bugs found:**
- Shell defines `--text: #eef5ff`, theme defines `--txt: #eef5ff` — same value, different names
- Shell `--line: #2c4d80`, theme `--line: #395f9d` — same name, different values
- `--panel`, `--panel2` defined in theme but never used (dead code)
**Fix:**
- Standardize to `--txt` everywhere (or document that shell and theme scopes are intentionally separate)
- Align `--line` values to `#395f9d` (theme wins, it's used more)
- Remove dead `--panel`, `--panel2` from theme `:root`

### 5.2 Replace hardcoded colors with CSS variables in theme.css
**File:** `theme.css`
**Bugs found (from audit):** `.sec`, `.acc-item`, `.panel`, `.stat-box`, `.matrix` all use hardcoded hex values instead of `var(--line)`.
**Fix:** Replace all `#2e4f84`, `#345790`, `#3b619f`, `#3f66a6`, `#4066a5`, `#4a71b3`, `#597db8` occurrences with `var(--line)` where appropriate.

### 5.3 Add `ch` units for line length
**File:** `theme.css`
**Research finding:** `ch` units (65-75ch) give optimal reading line length on any screen.
**Fix:** Add to `.wrap p` / `.content-body p`: `max-width: 72ch`. This replaces the current max-width px approach for text.

### 5.4 Add `env(safe-area-inset-*)` for mobile notch
**File:** `theme.css`, `default.html`
**Fix:** Add to `.main` padding: `padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)`.

---

## PHASE 6 — Reading UX Improvements

### 6.1 Scroll position persistence
**File:** `default.html`
**Research finding:** Save `{ chapterIdx, scrollRatio }` on `scrollend` event (or `visibilitychange` as fallback).
**Fix:**
- In the `go()` function: after iframe loads, restore scroll: `fr.contentWindow.scrollTo(0, savedRatio * fr.contentDocument.body.scrollHeight)`
- Add `message` listener in iframe content (navScript) that reports scroll ratio back to shell on `scrollend`
- `localStorage` key: `scroll_${BOOK_ID}_${i}` per chapter

### 6.2 Light/dark theme toggle
**File:** `default.html`, `theme.css`
**Fix:**
- Add sun/moon toggle button in `.top` bar
- `theme.css`: add `@media (prefers-color-scheme: light) { :root { --bg: #f0f4f8; --txt: #1a2535; ... } }`
- Manual toggle overrides via `[data-theme="light"]` on `<html>`
- Save preference to `localStorage.setItem('theme', 'light'|'dark')`

### 6.3 Bookmarks system
**File:** `default.html`
**Fix:**
- Add bookmark button (★) in `.top` bar
- Bookmarks stored as `bookmarks_${BOOK_ID}` array in localStorage: `[{chapterIdx, scrollRatio, label, timestamp}]`
- Bookmarks panel accessible from sidebar (collapsible section below chapter list)
- Click bookmark → go(chapterIdx) + restore scroll

---

## PHASE 7 — Ingest Quality

### 7.1 Fix FB2 ingest
**File:** `ingest.py`
**Fixes:**
- Handle nested `<section>` recursively (not just direct children of body)
- Preserve inline formatting: `<strong>` → `<b>`, `<emphasis>` → `<em>`, `<strikethrough>` → `<s>`
- Handle `<epigraph>` as `<blockquote>`, `<poem>/<stanza>/<v>` as `<pre>` with styling
- Handle `.fb2.zip` (decompress before parsing)
- Handle `<annotation>` as chapter lead paragraph

### 7.2 Fix EPUB ingest
**File:** `ingest.py`
**Fixes:**
- Skip nav documents: check `properties="nav"` or media-type `application/x-dtbncx+xml`
- Fix asset path resolution: use `urllib.parse.urljoin(base_path, m_href)` instead of hardcoded string replace
- Handle encoding fallback: try UTF-8, fallback to latin-1
- Fix zip path join to use `posixpath.join` not `os.path.join`

### 7.3 Add DOCX support
**File:** `ingest.py` (extend) or `ingest_docx.py` (new)
**Requires:** `python-docx`
**Logic:**
- Read paragraphs, detect heading styles (Heading 1/2) as chapter boundaries
- Convert runs with bold/italic/underline to HTML equivalents
- Extract images as base64 data URIs inline
- Output same `chapter1.html`, `chapter2.html` format

---

## PHASE 8 — Examples & Documentation

### 8.1 `examples/` directory
**Files:** `skills/html-book-bundler/examples/` (new dir)
Contents:
- `sample_book/chapter1.html` — rich chapter showing all visual components
- `sample_book/chapter2.html` — chapter with timeline + red_flags
- `sample_book/chapter3.html` — chapter with checklist + status_badge
- `sample_book/theme.css` — custom theme override example
- `sample_book.html` — pre-built output (run `npm run build -- --input examples/sample_book --output examples/sample_book.html`)

### 8.2 Visual showcase
**File:** `examples/visual_showcase.html` (new, standalone, pre-built)
Single HTML showing every CSS component from theme.css live: stats grid, cards, translator, accordion, blockquote.insight, details.long-para, red-flags, checklist, timeline, status-badge, truth-scale, compare-grid.
Purpose: designers can open it to see all components without running the pipeline.

### 8.3 Update reference files
**Files:** `references/advanced-system-features.md`, `references/single-file-architecture.md`
- `advanced-system-features.md`: remove superseded CSS runtime injection section; update search section to document MiniSearch approach; fix missing section 4
- `single-file-architecture.md`: update to reflect srcdoc architecture

### 8.4 `INPUT_SPEC.md`
**File:** `skills/html-book-bundler/INPUT_SPEC.md` (new)
Documents what a valid input chapter HTML must/can contain:
- Required: valid HTML with `<title>` or `<h1>` (one of them)
- Optional: `<p class="lead">` for hero subtitle, `<style>` block for chapter-specific CSS
- Optional: `class="hero"` section, `class="wrap"` container (auto-generated if absent)
- Image references: relative paths to assets in same directory (auto-inlined by bundler)
- Cross-chapter links: `href="chapter3.html"` or `href="chapter3.html#anchor"` (intercepted by navScript)

---

## PHASE 9 — Advanced Features

### 9.1 Exclusive accordions with `details[name]`
**File:** `theme.css`, `SKILL.md`
**Research finding:** Chrome 120+, Firefox 130+, Safari 17.2+ support `<details name="group">` for exclusive accordion groups (only one open at a time), zero JS.
**Fix:** Add `.acc-exclusive` wrapper pattern to theme.css docs + example in visual_showcase. No JS accordion needed for modern browsers.

### 9.2 Auto visual type detection
**File:** `chapter_processor.cjs` or new `scripts/visual_classifier.py`
**Logic:** Analyze paragraph content for keywords/patterns:
- Multiple "Если/If..." sentences → suggest `red_flags`
- Pairs of contrasting statements → suggest `truth_scale` or `compare_grid`
- Numbered steps or temporal sequence → suggest `timeline`
- Lists with ✓/✗ or "should/shouldn't" → suggest `checklist`
Output: `CHAPTER_VISUALS` dict suggestion written to stdout for human review. Not auto-applied — helps book author.

### 9.3 Book versioning in localStorage
**File:** `default.html`, `bundle.cjs`
**Fix:** At build time, compute a short hash of all chapter content (e.g. first 200 chars of each). Embed as `BOOK_VERSION`. localStorage key becomes `prog_${BOOK_ID}_${BOOK_VERSION}`. If version changes, old progress is ignored (book updated) — user starts fresh or is prompted.

### 9.4 Image size warning in bundler
**File:** `bundle.cjs`
**Fix:** After `bundleAssets()`, check total base64 image size. Warn if any chapter > 500KB of image data:
```
Warning: chapter3.html has 1.2MB of embedded images. Run --optimize to compress.
```

### 9.5 Playwright visual regression tests
**File:** `tests/visual_regression.spec.js` (new)
**Requires:** Playwright
**Tests:**
- Open sample_book.html in browser
- Screenshot first chapter → compare to baseline
- Verify sidebar has correct chapter count
- Verify search returns result for known keyword
- Verify prev/next navigation works
- Verify progress saved to localStorage after navigation
- Mobile viewport: verify sidebar off-canvas behavior

---

## Implementation Priority Order

| Phase | Priority | Complexity | Impact |
|---|---|---|---|
| Phase 1 (bug fixes) | P0 — do first | Low | Fixes silent corruption |
| Phase 3.2 (Cyrillic filter) | P0 — do first | Low | Fixes English books |
| Phase 4.1 package.json | P1 | Low | AI tool compatibility |
| Phase 4.2 README | P1 | Low | AI tool compatibility |
| Phase 2.1 srcdoc | P1 | Medium | Removes 2MB limit, simplifies code |
| Phase 5.1-5.2 CSS vars | P1 | Low | Theme consistency |
| Phase 6.1 scroll persist | P2 | Medium | Reading UX |
| Phase 4.3 requirements.txt | P2 | Low | Python deps clarity |
| Phase 7.1-7.2 FB2/EPUB fix | P2 | Medium | Ingest quality |
| Phase 2.2 MiniSearch | P2 | Medium | Real full-text search |
| Phase 8.1-8.2 examples | P2 | Medium | Discoverability |
| Phase 6.2 dark/light toggle | P3 | Medium | UX polish |
| Phase 5.3-5.4 ch/safe-area | P3 | Low | Typography |
| Phase 6.3 bookmarks | P3 | Medium | Power reader feature |
| Phase 7.3 DOCX | P3 | High | New format |
| Phase 9.1 exclusive accordions | P3 | Low | Modern CSS |
| Phase 9.2 auto visual type | P4 | High | AI-assisted authoring |
| Phase 9.3 versioning | P4 | Low | Edge case |
| Phase 9.4 image warning | P4 | Low | DX improvement |
| Phase 9.5 Playwright tests | P4 | High | Visual QA |
| Phase 4.4 dev server fix | P4 | Medium | DX only |

---

## Files to Create/Modify Summary

**Modified:**
- `skills/html-book-bundler/scripts/bundle.cjs` — args validation, srcdoc, MiniSearch index build, --dev, --optimize, --lang, image warning
- `skills/html-book-bundler/scripts/chapter_processor.cjs` — fix undefined injection, fix Cyrillic filter, srcdoc return
- `skills/html-book-bundler/scripts/ingest.py` — filename fix, FB2/EPUB quality fixes, DOCX
- `skills/html-book-bundler/scripts/dev_server.cjs` — inject EventSource reload script
- `skills/html-book-bundler/scripts/lint_book.py` — check for CHAPTERS= instead of B64=
- `skills/html-book-bundler/templates/default.html` — srcdoc, MiniSearch runtime, i18n placeholders, scroll persist, theme toggle, bookmarks
- `skills/html-book-bundler/assets/theme.css` — CSS var unification, ch units, safe-area, light theme
- `skills/html-book-bundler/tests/test_bundler.cjs` — update checks for srcdoc, add 10+ chapter sort test
- `skills/html-book-bundler/SKILL.md` — update to v5.0
- `skills/html-book-bundler/references/advanced-system-features.md` — fix superseded sections

**Created:**
- `skills/html-book-bundler/package.json`
- `skills/html-book-bundler/README.md`
- `skills/html-book-bundler/requirements.txt`
- `skills/html-book-bundler/INPUT_SPEC.md`
- `skills/html-book-bundler/lang/ru.json`
- `skills/html-book-bundler/lang/en.json`
- `skills/html-book-bundler/examples/sample_book/chapter1.html`
- `skills/html-book-bundler/examples/sample_book/chapter2.html`
- `skills/html-book-bundler/examples/sample_book/chapter3.html`
- `skills/html-book-bundler/examples/visual_showcase.html`
- `skills/html-book-bundler/INPUT_SPEC.md`
- `skills/html-book-bundler/tests/visual_regression.spec.js`
- `skills/html-book-bundler/scripts/visual_classifier.py`
