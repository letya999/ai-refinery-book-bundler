---
name: html-book-bundler
description: Engineering self-contained, high-performance, 100% offline interactive HTML books with WebP optimization, strict CSP security, and smart search indexing.
---

# HTML Book Bundler (v2.0)

Expert skill for transforming manuscripts into secure, single-file HTML applications that run entirely offline without external dependencies.

## 1. Zero-Trust Architecture

### A. Security First
- **Strict CSP:** Built-in Content Security Policy blocks all network access (`default-src 'none'`).
- **Sandbox Isolation:** Chapters run in a sandboxed `<iframe>` to prevent access to parent `localStorage` or `cookie`.
- **Safe Bridge:** Cross-chapter navigation uses a secure `postMessage` bridge with origin/source validation.

### B. Smart Payloads
- **WebP Optimization:** Automatically converts all images to WebP to minimize Base64 overhead.
- **Deduplicated Search Index:** Removes stop-words and duplicates to save up to 40% of text memory.
- **UTF-8 Enforcement:** Guarantees correct encoding for offline viewing across all devices.

### C. Resource Lifecycle
- **Memory Management:** Explicit `URL.revokeObjectURL()` calls prevent memory leaks during page flipping.
- **Zero-External:** Fails build if any `http(s)` links are present (everything must be bundled).

## 2. Advanced Tooling

### Asset Optimization:
```bash
# Compress images to WebP
python scripts/optimize_assets.py --input ./raw_images --output ./chapters/assets
```

### Production Build:
```bash
# Bundle chapters into one HTML
node scripts/bundle.cjs --input ./chapters --output my-book.html
# Mandatory Security Audit
python scripts/lint_book.py --file ./my-book.html
```

## 3. Best Practices
- **Images:** Use `.webp` for all assets to keep the final file under 20MB.
- **CSS/JS:** Keep styles and scripts local to chapters; the bundler will inline them automatically.
- **Navigation:** Use standard `<a href="chapter2.html#section">` links; the bridge will handle them.

## 4. References
- `references/single-file-architecture.md` (Updated)
- `references/interactive-visual-patterns.md`
- `references/pdf-visual-workflow.md`
