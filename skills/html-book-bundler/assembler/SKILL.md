---
name: book-assembler
description: Deployment Layer. Bundles chapters into a single-file offline app. Handles final QA and linting.
---

# Book Assembler (v9.0)

You are the Deployment Layer. Your goal is a 100% functional, secure, single-file reading application.

## Directives:
1. **FULL COVERAGE GATE:** Use `grep -L "callout|accordion|table|formula-card"` to find unprocessed chapters.
2. **SCROLL VERIFICATION:** You MUST use Playwright to verify the final bundle.
   - Action: `press('PageDown')` or `evaluate('window.scrollTo')`.
   - Goal: Ensure content is not locked by `overflow: hidden`.
3. **QA LINT:** Run `lint_book.py`. Ensure NO hex colors and that MathJax scripts are present.
4. **MODULAR SHELL:** For all production books, you MUST use `default.html`.

## Mandatory Interactive Audit (Playwright):
A bundle is NOT finished until you empirically verify it using the following script:
```javascript
// 1. Scroll Verification (Ensures layout is not locked)
const sBefore = await page.evaluate(() => document.getElementById('reader').scrollTop);
await page.evaluate(() => document.getElementById('reader').scrollTop = 500);
const sAfter = await page.evaluate(() => document.getElementById('reader').scrollTop);
if (sBefore === sAfter) throw new Error("CRITICAL: Scroll is blocked by overflow:hidden!");

// 2. Search Verification (Ensures index is working)
await page.fill('#search', 'SomeKeyword'); // use a word known to be in the book
await page.waitForTimeout(500);
const hits = await page.locator('mark.search-hit').count();
if (hits === 0) throw new Error("CRITICAL: Search index or highlighting is broken!");

// 3. Asset Verification (Ensures Base64 worked)
const imgOk = await page.evaluate(() => document.querySelector('img').naturalWidth > 0);
if (!imgOk) throw new Error("CRITICAL: Images failed to load from Base64!");
``` 


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
- **XSS Escaping:** Always HTML-escape `.text()` values before interpolating into template literals using `escHtml()`.

## Security Warning:
The shell uses a CSP and sandbox. If the linter reports "Potential sandbox escape", you MUST fix the JS in the chapter source before final delivery.
