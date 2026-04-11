# Data Visualization & Decision Tools (Zero-Dependency)

This reference provides implementation patterns for handling complex data and decision logic in interactive HTML books.

## 1. Smart Responsive Tables (Grid-based)
Instead of standard `<table>`, use CSS Grid to allow seamless transition from a "Table View" (Desktop) to a "Card View" (Mobile).

```css
.smart-table {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1px;
  background: var(--line);
}
.table-cell {
  background: var(--panel);
  padding: 12px;
}
@media (max-width: 600px) {
  .smart-table { display: block; }
  .table-cell::before {
    content: attr(data-label);
    display: block;
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
  }
}
```

## 2. Interactive Checklists (Action-Oriented)
Methodological books focus on *doing*. Use persistent checkboxes to track reader progress.

```javascript
// Sync checkbox with localStorage
document.querySelectorAll('.task-check').forEach(box => {
  const id = box.id;
  box.checked = localStorage.getItem(id) === 'true';
  box.onchange = () => localStorage.setItem(id, box.checked);
});
```

## 3. Micro-Charts (Pure SVG)
Visualizing maturity or effort distribution without Chart.js.

### A. Simple Bar Chart (SVG)
```html
<svg width="100%" height="60" viewBox="0 0 100 60">
  <rect x="0" y="40" width="15" height="20" fill="var(--acc)" />
  <rect x="20" y="10" width="15" height="50" fill="var(--acc2)" />
  <text x="0" y="10" font-size="8" fill="var(--muted)">Effort</text>
</svg>
```

### B. Radar/Spider Chart (Path-based SVG)
Use a pre-calculated `<polygon points="...">` to show maturity profiles across multiple axes (e.g., Focus, Simplicity, Speed).

## 4. Decision Matrices (IF/THEN Logic)
Interactive grids to help readers choose a path.

```html
<div class="decision-grid">
  <button onclick="highlightResult('path-a')">Condition 1</button>
  <button onclick="highlightResult('path-b')">Condition 2</button>
  <div id="result-area" class="result-box">Select a condition...</div>
</div>
```

## 5. Print & PDF Safety
Ensure interactive content is accessible when exported to static formats.

```css
@media print {
  .card-flip { transform: none !important; }
  .smart-accordion { display: block !important; }
  .no-print { display: none !important; }
  body { background: white; color: black; }
}
```
