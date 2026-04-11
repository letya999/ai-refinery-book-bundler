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

## 4. Personalization: The Annotation Engine

Users should be able to highlight text and save notes. Since the book is a local file, `localStorage` is the only persistent database.

**The Solution (Selection API + XPath/CSS Selectors):**
1. Listen for the `selectionchange` or `mouseup` event inside the chapter `iframe`.
2. Capture the `window.getSelection().getRangeAt(0)`.
3. Serialize the Range into a robust path (e.g., "3rd paragraph, 15th character to 42nd character").
4. Save to `localStorage.setItem('annotations', JSON.stringify(data))`.
5. On chapter load, deserialize the paths and wrap the text nodes in `<mark>` tags.

*Note: This is technically complex but transforms a static read-only file into a personalized workspace.*
