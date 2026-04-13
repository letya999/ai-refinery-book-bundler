---
name: html-book-bundler
description: The ultimate AI-driven book compiler. Converts raw source files into a semantically enriched, visually engaging single-file HTML app. Implements a strict pipeline: Text Extraction -> Theme Ideation -> Visual Planning -> Semantic Assembly.
---

# HTML Book Bundler (v6.0 — The AI-Architect Edition)

This skill elevates the book creation process from simple format conversion to **intelligent architectural redesign**. It transforms raw text into a modern, highly concentrated, interactive reading app. 

When you (the AI) invoke this skill, you are not just a parser; you are an Editor-in-Chief and an Information Designer. **You MUST strictly follow this 5-Phase pipeline.**

## MANDATORY 5-PHASE PIPELINE

### PHASE 1: Complete Raw Text Extraction
- **Action**: Use tools like `ingest.py`, PDF parsing scripts, or read existing files to extract the 100% complete raw text from the source material.
- **Rule**: Do not summarize yet. Just get the text into a readable format (e.g., raw HTML chapters) so you have the full context to analyze. Strip out OCR garbage, page numbers, and running headers.

### PHASE 2: Theme & Style Ideation
- **Action**: Analyze the overall message, tone, and target audience of the entire book.
- **Rule**: Decide on a visual theme. Should it be strict and corporate? Playful and modern? Deep and philosophical? 
- **Deliverable**: Mentally define (or write to a config) the color palette, typography tweaks, and structural logic that will guide the visuals. If needed, customize `assets/theme.css` to fit this specific book's vibe (e.g., adding specific background gradients or interactive CSS components).

### PHASE 3: Chapter-by-Chapter Visual Planning
- **Action**: Before touching the code, build a "Visual Blueprint" for every chapter.
- **Rule**: For each chapter, identify 2-4 key "Semantic Anchors" — concepts that are too important to remain plain text.
- **Mapping**:
  - *Processes, algorithms, historical timelines* → **Timeline** (`.vis-timeline`)
  - *Comparisons, "Good vs. Bad", "Myth vs. Reality"* → **Translator** (`.translator`)
  - *Metrics, "Inputs/Outputs", KPIs, requirements* → **Stats** (`.stats`)
  - *Lists of types, definitions, categorizations* → **Grid/Cards** (`.grid`, `.card`)
  - *Deep dives, case studies, optional lengthy details* → **Accordion** (`details.acc-item`)
  - *The single most critical takeaway* → **Insight Quote** (`blockquote.insight`)

### PHASE 4: Semantic Assembly & Volume Constraint
- **Action**: Rewrite and assemble each chapter HTML using your blueprint.
- **Strict Volume Constraint**: REDUCE the word count by 50-75%. Extract only the **"meat"** (essence, summary, overview, main takeaways). Eliminate fluff, repetitive anecdotes, and filler, while perfectly retaining the author's unique voice and wisdom.
- **Rule**: A "wall of text" is an automatic FAILURE. Every chapter MUST be a rich mix of concise paragraphs and the visual components planned in Phase 3. Add emojis strategically to guide the reader's eye.

### PHASE 5: Bundling & Quality Assurance
- **Action**: Run `node skills/html-book-bundler/scripts/bundle.cjs --input <chapters_dir> --output <final_book.html> --title "Book Title" --lang ru`.
- **Rule**: Open the final bundled HTML file and run a semantic check. Ensure that styles from `theme.css` applied correctly and no visual tags are broken. 

---

## Component Reference (from `theme.css`)

All components are CSS-only and require zero JS (except native HTML tags like `<details>`). Use these exact classes when rewriting the HTML in Phase 4.

| Visual Type | CSS Classes Required | Purpose |
|---|---|---|
| **Stats** | `<div class="stats"><div class="stat"><b class="stat-num">...</b><span class="stat-label">...</span></div></div>` | Metrics, short inputs/outputs. |
| **Translator** | `<div class="translator"><div class="tr-col bad/good"><div class="tr-head bad/good">...</div><ul>...</ul></div></div>` | Strong contrasts. |
| **Cards Grid** | `<div class="grid"><div class="card"><b>...</b><p>...</p></div></div>` | Collections of concepts. |
| **Timeline** | `<div class="vis-timeline"><div class="tl-step"><div class="tl-num">1</div><div class="tl-content">...</div></div></div>` | Step-by-step logic. |
| **Accordion** | `<details class="acc-item"><summary class="acc-head">...</summary><div class="acc-body">...</div></details>` | Expandable deep dives. |

## Absolute Prohibitions
1. **NO EXTERNAL DEPENDENCIES**: No CDNs, no external JS libraries, no web fonts. The book must be 100% offline.
2. **NO BLIND COPY-PASTING**: Do not just wrap the original text in HTML tags. You MUST distill the semantic essence.
3. **NO VISUAL MONOTONY**: Do not use the exact same visual component (e.g., only Cards) for three chapters in a row. Rotate them intelligently based on the context.