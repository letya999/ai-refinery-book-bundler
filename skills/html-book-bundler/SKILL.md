---
name: html-book-bundler
description: Master Skill Bundle (v8.2). A 4-role pipeline (Ingest, Architect, Design, Assemble) for creating offline-first interactive books.
---

# HTML Book Bundler (Skill Bundle v8.2)

This is the umbrella skill for the book production toolchain. It manages 4 specialized sub-skills for each layer of production.

## Components (Sub-skills):
1. **book-ingester:** OCR cleanup and structural extraction.
2. **book-architect:** Semantic analysis, glossary mining, and visual blueprinting.
3. **book-designer:** SVG authoring, CSS enrichment, and contrast enforcement.
4. **book-assembler:** Final bundling, QA, and security linting.

## Shared Mantras:
- **In-place Workflow:** Always edit files in the target book directory. No complex subfolder hierarchies.
- **Zero Hex Colors:** SVGs must be theme-adaptive via CSS variables.
- **Variables Contract:** Both the shell (`default.html`) and chapters (`theme.css`) MUST use identical CSS variable names (`--bg`, `--txt`, `--acc`, `--acc2`, `--line`, `--muted`, `--warn`, `--bad`, `--bg2`, `--fg`, `--panel`, `--panel2`) to ensure seamless visual integration.
- **Mobile First:** All output must be responsive and respect safe-area-insets.
- **Linter Enforcement:** `lint_book.py` will fail on hex colors in SVG and warn on "Wall of Text" (long chapters without `vis-` components).

## Lessons Learned (2026-04-15):
- SVG links inside `<text>` are invalid.
- Fan-out arrows need "trunk and branch" pattern.
- Arrowheads require `<defs>` and `marker-end`.
- Glossary links require explicit file registration (fixed in v8.0).
- Anchor navigation bypasses scroll restoration (fixed in v8.0).

## Lessons Learned (2026-04-17):
- **STOP_WORDS JS bug:** `.split()` chain must be wrapped in `()` when building from concatenated string literals — operator precedence calls `.split()` only on the last literal otherwise.
- **Python raw string quotes:** In `r'...'` strings, an unescaped `'` inside `[^"']` terminates the raw string. Use `r"""..."""` triple quotes or escape as `[^"\'` for character classes containing single quotes.
- **langCode propagation:** `prepareChapter` receives `langCode` but had no access to LANG object for hero block generation. Chapter-level i18n strings must be derived from `langCode` directly or LANG must be passed down.
- **`user-scalable=no` is WCAG 1.4.4 violation:** Never disable pinch-to-zoom; users with low vision need it.
- **EPUB CSS via data URI href doesn't work:** Browsers ignore `<link href="data:text/css;base64,...">` as stylesheets. CSS must be inlined as `<style>` blocks.
- **Non-existent files in README:** Always verify all referenced filenames exist before committing documentation.

## Lessons Learned (2026-04-17, v8.1):
- **`const` vs `let` for fallback vars:** Any variable that gets a default-fallback assignment (e.g. unsupported lang) must be declared `let`, not `const`. A `const` reassignment in strict mode throws TypeError silently during error handling.
- **`bundleAssets` must skip `.html` files:** Inlining `<a href="chapter2.html">` as a base64 data URI breaks inter-chapter navigation — navScript bails early on `data:` hrefs. Only inline images/fonts/CSS.
- **EPUB `<link>` attribute order:** HTML attribute order is arbitrary. Regex that assumes `rel=` before `href=` misses most real EPUB files. Match the whole `<link>` tag, then extract each attribute with a separate `re.search()`.
- **Light mode rgba backgrounds:** `rgba(15,31,56,.4)` is invisible on dark but creates dark patches on light backgrounds. Always add `[data-theme="light"]` overrides for any element using hardcoded dark rgba values.
- **Define helper functions outside loops:** Python functions redefined on every loop iteration cause confusing closure behavior (late binding). Move them above the loop with explicit parameters.

