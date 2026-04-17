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
- **Sandbox Paradox:** `allow-scripts` + `allow-same-origin` = RCE Risk. All communication between shell and book must be via `postMessage`.
- **Base64 Bloat:** Limit image width to 1000px in `optimize_assets.py` to prevent mobile browser OOM crashes.
- **EPUB Navigation:** Regex path rewriting must skip `.html` and `#` to preserve inter-chapter links.
- **PDF Extraction:** Use dynamic font baseline calculation (`_calculate_baseline`) for relative heading detection (Pocket vs A4 formats).

## Usage:
Refer to the individual SKILL.md in subdirectories for role-specific instructions.
