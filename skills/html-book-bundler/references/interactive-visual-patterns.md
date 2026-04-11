# Interactive & Visual Patterns for HTML Books

This reference contains proven techniques from the `mars-venera` and `ne-uslozhnyay` projects to enrich the user experience in self-contained single-file books.

## 1. Atmospheric Anchors (CSS Backgrounds)

Backgrounds MUST support the cognitive goal of the chapter, providing depth without distraction.

### A. Twinkle Stars (Focus & Philosophy)
Ideal for deep, dark themes.
```css
.stars {
  position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(1px 1px at 20px 30px, #fff, rgba(0,0,0,0)),
              radial-gradient(1px 1px at 40px 70px, #fff, rgba(0,0,0,0));
  background-size: 200px 200px;
  animation: twinkle 4s infinite;
}
@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}
```

### B. Dynamic Flow (Soft Transitions)
Smooth color bleeding for introductory sections.
```css
.hero {
  background: linear-gradient(-45deg, #081423, #0f1f38, #163056, #081423);
  background-size: 400% 400%;
  animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

### C. Tech Grid (Structure & Logic)
For technical or methodological sections.
```css
.grid-bg {
  background-image: linear-gradient(rgba(114, 216, 255, 0.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(114, 216, 255, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

## 2. Structural Data Layouts

### The "Translator" Pattern (Complexity vs Simplicity)
Comparison of two different worldviews or approaches.
```html
<div class="translator">
  <div class="side-complex">
    <span class="label">Complex</span>
    <p>Verbose corporate jargon...</p>
  </div>
  <div class="side-simple">
    <span class="label">Simple</span>
    <p>The essence in three words.</p>
  </div>
</div>
```

### Metrics Gauge (Risk/Maturity)
Visualizing values like risk, stress, or progress.
```html
<div class="gauge">
  <div class="gauge-bar">
    <div class="gauge-fill" style="width: 75%; background: var(--acc);"></div>
  </div>
  <div class="gauge-label">Level: High</div>
</div>
```

## 3. Interactive UX Components

### Flash-Cards (Memory Reinforcement)
For "Myth vs. Reality" or key takeaways.
```css
.card-flip {
  transition: transform 0.6s;
  transform-style: preserve-3d;
}
.card-flip.is-flipped {
  transform: rotateY(180deg);
}
```

### Smart Accordion (Context-on-Demand)
Hiding secondary details or examples to maintain a clean reading flow.
- Use CSS `grid-template-rows: 0fr` to `1fr` transitions for smooth height animation without hard-coded pixel values.

## 4. Engineering Implementation Standards

1.  **State Persistence:** Always save `curChapter` using `localStorage.setItem('book_state', chapterIndex)`.
2.  **Memory Optimization:** Revoke old Blob URLs when navigating between chapters.
3.  **Isolation Integrity:** Use `URL.createObjectURL(new Blob([html], {type: 'text/html'}))` to sandbox chapter styles.
