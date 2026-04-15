# HTML Book Bundler Skill (v8.1)

## Overview
A specialized toolchain for creating high-quality, single-file HTML books with rich visual components and interactive navigation.

## THE PIPELINE (v8.0 — AI-Driven 4-Role):

1. **INGEST** — Clean raw chapter HTML: fix `lang`, `hero` structure, remove PDF/OCR artifacts.
2. **ARCHITECT** — Semantic analysis per chapter → `blueprint.json` (defines diagrams, terms, and components).
3. **DESIGN** — Write enriched HTML: inject SVG diagrams (CSS-var only), glossary links, and visual components.
4. **ASSEMBLE** — Run `bundle.cjs` to produce final single-file HTML and perform linting.

## SVG Contract (non-negotiable):

- **NO HEX COLORS**. Use CSS variables only: `var(--acc)`, `var(--txt)`, `var(--panel)`, `var(--line)`, `var(--bad)`, etc.
- **Accent Nodes**: `style="fill:var(--acc)"` with text `style="fill:var(--bg)"`.
- **Default Nodes**: `class="diag-node"`.
- **Text**: `class="diag-text"`.
- **Links/Arrows**: `class="diag-link"`.
- **Wrapper**: Wrap every SVG in `<div class="vis-diag">...<div class="caption">...</div></div>`.

### Arrowhead Markers (REQUIRED for flowcharts):
Every SVG with directional arrows MUST declare markers in `<defs>`:
```html
<defs>
  <marker id="arrN" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" style="fill:var(--line)"/>
  </marker>
</defs>
```
Then reference on each arrow: `marker-end="url(#arrN)"`. Without this, all arrows render as plain lines.

### SVG Text Rules:
- **NEVER** put `<a href>` inside an SVG `<text>` element — it is invalid and silently discarded by browsers.
- Move hyperlinks to the caption `<div>` outside the SVG, or use SVG-level `<a>` elements.
- Keep text inside node circles/rects: check that text `y` coordinate is within `cy ± r` (for circles) or within rect bounds.

### Multi-Branch Diagrams:
- **BAD**: 4 arrows all starting from the same point (350,100) — they visually overlap.
- **GOOD**: Use a vertical trunk line first, then 4 short horizontal branches fanning out to boxes.
  ```
  Assess box → (trunk) vertical line → branch1 → Box1
                                      → branch2 → Box2
                                      → branch3 → Box3
                                      → branch4 → Box4
  ```

## chapterMap & Navigation:

- `chapter_processor.cjs` MUST include `glossary.html` in the `chapterMap`, pointing to the last chapter index.
- All chapter iframes MUST respect the `--lang` flag from the bundler.
- Inter-chapter links use the format `href="glossary.html#anchor"` and are intercepted by the navScript bridge.

### Anchor Navigation Timing:
- When `go(i, anchor)` is called with an anchor: **skip scroll restoration** (anchor takes priority over saved position).
- Defer `scrollIntoView` with `setTimeout(..., 80)` after `onload` to allow iframe layout to settle before scrolling.
- Without the guard, the restored scroll position overrides the anchor target.

## Semantic Quality Validator:

The `chapter_processor.cjs` validator checks for visual components. The regex must include all common container classes:
```js
const visualTags = /class="(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)"|<table>/i;
```

## Template Requirements:

Every bundled output must include:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline' data:; img-src 'self' data: blob:; connect-src 'none'">
```

## Usage:
```bash
node bundle.cjs --input <dir> --output <file.html> --title "Book Title" --lang ru --skip-insights
```

## Lessons Learned (from pm-book debug session):

1. **Glossary nav was silently broken**: `chapterMap` only mapped `chapterN.html` files, never `glossary.html`. All 51 term-links were dead. Fix: always add `chapterMap['glossary.html'] = totalChapters - 1` after the for-loop.

2. **SVG arrowheads require `<defs>` + `marker-end`**: Multiple chapters had SVG flowcharts with plain lines and no arrowheads. The bundler should treat missing `<defs>` in arrow-heavy SVGs as a warning.

3. **SVG `<a>` inside `<text>` is invalid**: HTML anchors do not work inside SVG `<text>`. Use caption text outside the SVG for glossary links.

4. **Fan-out arrows from one point look broken**: When 4 strategy arrows all start at `(350, 100)`, they visually stack. Always use a trunk-and-branch pattern for 1-to-N fanouts.

5. **Anchor scroll competes with saved scroll restore**: The `go()` function must skip restoring the saved scroll position when a specific anchor target is provided, otherwise the anchor scroll is cancelled.

6. **Semantic validator missed `vis-diag` and `vis-stats`**: Chapters with SVGs but no `card`/`translator` blocks were falsely flagged as "wall of text". The validator regex must cover all visual container classes.
