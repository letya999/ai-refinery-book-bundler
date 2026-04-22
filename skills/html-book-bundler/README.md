# HTML Book Bundler v9.0 "Director's Cut"

A high-fidelity AI production pipeline designed to transform raw manuscripts (PDF, EPUB, FB2, DOCX) into interactive, offline-first "Masterpiece" reading applications. 

This framework moves beyond simple file concatenation into a structured **refinery process** where content is cleaned, architected, enriched, and audited.

---

## 🚀 The Vision: From Raw Data to High-Fidelity UI

The goal is to produce a single, portable HTML file that feels like a modern web app but remains 100% functional without a server or internet connection.

*   **Source Example:** `Грубер Мартин. Понимание SQL - royallib.com.epub` (Raw technical text).
*   **Result Example:** [outputs/ne_uslozhnyay/ne-uslozhnyay-preview-book.html](outputs/ne_uslozhnyay/ne-uslozhnyay-preview-book.html) (Interactive high-fidelity output).

---

## 🏗 The Four Horsemen: Role-Based Pipeline

The production is divided into four specialized AI-agent phases, each governed by its own logic:

### 1. Ingester (The Purifier)
*   **Mission:** Deep extraction and artifact removal.
*   **Logic:** Strips PDF headers/footers, decodes FB2 entities, and maps the physical topology.
*   **Skill:** `book-ingester`. Uses `ingest.py` and `pdf_parser_general.py`.

### 2. Architect (The Visionary)
*   **Mission:** Semantic distillation and storyboarding.
*   **Logic:** Analyzes the book's "vibe" to create a **Director's Note**. It plans which sections become interactive and which patterns from the `visual-bank.md` to apply.
*   **Skill:** `book-architect`.

### 3. Designer (The Craftsman)
*   **Mission:** AST-based enrichment and UI injection.
*   **Logic:** Uses `chapter_processor.cjs` to wrap prose in rich components:
    *   **Technical logic** → `.formula-card`
    *   **Data comparisons** → `.grid` with `.card`
    *   **Logic flows** → Theme-adaptive SVGs.
*   **Skill:** `book-designer`.

### 4. Assembler (The Auditor)
*   **Mission:** Final bundling and high-stakes verification.
*   **Logic:** Generates the `SIDX` search index, manages asset deduplication, and runs the **Interactive Audit Protocol** via Playwright.
*   **Skill:** `book-assembler`.

---

## 📜 The Quality Manifesto (Mandates)

To reach "Director's Cut" status, every book must pass these gates:

1.  **Rule 70/30 (The Engagement Gate):** At least 70% of the reading flow must consist of structured/visual components (cards, tables, diagrams). Max 30% plain prose.
2.  **Zero Hex Colors:** All components must use CSS variables (`--bg`, `--acc`, etc.). Hardcoded hex codes are a failure.
3.  **Scoped CSS Rule:** Chapter styles must be scoped under `.chapter-content` to prevent breaking the reader's UI.
4.  **Scroll Guard:** Iframe environments are tricky. Every chapter must explicitly handle `overflow-y: auto !important` to ensure responsiveness.
5.  **2MB OOM Mitigation:** To prevent crashes on mobile Safari, chapters exceeding 2MB are automatically split into logical "Chunks" (e.g., Chapter 1.1, 1.2).

---

## 🛠 Technical Architecture & Deep Dive

*   **Security (Sandbox):** Chapters run in `iframe.srcdoc` with a strict `sandbox="allow-scripts"` policy. The `allow-same-origin` flag is intentionally omitted for defense-in-depth.
*   **Communication:** All shell↔chapter interaction (theme, scroll, search hits) is handled via a robust `postMessage` protocol.
*   **Asset Management:** Images are optimized to 1000px, stored in a deduplicated `ASSETS` JSON dictionary, and lazy-loaded via `IntersectionObserver`.
*   **Search Engine:** A build-time inverted index (`SIDX`) with prefix matching and AND-intersection logic. No external dependencies.

---

## 🏁 AI Agent Quick Start

If you are an AI agent assigned to this task, follow this loop:

```bash
# Phase 1: Ingest
python scripts/ingest.py --input "book.epub" --output ./chapters

# Phase 2: Design (Automated Enrichment)
# The designer sub-agent will use chapter_processor.cjs for AST modifications

# Phase 3: Bundle
node scripts/bundle.cjs --input ./chapters --output book.html --title "Masterpiece Edition"

# Phase 4: Audit (Mandatory)
# Run tests to ensure CSP and Search integrity
node tests/test_bundler.cjs
```

---

## 📂 Project Structure

*   `scripts/` — The engine (Bundler, Ingesters, Linters, Dev Server).
*   `templates/default.html` — The battle-tested interactive shell.
*   `assets/theme.css` — The shared visual contract (Dark/Light).
*   `skills/` — Self-contained context for sub-agents (Architect, Designer, etc.).
*   `lang/` — i18n support for UI strings and search stop-words.

---
*Documentation updated April 22, 2026. Standardized for Skill Bundle v9.0.*
