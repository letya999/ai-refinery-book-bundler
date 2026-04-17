# Single-File Architecture (Offline-First)

**Goal:** A single standalone `*.html` file that works entirely offline without any external network dependencies or CDN calls.

## Core Strategy: The `srcdoc` Pattern

The bundler transforms multiple source chapters and assets into a single HTML shell that dynamically manages content.

1. **Chapter Storage:** Chapters are stored as UTF-8 strings within a global `CHAPTERS` array in the shell's `<script>` block.
2. **Dynamic Loading:** When a user selects a chapter, the shell updates the main `<iframe>` using the `srcdoc` attribute: `iframe.srcdoc = CHAPTERS[index]`.
3. **Escaping:** To prevent premature script termination in the shell, any `</script>` tags within the chapter HTML are escaped as `<\/script>` during the JSON serialization process in the bundler.
4. **Zero External Assets:** All images and small assets are converted to Base64 Data URIs and inlined directly into the chapter HTML or CSS before bundling.

## Visual & Interaction Principles

1. **Self-Contained Visuals:** All diagrams and charts use standard HTML/CSS or `canvas`. 
2. **No External Fonts/Icons:** Use system fonts or embed small critical fonts via `@font-face` Data URIs.
3. **Vanilla JS Preference:** Minimize dependencies. If a library is required, it must be inlined into the shell.
4. **Lazy Initialization:** Heavy visual components should initialize only when the chapter is loaded into the viewport.

## Shell Layout & Features

- **Responsive Sidebar:** Chapter navigation with search and bookmarking.
- **Sandboxed Execution:** The content `<iframe>` uses `sandbox="allow-scripts allow-same-origin"` to isolate chapter logic while allowing communication with the shell.
- **Persistence:** Reading progress (current chapter and scroll position) and bookmarks are saved to `localStorage` keyed by a unique `BOOK_ID`.
- **Navigation Bridge:** Chapters communicate back to the shell (e.g., for inter-chapter links) using `window.parent.postMessage`.

## Security & Resilience

- **CSP Headers:** The shell includes a strict `Content-Security-Policy` to block all external network requests.
- **Offline Reliability:** The file must remain fully functional when opened from a local disk (`file://` protocol).
- **Memory Management:** Since it's a single-file app, avoid memory leaks in long-running sessions by cleaning up global event listeners or heavy objects if chapters are frequently switched.

## Technical Rationale

The `srcdoc` approach is preferred over `Blob URLs` (legacy) because it is more robust, requires no manual memory management (`URL.revokeObjectURL`), and works consistently across all modern browsers without permission issues common with `blob:` origins.

---
See also: `references/performance-playbook.md`, `references/library-injection-mode.md`.
