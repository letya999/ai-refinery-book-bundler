---
name: html-book-bundler
description: Master Skill Bundle (v8.0). A 4-role pipeline (Ingest, Architect, Design, Assemble) for creating offline-first interactive books.
---

# HTML Book Bundler (Skill Bundle v8.0)

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

## Usage:
Refer to the individual SKILL.md in subdirectories for role-specific instructions.
