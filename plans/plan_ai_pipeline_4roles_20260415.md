# Plan: AI-Driven 4-Role Pipeline for PM Book (v8.0)
Date: 2026-04-15

## Concept

Instead of deterministic Python scripts, the AI executes 4 sequential roles on the
existing chapter source files. Each role is a distinct cognitive mode with a clear
input, output, and set of constraints. No sub-agents, no sub-skills infrastructure —
just the implementing AI working through 4 passes over the material.

Source files are already extracted in: `chapters_pm_book/` (15 chapters + glossary)
Source PDF is available at: `pm_book_ru.pdf` (for cross-reference if needed)

---

## Pre-condition fix (do this FIRST before the 4 roles)

File: `skills/html-book-bundler/scripts/chapter_processor.cjs`

Fix 1 — chapterMap missing glossary.html (line ~148, inside navScript template):
After the `for` loop that builds chapterMap, add:
```
chapterMap['glossary.html'] = ${totalChapters} - 1;
```

Fix 2 — hardcoded lang="en" (line ~230):
Change `'<html lang="en">'` to `\`<html lang="${langCode}">\``
Also add `langCode = 'ru'` parameter to `prepareChapter()` function signature,
and pass `langCode` from `bundle.cjs` when calling `prepareChapter()`.

---

## Role 1: INGEST
**Mode**: Editor / Cleaner
**Input**: `chapters_pm_book/chapter*.html` as they currently exist on disk
**Output**: Cleaned versions of same files (overwrite in place)

What the AI does in this role:
- Reads each chapter HTML file
- Removes PDF extraction artifacts: double spaces, broken hyphenation (words split
  across lines like "пла-нирование"), orphaned page numbers, repeated headers/footers
- Ensures each chapter has proper: `<html lang="ru">`, `<title>`, `<body>`,
  `<section class="hero">` with h1, `.wrap` container
- Does NOT add any visuals — pure structural cleanup only
- Chapters to process: chapter1.html through chapter15.html + glossary.html

Checklist per chapter:
- [ ] `lang="ru"` on html tag
- [ ] `<title>` matches chapter heading
- [ ] `<section class="hero">` present with `.kicker` and `<h1>`
- [ ] `<div class="wrap">` wraps body content
- [ ] No broken words from PDF line-wrapping
- [ ] No duplicate text blocks (OCR artifacts)

---

## Role 2: ARCHITECT
**Mode**: Semantic Analyst / Information Architect
**Input**: Cleaned chapter HTML files from Role 1
**Output**: `chapters_pm_book/blueprint.json`

What the AI does in this role:
- Reads each chapter's text content
- For each chapter produces a semantic record:

```json
{
  "chapter": 6,
  "title": "Глава VI. Планируем содержание",
  "core_concept": "WBS decomposition, scope management",
  "pm_terms_found": ["WBS", "Scope", "Deliverable", "Package"],
  "diagrams_needed": [
    {
      "type": "wbs_tree",
      "placement": "after_intro",
      "caption": "Иерархическая структура работ (WBS): декомпозиция по фазам"
    }
  ],
  "visual_components": ["stats_block", "translator_block"],
  "glossary_terms_to_link": ["WBS", "Scope", "Milestone"],
  "insight_quotes": [
    "Если вы не можете разложить проект на части — вы не понимаете его содержания."
  ]
}
```

Rules for diagram assignment:
- Chapter 3 (Подход):  translator (Waterfall vs Agile columns)
- Chapter 4 (Инициация): flowchart SVG (инициация→устав→kick-off), stats block
- Chapter 5 (Планирование): horizontal timeline SVG (5 фаз), process flow
- Chapter 6 (Содержание): WBS tree SVG (3 levels), stats
- Chapter 7 (Команда): RACI HTML table
- Chapter 8 (Время/Стоимость): Gantt SVG (5 tasks, weeks on X-axis) + Critical Path SVG
- Chapter 9 (Ответственность): RACI + communications matrix
- Chapter 10 (Риски): 3×3 Risk heatmap SVG (probability vs impact)
- Chapter 11 (Другие планы): Change control flowchart SVG
- Chapter 12 (Контроль): 4-node circular control cycle SVG
- Chapter 13 (Закрытие): checklist visual, timeline
- Chapters 1, 2, 14, 15: stats blocks, translator blocks (no complex SVG)

