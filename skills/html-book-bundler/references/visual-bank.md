# Standard Visualization Bank (Zero-Dependency)

A library of copy-pasteable, interactive diagrams for methodology and project management books. All components use pure SVG, CSS, and vanilla JS.

## 1. Cause-and-Effect (Fishbone / Ishikawa)
Ideal for root-cause analysis in management chapters.

```html
<svg width="100%" height="300" viewBox="0 0 600 300" class="fishbone">
  <!-- Backbone -->
  <line x1="50" y1="150" x2="550" y2="150" stroke="var(--line)" stroke-width="4" />
  <polygon points="550,140 580,150 550,160" fill="var(--acc)" />
  
  <!-- Ribs (Top) -->
  <g class="rib" onclick="showDetail('people')">
    <line x1="150" y1="150" x2="250" y2="50" stroke="var(--muted)" stroke-width="2" />
    <text x="220" y="40" fill="var(--text)" font-size="12">People</text>
  </g>
  <!-- Ribs (Bottom) -->
  <g class="rib" onclick="showDetail('tools')">
    <line x1="200" y1="150" x2="300" y2="250" stroke="var(--muted)" stroke-width="2" />
    <text x="270" y="270" fill="var(--text)" font-size="12">Tools</text>
  </g>
</svg>
```

## 2. Methodology Gantt Chart (Timeline)
Visualizing project phases without heavy libraries. Uses **CSS Grid**.

```html
<div class="mini-gantt" style="display: grid; grid-template-columns: 100px repeat(4, 1fr); gap: 5px;">
  <div class="gantt-label">Phase 1</div>
  <div class="gantt-bar" style="grid-column: 2 / 4; background: var(--acc); border-radius: 4px;"></div>
  <div class="gantt-empty"></div><div class="gantt-empty"></div>
  
  <div class="gantt-label">Phase 2</div>
  <div class="gantt-empty"></div>
  <div class="gantt-bar" style="grid-column: 3 / 6; background: var(--acc2); border-radius: 4px;"></div>
</div>
```

## 3. High-Fidelity Histogram
For showing frequency of events or risk distribution.

```html
<svg width="100%" height="150" viewBox="0 0 200 100">
  <!-- X/Y Axes -->
  <line x1="20" y1="10" x2="20" y2="90" stroke="var(--muted)" />
  <line x1="20" y1="90" x2="190" y2="90" stroke="var(--muted)" />
  
  <!-- Bars -->
  <rect x="30" y="40" width="20" height="50" fill="var(--acc)" class="bar-hover" />
  <rect x="55" y="20" width="20" height="70" fill="var(--acc2)" class="bar-hover" />
  <rect x="80" y="60" width="20" height="30" fill="var(--acc)" class="bar-hover" />
</svg>
```

## 4. Flowcharts & Logic Trees
Using SVG `<path>` with `marker-end="url(#arrowhead)"` for directed graphs.

```html
<svg width="100%" height="200">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="var(--line)" />
    </marker>
  </defs>
  <rect x="10" y="70" width="80" height="40" rx="5" fill="var(--panel)" stroke="var(--acc)" />
  <path d="M 90 90 L 140 90" stroke="var(--line)" fill="none" marker-end="url(#arrowhead)" />
  <rect x="150" y="70" width="80" height="40" rx="5" fill="var(--panel)" stroke="var(--acc2)" />
</svg>
```

## 5. Radar / Spider Chart
For multi-axis maturity assessment. Uses a single `<polygon>` with calculated points.

```html
<svg width="200" height="200" viewBox="0 0 200 200">
  <!-- Background Web -->
  <circle cx="100" cy="100" r="80" fill="none" stroke="var(--line)" stroke-dasharray="4 4" />
  <!-- Data Polygon -->
  <polygon points="100,20 180,100 100,180 20,100" fill="rgba(114,216,255,0.3)" stroke="var(--acc)" stroke-width="2" />
</svg>
```
