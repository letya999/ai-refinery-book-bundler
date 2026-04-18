---
name: book-assembler
description: Deployment Layer. Bundles chapters into a single-file offline app. Handles final QA and linting.
---

# Book Assembler (v8.3)

You are the Deployment Layer. Your goal is a 100% functional, secure, single-file reading application.

## Directives:
1. **Stable ID:** Ensure the `--title` matches previous builds to maintain user `localStorage` (bookmarks, progress). The `BOOK_ID` is a hash of the title.
2. **Zero-Dependency:** Inline all CSS and assets using `bundle.cjs`.
3. **QA Checks:** 
   - Run `../scripts/lint_book.py`. Fix any hex colors or sandbox escape risks.
   - Verify search functionality jumps to matched words (Search UI Integration).
4. **Final Assembly:** Use `--skip-insights` ONLY if the Designer already inserted manual `<blockquote class="insight">` blocks. Without it, auto-enrichment runs and may duplicate insights.

## Workflow:
# In-place optimization (max 1000px width — prevents mobile OOM)
python ../scripts/optimize_assets.py --dir ./chapters
# Bundle
node ../scripts/bundle.cjs --input ./chapters --output book_v8.html --title "Final Book Title" --lang ru
# Optional: Dev mode with live reload
node ../scripts/bundle.cjs --input ./chapters --output book_v8.html --dev
node ../scripts/dev_server.cjs book_v8.html
# Audit
python ../scripts/lint_book.py --file book_v8.html
```

## Critical Lessons:
- **Sandbox Architecture (FINAL):** The iframe uses `allow-scripts` ONLY — `allow-same-origin` has been permanently removed. Theme propagation, scroll restoration, search, anchors, and asset loading are ALL done via `postMessage`. Never reintroduce `allow-same-origin`. Never call `window.parent.document` from chapter JS — that would be a sandbox escape.
- **`guestReady` Is the Only Sync Point:** Do NOT wait for `iframe.onload` to send postMessage calls. Always wait for `{action:'guestReady'}` from the guest. `onload` fires before guest scripts execute, causing race conditions where setTheme/setScrollRatio messages are missed.
- **`</script>` Escaping — All JSON Blobs:** CHAPTERS, ASSETS, SEARCH_IDX, LANG_JSON and GLOBAL_TITLES must all have `</script>` escaped to `<\/script>`. Missed any one of them and JS code embedded in a book (e.g., a programming tutorial) will break the output HTML entirely.
- **Print Functionality:** Iframes do not print correctly. We use a popup-based printing mechanism (`print-btn`) that restores lazy-loaded images first. Do not add `height: 100vh` to iframes in `@media print`.
- **`--skip-insights` is Partial:** `--skip-insights` ONLY disables `autoInjectInsights` (pullquotes). It does NOT disable `autoCollapseLongParas`, `styleFirstPara`, or `autoEnrichLists`. If you want to suppress ALL auto-enrichment, you must process chapters manually before bundling.
- **Base64 Bloat:** Always run `optimize_assets.py` before bundling if the source has images. The 1000px width cap is mandatory.

## Security Warning:
The shell uses a CSP and sandbox. If the linter reports "Potential sandbox escape", you MUST fix the JS in the chapter source before final delivery.
