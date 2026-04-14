---
name: html-book-bundler
description: The ultimate AI-driven book compiler. Converts raw source files into a semantically enriched, visually engaging single-file HTML app. Implements a strict pipeline: Text Extraction -> Theme Ideation -> Visual Planning -> Semantic Assembly.
---

# HTML Book Suite (v7.0 — Modular Orchestrator)

This skill now orchestrates a 4-agent pipeline for high-end book production. 

## THE PIPELINE:

1.  **INGEST** (via `book-ingester`): Raw extraction & cleaning.
2.  **ARCHITECT** (via `book-architect`): Semantic distillation & **Glossary extraction**. Injects links to `glossary.html`.
3.  **DESIGN** (via `book-designer`): High-fidelity visuals, **SVG diagrams**, and Emoji navigation.
4.  **ASSEMBLE** (via `book-assembler`): Technical bundling and final QA.

## Orchestration Rules:
- **Glossary First**: Term extraction must happen after distillation but before visual enrichment.
- **Semantic Integrity**: Every term link MUST resolve to an anchor in `glossary.html`.
- **Visual Variety**: Ensure different visual types across the chapters.

Refer to sub-skills in `skills/html-book-suite/` for specific directives.

