# Input Specification: HTML Chapter Files

`bundle.cjs` consumes a directory of HTML chapter files. This document defines what valid input looks like.

## File naming

Files must end in `.html` and sort correctly by `localeCompare` with `{ numeric: true }`:

```
chapter1.html
chapter2.html
...
chapter10.html   ← comes after chapter9, not after chapter1
chapter11.html
```

Any naming scheme that sorts correctly works:
- `chapter1.html` ... `chapter12.html` (recommended)
- `01.html` ... `12.html`
- `part1.html` ... `part9.html`

`ingest.py` always outputs `chapter1.html`, `chapter2.html`, etc.

## Minimal valid chapter

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Chapter Title</title>
</head>
<body>
  <p>Content here.</p>
</body>
</html>
```

The bundler extracts the chapter title from `<title>` first, then `<h1>`, then filename.

## Optional: local theme override

Place a `theme.css` in the chapters directory to override `assets/theme.css` for this book:

```
chapters/
  chapter1.html
  chapter2.html
  theme.css       ← optional, overrides default theme
```

## Optional: local assets (images)

Place images relative to chapter files. `bundle.cjs` stores them in a shared `ASSETS` dictionary (keyed by content hash) and lazy-loads them via `IntersectionObserver` — images are only decoded when they scroll into view, preventing mobile OOM crashes on image-heavy books:

```
chapters/
  chapter1.html   ← <img src="assets/cover.jpg">
  assets/
    cover.jpg
```

During bundling, `src` attributes are replaced with a 1x1 transparent GIF placeholder and a `data-src="assetKey"` attribute. The shell resolves each key to a base64 data URI on demand via postMessage (`requestAsset`/`provideAsset`). Linked non-HTML assets (`href=`) are resolved on click and offered as downloads.

External URLs (`http://`) and existing data URIs are left unchanged. Run `optimize_assets.py --dir ./chapters` before bundling to cap image width at 1000px.

## Chapter HTML conventions (for rich output)

`chapter_processor.cjs` auto-enriches all chapters. You can also use these CSS classes explicitly:

### Structural classes (from theme.css)
```html
<div class="wrap">          <!-- main content container, max 860px -->
<div class="hero">          <!-- full-width hero with gradient background -->
<div class="sec">           <!-- section with subtle panel background -->
<div class="grid">          <!-- card grid, auto-columns -->
  <div class="card">...</div>
</div>
<div class="stats">         <!-- stats row -->
  <div class="stat"><b class="stat-num">42</b><span>label</span></div>
</div>
<details class="acc-item">
  <summary class="acc-head">Question</summary>
  <div class="acc-body">Answer</div>
</details>
<blockquote class="insight">Pullquote text</blockquote>
<p class="lead-para">Opening paragraph with larger text</p>
```

### Cross-chapter navigation links
The `navScript` intercepts internal links automatically:
```html
<a href="chapter3.html">Go to chapter 3</a>
```
These are converted to `postMessage` navigation calls. No manual JS required.

### Exclusive accordions (CSS-only, modern browsers)
```html
<details name="group1">
  <summary>Option A</summary>
  <p>Content A — only one open at a time within the group</p>
</details>
<details name="group1">
  <summary>Option B</summary>
  <p>Content B</p>
</details>
```
Requires Chrome 120+ / Firefox 130+ / Safari 17.2+.

## What the bundler does NOT accept

- Directories as chapter content (only `.html` files are read)
- Chapters that `require()` Node modules or use `import` (browser-only HTML)
- Chapters with absolute filesystem paths in `src=` (use relative paths only)
- Non-UTF-8 encoding without a `<meta charset>` declaration