## Lessons Learned (2026-04-17, v8.2 audit):
1. **DOCX images are `InlineShape` objects, not paragraphs** — `doc.paragraphs` iteration silently skips all embedded images. Always check `doc.inline_shapes` count and warn.
2. **Always `html.escape()` ALL config-sourced strings going into HTML** — including chapter titles, not just extracted body content.
3. **`chapterWord` i18n** — never use hardcoded language ternaries; always route through the LANG object so new languages work automatically.
4. **FB2/DOCX ingesters must emit `lang` attribute on `<html>`** — inconsistency with `pdf_parser_general.py` was a silent a11y violation.
5. **`theme.css` hero override must exist in both `[data-theme]` AND `@media (prefers-color-scheme)`** — the OS preference fallback and the explicit toggle are two separate CSS paths.
6. **Linter must enforce `viewBox` on all SVGs** — a designer rule without linter enforcement is an honor system, not a rule.
7. **Search index must be built before `bundleAssets`:** building from post-base64 content floods the SIDX with noise tokens from data URIs.
8. **`bundleAssets` must skip `.css` — use `inlineStylesheets()` instead:** browsers ignore `<link href="data:application/octet-stream;...">` as stylesheets; CSS must be inlined as `<style>` blocks.
9. **`el_to_html` tail text must be HTML-escaped:** FB2 XML element tail text is auto-decoded by the parser; forgetting `escape_html(tail)` is a silent XSS vector.
10. **`LANG.dir` was a dead field:** now wired to `dir="{{LANG_DIR}}"` on the shell `<html>` element — RTL books work correctly.
11. **`autoEnrichLists` must skip `<ol>` entirely:** ordered lists have sequence semantics that card grids destroy.
12. **Keep output filename stable:** the base name becomes the localStorage key prefix (`BOOK_ID`). Renaming the output file silently resets all bookmarks and reading position.

## AUDIT TRAIL

### Open
_(none — all known issues resolved in v8.2 audit pass)_

### Resolved (2026-04-17)
- `[CRIT]` Search index poisoned by base64 — `bundle.cjs:chapterTexts` now extracted before `bundleAssets`
- `[CRIT]` CSS `<link>` silently broken by bundleAssets — added `.css` skip + `inlineStylesheets()` function
- `[CRIT]` FB2 tail text XSS — all `el_to_html` returns now call `escape_html(tail)`
- `[CRIT]` `LANG.dir` dead field — wired to `{{LANG_DIR}}` template placeholder
- `[SIG]`  `autoEnrichLists` converts `<ol>` — now skipped; also skips already-classed lists
- `[SIG]`  `dev_server.cjs --port` NaN — validates range 1-65535 and exits with error
- `[BUG]`  Duplicate `document.getElementById('search')` — now uses `searchEl`
- `[BUG]`  `document.documentElement.lang` set twice — removed JS duplicate (template handles it)
- `[BUG]`  `styleFirstPara` ignores single-quoted class attributes — regex now handles both quote styles
- `[DEAD]` `"loading"` key in lang JSONs — removed from `en.json` and `ru.json`
- `[DOC]`  Version mismatch across files — all sub-skills, README, package.json bumped to v8.1
- `[DOC]`  `--skip-insights` risk of duplicate pullquotes — documented in assembler SKILL.md
- `[DOC]`  `bookId` → localStorage coupling — documented in assembler SKILL.md
- `[AUDIT v8.2]` Version string in --help → fixed in `bundle.cjs` (v8.2)
- `[AUDIT v8.2]` Expand Russian/English stop words → fixed in `bundle.cjs`
- `[AUDIT v8.2]` `chapterWord` hardcoded ternary → replaced with `chapterLabel` parameter in `chapter_processor.cjs` and passed from `bundle.cjs` via i18n JSON
- `[AUDIT v8.2]` Unescaped title in `pdf_parser_general.py` → title now escaped in `<title>` and `<h1>`
- `[AUDIT v8.2]` Missing `lang` attribute in FB2/DOCX output → now emitted from `ingest.py`
- `[AUDIT v8.2]` Support for `.doc` binary → explicitly blocked in `ingest.py` with helpful error
- `[AUDIT v8.2]` Silent skip of images in DOCX → warning now printed if `inline_shapes` detected
- `[AUDIT v8.2]` Linter: Missing `viewBox` in SVG → check added to `lint_book.py`
- `[AUDIT v8.2]` Linter: `user-scalable=no` check → check added to `lint_book.py`
- `[AUDIT v8.2]` Linter: Extended SVG hex check → now catches `stop-color`, `flood-color`, `lighting-color`
- `[AUDIT v8.2]` `theme.css` hero background inconsistency → added override in `@media (prefers-color-scheme: light)`
- `[AUDIT v8.2]` Shell: origin validation in bridge → added `e.source !== fr.contentWindow` check in `default.html`
- `[AUDIT v8.2]` Shell: legacy `blob:` in CSP → removed from `default.html`

## References:
See `references/` directory for 8 architectural docs covering architecture, shell JS API, theming, security, search, i18n, and deployment.

## Usage:
Refer to the individual SKILL.md in subdirectories for role-specific instructions.