Also in this role: expand glossary.
Current glossary has 15 terms. Architect role reads all chapter text and identifies
any additional PM terms that appear frequently but have no glossary entry.
Adds them to the glossary term map.

Output file `blueprint.json` is saved in `chapters_pm_book/`.

---

## Role 3: DESIGN
**Mode**: Visual Designer / HTML Author
**Input**: `blueprint.json` + cleaned chapter HTML files
**Output**: Fully enriched chapter HTML files (overwrite in place)

What the AI does in this role:
FOR EACH CHAPTER (process one by one):

1. Read the chapter's blueprint record
2. Inject glossary term links into body text (per `glossary_terms_to_link` list)
   Pattern: `<a href="glossary.html#TERM_LOWER" class="term-link">TERM</a>`
3. Inject visual components per `visual_components` list
4. Inject SVG diagram(s) per `diagrams_needed` list

SVG RULES (MANDATORY — no exceptions):
- ALL fills/strokes via CSS variables: `var(--acc)`, `var(--txt)`, `var(--panel)`,
  `var(--panel2)`, `var(--line)`, `var(--bad)`, `var(--acc2)`, `var(--warn)`
- NEVER hardcode hex colors (#000, #f8fafc etc.)
- Accent nodes: `style="fill:var(--acc)"` + text `style="fill:var(--bg)"` for contrast
- Default nodes: `class="diag-node"` (= panel fill + acc stroke, from theme.css)
- Text in SVG: `class="diag-text"` (= txt color, centered, from theme.css)
- Links/arrows: `class="diag-link"` (= line stroke, no fill, from theme.css)
- Critical/bad path: `style="stroke:var(--bad);stroke-width:3"`
- Wrap every SVG in: `<div class="vis-diag">...<div class="caption">TEXT</div></div>`

SVG SPECS per diagram type:

### wbs_tree (ch6)
viewBox="0 0 600 240"
Root node at top center: 200×50, `style="fill:var(--acc)"`, text `style="fill:var(--bg)"`
3 level-2 nodes below: `class="diag-node"` 
2-3 level-3 leaf nodes: smaller `class="diag-node"`, dashed stroke
Connectors: `class="diag-link"`

### gantt (ch8)
viewBox="0 0 700 220"
Y-axis: 5 task labels left (text `class="diag-text"` right-aligned)
X-axis: week numbers 1-8 (text `class="diag-text"`)
Grid lines: `stroke="var(--line)" stroke-width="0.5" opacity="0.4"`
Task bars: `<rect class="diag-node">` with `style="fill:var(--acc2)"` for normal,
           `style="fill:var(--bad)"` for critical path task
Caption: "Диаграмма Ганта: пример 5 задач, критический путь выделен"

### critical_path_network (ch8)
viewBox="0 0 600 160"
5 nodes: Start, Task A (CP), Task B, Task C (CP), End
CP path nodes: `style="stroke:var(--bad);stroke-width:3"`
CP arrows: `style="stroke:var(--bad)"`
Non-CP arrows: `class="diag-link"`
Node text: `class="diag-text"` + duration label below in `var(--muted)`

### risk_matrix (ch10)
viewBox="0 0 360 300"
3×3 grid, 9 cells
Axis labels: "Вероятность" (Y) and "Воздействие" (X) — `class="diag-text"`
Cell colors:
  Low zone: `fill="rgba(135,239,201,.2)"` (acc2 tinted)
  Medium: `fill="rgba(255,209,138,.2)"` (warn tinted)
  High: `fill="rgba(255,143,143,.2)"` (bad tinted)
Each cell has text label: "Низкий", "Средний", "Высокий"
Caption: "Матрица рисков: вероятность × воздействие"

### flowchart (ch4, ch11)
viewBox="0 0 560 160"
4-5 boxes in horizontal sequence with arrows
Decision diamond if needed: rotated rect
Box type: `class="diag-node"` for process, `style="fill:var(--acc)"` for start/end
Caption relevant to chapter content

### timeline_horizontal (ch5)
viewBox="0 0 700 100"
Horizontal line: `class="diag-link"` full width
5 milestone dots: circles `r="8"` with `style="fill:var(--acc)"`
Labels below each: phase name, `class="diag-text"`
Caption: "5 групп процессов планирования по PMBOK"

### circular_cycle (ch12)
viewBox="0 0 300 300"
4 nodes at clock positions (12, 3, 6, 9)
Center circle or label
Curved arrows between nodes (use arc paths)
Nodes: `class="diag-node"`, text: `class="diag-text"`
Caption: "Цикл контроля исполнения проекта"

### translator_block (ch3 and others)
Not SVG — HTML component:
```html
<div class="translator">
  <div class="tr-col bad">
    <div class="tr-head bad">Waterfall</div>
    <ul><li>...</li></ul>
  </div>
  <div class="tr-col good">
    <div class="tr-head good">Agile</div>
    <ul><li>...</li></ul>
  </div>
</div>
```
Content must be drawn from chapter text, not fabricated.

### stats_block
```html
<div class="stats">
  <div class="stat"><b class="stat-num">VALUE</b><span class="stat-label">LABEL</span></div>
</div>
```
Values must come from chapter text (real numbers/terms, not made up).

Also in this role: update `chapters_pm_book/glossary.html`
- Add any new terms identified by Architect role
- Each term: `<div class="card" id="TERM_LOWER"><b>TERM</b><p>DEFINITION</p></div>`
- Ensure ALL terms linked from chapters have matching `id=` in glossary

---

## Role 4: ASSEMBLE
**Mode**: Build Engineer
**Input**: Enriched chapter HTML files + fixed chapter_processor.cjs
**Output**: `pm-book-v8.html`

What the AI does in this role:
1. Verify pre-condition fix was applied to chapter_processor.cjs
2. Run:
   ```
   node skills/html-book-bundler/scripts/bundle.cjs \
     --input chapters_pm_book \
     --output pm-book-v8.html \
     --title "Управление ИТ-проектами: Полное руководство" \
     --lang ru \
     --skip-insights
   ```
3. Run lint:
   ```
   python skills/html-book-bundler/scripts/lint_book.py --file pm-book-v8.html
   ```
4. Quick self-audit: check that bundled output contains:
   - At least 8 `<svg` occurrences (across all chapters embedded in JSON)
   - `chapterMap['glossary.html']` present in output
   - `lang="ru"` on chapter iframes (not `lang="en"`)
   - All glossary hrefs have matching id anchors in glossary chapter

---

## Also update: SKILL.md

Rewrite SKILL.md to document the ACTUAL pipeline:

```
## THE PIPELINE (v8.0 — AI-Driven 4-Role):

1. INGEST   — Clean raw chapter HTML: fix lang, hero structure, PDF artifacts
2. ARCHITECT — Semantic analysis per chapter → blueprint.json (what goes where)
3. DESIGN   — Write enriched HTML: SVG diagrams (CSS-var only), term links, components
4. ASSEMBLE — bundle.cjs + lint

## SVG Contract (non-negotiable):
- No hex colors. Only CSS variables.
- Accent nodes: fill:var(--acc) + text fill:var(--bg)
- All text: class="diag-text"
- Wrap in: <div class="vis-diag">

## chapterMap Contract:
- chapter_processor.cjs MUST include glossary.html → last chapter index
- All chapter iframes MUST use lang from --lang flag
```

---

## File Change Summary

| File | Action |
|------|--------|
| `skills/html-book-bundler/scripts/chapter_processor.cjs` | Fix chapterMap + lang param |
| `chapters_pm_book/chapter1.html` through `chapter15.html` | Roles 1+3: clean + enrich |
| `chapters_pm_book/glossary.html` | Role 2+3: expand terms, add ids |
| `chapters_pm_book/blueprint.json` | Role 2: create (intermediate artifact) |
| `skills/html-book-bundler/SKILL.md` | Role 4: update to document real pipeline |
| `pm-book-v8.html` | Role 4: final output |

---

## Execution Notes

- Process chapters one by one in Role 3 (not all at once) to avoid context overload
- Start with chapters that have the most complex diagrams (8, 10, 6, 12) then simpler ones
- SVG must be tested mentally against dark theme: if you're using var() everywhere, it works
- Do not add visual components with invented facts — draw content from chapter text only
- `--skip-insights` because chapters will have manually placed `<blockquote class="insight">` 
  from the enrichment; auto-injection would double them
