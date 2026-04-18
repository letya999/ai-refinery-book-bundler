---
name: html-book-bundler
description: Master Skill Bundle (v8.3). A 4-role pipeline (Ingest, Architect, Design, Assemble) for creating offline-first interactive books.
---

# HTML Book Bundler (Skill Bundle v8.3)

This is the umbrella skill for the book production toolchain. It manages 4 specialized sub-skills for each layer of production.

## Components (Sub-skills):
1. **book-ingester:** Unified extraction from PDF, EPUB, FB2, DOCX (including images).
2. **book-architect:** Semantic distillation, `terms.json` mining, and visual blueprinting.
3. **book-designer:** AST-based enrichment, high-fidelity SVGs, and contrast enforcement.
4. **book-assembler:** Final bundling with stable MD5 indexing and security audit.

## Shared Mantras:
- **Zero Hex Colors:** SVGs must be theme-adaptive via CSS variables.
- **Variables Contract:** Both the shell (`default.html`) and chapters (`theme.css`) MUST use identical CSS variable names (`--bg`, `--txt`, `--acc`, `--acc2`, `--line`, `--muted`, `--warn`, `--bad`, `--bg2`, `--fg`, `--panel`, `--panel2`) to ensure seamless visual integration.
- **Stable Identity:** `BOOK_ID` is derived from the book title (MD5 hash). Changing the `--title` resets user progress; changing the output filename does NOT.
- **Cheerio over Regex:** All structural HTML modifications MUST use Cheerio AST parsing for reliability.
- **Mobile First:** All output must be responsive, respect safe-area-insets, and allow pinch-to-zoom (WCAG 1.4.4).

## Critical Lessons (2026-04-17):
- **Sandbox Resolution (FIXED in v8.3):** The iframe now uses ONLY `allow-scripts` — `allow-same-origin` has been removed. All shell/chapter communication is done via `postMessage` (theme, scroll, anchors, search, asset loading). Never reintroduce `allow-same-origin`; never call `window.parent.document` from chapter JS. The CSP `connect-src: none` remains as a defense-in-depth layer.
- **Base64 Bloat:** Limit image width to 1000px in `optimize_assets.py` to prevent mobile browser OOM crashes. The function default AND the CLI default MUST both be 1000 — verify if changing either.
- **EPUB Navigation:** Regex path rewriting must skip `.html`/`.xhtml`/`#` to preserve inter-chapter links.
- **PDF Extraction:** Use dynamic font baseline calculation (`_calculate_baseline`) for relative heading detection (Pocket vs A4 formats). Without `--pdf-chapters`, the entire PDF becomes ONE chapter.
- **Data-URI Memory Management:** Injecting hundreds of megabytes of Base64 strings directly into the DOM crashes mobile Safari. Move assets to a JSON dictionary and lazy load them via `IntersectionObserver` in the guest script.
- **Standard API over Browser Hacks:** Relying on `window.find()` creates inconsistent search UI and doesn't allow scrolling through multiple hits per chapter. Custom `TreeWalker` highlighting (`<mark>`) is the correct approach.
- **Hardcoded Logic Breaks i18n:** Stop words for inverted indices should not be hardcoded in the bundler. They are language-specific and must be loaded dynamically from `lang/*.json` files.
- **QA Linter Hex Expansion:** Linter checking SVGs for hardcoded hex codes must support 8-character codes (`#RRGGBBAA`) exported by Figma, not just 3 or 6 characters.
- **Text-to-HTML XSS:** When converting list items to stat cards or grid cards, always HTML-escape `.text()` values before interpolating into template literals. Cheerio `.text()` decodes entities — re-injecting them raw creates broken HTML.
- **Sub-skill SKILL.md must be self-contained:** Each role's SKILL.md is the full context for the AI agent executing that role. Never put critical lessons only in the umbrella SKILL.md — the sub-agent won't see it.

## Critical Lessons (2026-04-18, audit session):
- **Search Highlighting vs Tag Boundaries:** Simple text-node search fails on formatted words (e.g., `<b>W</b>ord`). Use a virtual text buffer + DOM mapping to ensure robust search across tag boundaries.
- **Scanned PDF Validation:** Always check the total extracted text length. If 0, warn the user explicitly about "Scanned PDF" to prevent confusion over empty outputs.
- **Unified JSON Injection:** Use a dedicated `safeJsonInject` helper for all JSON blobs in the template. This centralizes `</script>` escaping and prevents breaking the output file with embedded code examples.
- **Theme Variable Integrity:** Validate the presence of mandatory CSS variables (`--bg`, `--acc`, etc.) during bundling. This prevents a "broken UI" experience when a custom theme is incomplete.
- **`guestReady` is the only safe sync point:** Never send `setTheme`, `setScrollRatio`, or `highlightSearch` from `iframe.onload`. The `onload` event fires before the guest script runs. Always wait for `{action:'guestReady'}` from the guest before sending any postMessage commands.

## Critical Lessons (2026-04-18, second audit):
- **CSS must stay synchronized between `default.html` and `theme.css`:** Both files define the same visual layer (shell sidebar and chapter iframe). Whenever you update `font-family`, antialiasing, or any global CSS in `default.html`, make the identical change in `theme.css`. The comment `/* Matches default.html shell font — always keep these in sync */` marks the critical line.
- **EPUB `ingest_epub()` must receive `--lang`:** `ingest_epub()` previously lacked a `lang` parameter, causing chapters to inherit whatever lang was in the EPUB source (often wrong for localized EPUB editions). Always pass `lang` through to `ingest_epub()` and inject it into each chapter's `<html>` tag if missing.
- **navScript regexes require double-double escaping:** JS regex patterns inside CJS template literals need `\\\\d` for `\d`, `\\\\.` for `\.`, etc. Each backslash is doubled twice (once for the JS string literal, once for the regex engine). Do **not** edit navScript regex patterns without understanding this — one extra or missing slash silently breaks chapter navigation mapping.
- **Tests and linter must cover SEARCH_IDX:** Having tests only for CHAPTERS+ASSETS escaping is insufficient. Added Test 21 (SIDX structure + escaping) and a `lint_book.py` SIDX validation. Without both, a broken SIDX disables all search with no visible error.
- **`@media print` is fundamentally broken for iframes:** iframe content does not render in browser print layout. Replaced phantom print CSS with a `print-btn` that calls `window.open()` and restores lazy images from ASSETS before printing. The new popup prints correctly.
- **`wrap()` in Cheerio uses the innermost child:** `$p.wrap($details)` inserted `$p` _inside_ `<summary>` (the only child of `$details`), not after it. Use `$p.replaceWith($details); $details.append($p)` to get the correct sibling structure.
- **`dev_server.cjs` must exist if `--dev` is documented:** The `--dev` flag injects an SSE live-reload client. `dev_server.cjs` is the matching server. Added a minimal stdlib-only implementation in `scripts/dev_server.cjs`.

## Usage:
Refer to the individual SKILL.md in subdirectories for role-specific instructions.
