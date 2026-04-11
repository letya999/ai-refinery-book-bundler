---
name: html-book-bundler
description: Engineering self-contained, interactive HTML books with sandboxed chapter isolation, automated integrity linting, and actionable data governance.
---

# HTML Book Bundler

Expert skill for transforming linear manuscripts into professional-grade, interactive single-file HTML applications. Focuses on isolative architecture, automated quality assurance, and cognitive-load-reducing visual patterns.

## 1. Core Architecture (The Three-Tier Model)

### A. The Shell (Application Layer)
- **Responsibility:** Navigation, State Persistence, UI/UX Chrome.
- **State Management:** MUST use `localStorage` to persist `currentChapterIndex` and analytical state.
- **Progress Tracking:** Mandatory visual progress indicator.

### B. The Sandbox (Chapter Layer)
- **Isolation:** Each chapter MUST be rendered via a Blob URL inside an `<iframe>`.
- **Scope Safety:** Zero CSS/JS leakage. 
- **Memory Management:** MUST call `URL.revokeObjectURL()` on navigation.

### C. The Asset Payload (Data Layer)
- **Zero-Dependency:** All assets MUST be bundled. External URLs are a Hard Fail.
- **Base64 Packaging:** Chapters stored as encoded strings.

## 2. Automated Quality Assurance (Linter)

Every build MUST be validated using the `lint_book.py` utility.

### Critical Checks (Errors):
- **External Links:** Any `http(s)` URL in `src` or `href` (except explicitly allowed Shell links).
- **Charset:** Missing `<meta charset="utf-8">` in any chapter.
- **Data Integrity:** Checkboxes/Checklists missing unique `id` attributes (breaks persistence).
- **Encoding:** Base64 corruption or decoding failures.

### Performance & UX Checks (Warnings):
- **Asset Size:** Chapters > 1MB or total file > 15MB.
- **Memory:** Missing `revokeObjectURL` call.
- **A11y:** Images missing `alt` text or missing `prefers-reduced-motion` support.
- **UX:** Missing `localStorage` persistence logic.

## 3. Engineering Quality Gate (Mandatory)

Before delivery, the engineer MUST run:
```bash
python skills/html-book-bundler/scripts/lint_book.py --file ./output.html
```
**A result with any [X] ERRORS is rejected.**

## 4. Workflows

### Scenario: Bundling & Linting
```bash
node skills/html-book-bundler/scripts/bundle.cjs --input ./chapters --output my-book.html
python skills/html-book-bundler/scripts/lint_book.py --file ./my-book.html
```

### Scenario: Asset Optimization
*Before bundling, ensure images are resized and compressed. Use `extract_pdf_visuals.py` at high DPI only for critical diagrams.*

## 5. Visual & Analytical Strategy
- **Backgrounds:** `Twinkle Stars`, `Structured Grid`, `Ambient Pulse`.
- **Content:** `Translator Pattern`, `Persistent Checklists`, `Decision Engines`.
- **Viz Bank:** `Ishikawa`, `Mini-Gantt`, `Radar Charts`, `Logic Trees`.

## 6. Relevant References
- `references/interactive-visual-patterns.md`
- `references/visual-bank.md`
- `references/data-and-decision-visuals.md`
- `references/advanced-system-features.md`
- `references/pdf-visual-workflow.md`
- `references/single-file-architecture.md`
