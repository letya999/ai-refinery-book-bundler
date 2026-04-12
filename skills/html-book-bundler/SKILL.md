---
name: html-book-bundler
description: Engineering self-contained, interactive HTML books with recursive asset bundling, manifest-driven navigation, and real-time development sync.
---

# HTML Book Bundler

Expert skill for transforming linear manuscripts into professional-grade, interactive single-file HTML applications.

## 1. Core Architecture (The Three-Tier Model)

### A. The Shell (Application Layer)
- **Responsibility:** Navigation, State Persistence (localStorage), UI/UX.
- **Search:** Full-text search across all chapters with debounced indexing.
- **Dev Mode:** Automatic Live Reload when used with `dev_server.cjs`.

### B. The Sandbox (Chapter Layer)
- **Isolation:** Each chapter rendered via Blob URL in a sandboxed `<iframe>`.
- **Navigation Bridge:** Automated `postMessage` injection for cross-chapter links.
- **Asset Handling:** Recursive bundling of `<img>`, `<link>`, `<script>`, and `url()` assets.

### C. The Asset Payload (Data Layer)
- **Zero-Dependency:** 100% of local resources (images, CSS, JS) are converted to Base64/DataURIs.

## 2. Automated Quality Assurance (Linter)

Mandatory validation via `lint_book.py`.

### Critical Checks:
- **Zero-External:** Fails if any `http(s)` links are found in chapters (must be bundled).
- **Sandbox Safety:** Prevents unauthorized `window.parent` access.
- **Data Integrity:** Ensures unique IDs for all interactive elements (checkboxes).

## 3. Workflows

### Scenario: Development
```bash
# Starts server with Live Reload
node skills/html-book-bundler/scripts/dev_server.cjs --input ./chapters
```

### Scenario: Production Build
```bash
# Bundle and Audit
node skills/html-book-bundler/scripts/bundle.cjs --input ./chapters --output my-book.html
python skills/html-book-bundler/scripts/lint_book.py --file ./my-book.html
```

## 4. Visual Strategy
- **Backgrounds:** Animated `Twinkle Stars`, `Blur Backdrops`.
- **Interactivity:** `Persistent Checklists`, `Progress Tracking`, `Navigation Manifests`.

## 5. References
- `references/single-file-architecture.md`
- `references/interactive-visual-patterns.md`
- `references/pdf-visual-workflow.md`
