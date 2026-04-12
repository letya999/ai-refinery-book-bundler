# Advanced System Features for Single-File HTML Books

To elevate a basic bundled HTML file into a fully-fledged "Offline Web App" without introducing external dependencies, implement the following advanced architectural patterns. 

## 1. Performance & Smooth Navigation (Modern APIs)

### A. View Transitions API (Seamless Chapter Switching)
Instead of an abrupt reload when swapping the `iframe.src` (Blob URL) or changing the active chapter `div`, use the native View Transitions API to create a fluid, app-like page turn or crossfade.

```javascript
// Function to switch chapter
async function goToChapter(index) {
  const switchLogic = () => {
    // Load the new Blob URL into the iframe or swap the active DIV
    document.getElementById('frame').src = createBlobUrl(index);
    updateActiveSidebarItem(index);
  };

  // Fallback for older browsers
  if (!document.startViewTransition) {
    switchLogic();
    return;
  }

  // Smooth transition for modern browsers
  document.startViewTransition(() => switchLogic());
}
```

### B. Content-Visibility (Render Deferral)
For long chapters with heavy DOM trees or many embedded `<canvas>` graphics, defer rendering of off-screen elements until the user scrolls near them. This drastically improves the Time-To-Interactive (TTI).

```css
/* Apply to top-level sections inside the chapter iframe */
.chapter-section {
  content-visibility: auto;
  contain-intrinsic-size: 0 500px; /* Estimated height to prevent scrollbar jumping */
}
```

## 2. The Shared Asset Cache (Minimizing File Size)

If every chapter `iframe` needs the same 50KB of CSS and JS utility functions, injecting them into 20 chapters multiplies the file size by 1MB unnecessarily.

**The Solution:**
1. At build time (`bundle.cjs`), concatenate all shared CSS/JS.
2. Store this shared payload as a **single Base64 string** in the main Shell.
3. When loading a chapter, decode the chapter HTML, inject the shared string into the `<head>`, and *then* create the Blob URL.

```javascript
// Concept inside the Shell
const SHARED_CSS = atob(window.B64_COMMON_STYLES);

function renderChapter(base64HTML) {
    let html = atob(base64HTML);
    // Inject the shared cache right before the closing </head>
    html = html.replace('</head>', `<style>${SHARED_CSS}</style></head>`);
    
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    return URL.createObjectURL(blob);
}
```

## 3. Offline Full-Text Search Engine

A critical feature for technical books. Since there is no backend, the search must run entirely in the browser.

**The Solution (Zero-Dependency Inverted Index):**
1. During the Node.js build process (`bundle.cjs`), strip HTML tags from all chapters, tokenize the text, and build a lightweight inverted index (Word -> Array of Chapter IDs).
2. Serialize this index to JSON and embed it into the Shell's `<script>` tag.
3. In the client UI, a simple search input queries this JSON object instantly.

```javascript
// Embedded Index (generated at build time)
const SEARCH_INDEX = {
  "architecture": [0, 5],
  "canvas": [2, 3, 5],
  "principle": [1, 2, 8]
};

function searchBook(query) {
  const term = query.toLowerCase().trim();
  const results = SEARCH_INDEX[term] || [];
  // Render results in the sidebar pointing to Chapter indices
}
```

## 5. Cross-Chapter Navigation (Iframe Bridge)

When each chapter is isolated in an `iframe` with a `Blob URL`, standard relative links (e.g., `<a href="chapter2.html">`) fail because the `Blob` origin is considered `null` or `cross-origin` from the main book file. Direct access to `window.parent` is often blocked by browser security policies.

**The Solution (The Bridge Pattern):**
1. **The Shell Listener:** The main book file (Shell) listens for a specific `message` event.
2. **The Chapter Bridge:** The bundler automatically injects a small script into every chapter that intercepts all link clicks and sends a `postMessage` to the parent instead of following the link.

```javascript
// Inside the Shell (templates/default.html)
window.addEventListener('message', e => {
  if (e.data && e.data.action === 'bookGo') {
    // chapterIdx is target chapter, anchorId is optional element ID
    navigateToChapter(e.data.chapterIdx, e.data.anchorId);
  }
});

// Inside every Chapter (Injected by scripts/bundle.cjs)
document.addEventListener('click', e => {
  const a = e.target.closest('a');
  if (a && a.getAttribute('href')) {
    const href = a.getAttribute('href');
    if (href.startsWith('http')) return; // Allow external links

    e.preventDefault();
    const parts = href.split('#');
    const chapterIdx = parseChapterIndex(parts[0]);
    const anchorId = parts[1] || null;

    window.parent.postMessage({ 
      action: 'bookGo', 
      chapterIdx, 
      anchorId 
    }, '*');
  }
});
```

**Key Benefit:** This creates a seamless "Single Page App" feel where users can jump between chapters and specific anchors (e.g., a specific project phase in P3.express) even though the content is technically isolated and encoded.
