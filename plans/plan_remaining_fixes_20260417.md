# Plan: HTML Book Bundler v8.3 — Remaining Fixes (items 2-7)

**Date:** 2026-04-17

---

## Fix 2 — `autoEnrichLists` stats pattern too aggressive (`chapter_processor.cjs`)

**Problem:** Any `<ul>` list item containing a colon or em-dash triggers stats conversion. Items like `"See chapter 3: next steps"` or `"URL: https://example.com"` become stat cards.

**Fix in `autoEnrichLists`:** After parsing stats, add two guards before accepting the stats pattern:
1. Every label must be ≤ 35 characters (real stat labels are short: "Revenue", "Users", "Growth rate")
2. No label should look like a URL or sentence fragment (no spaces after colon that start with http/www, no label containing more than 4 words)

Concretely, change the stats check from:
```js
if (stats.every(s => s !== null)) {
```
To:
```js
const isValidStats = stats.every(s => s !== null)
  && stats.every(s => s.label.length <= 35 && s.label.split(/\s+/).length <= 5 && !/https?:\/\//.test(s.label));
if (isValidStats) {
```

---

## Fix 3 — Unified PDF entry in `ingest.py`

**Problem:** `ingest.py` supports FB2/EPUB/DOCX but not PDF, even though `pdf_parser_general.py` exists in the same `scripts/` directory. Users following the SKILL have to use a different command for PDF.

**Fix in `ingest.py`:**
- Add `.pdf` to the supported formats check in `main()`:
```python
elif suffix == '.pdf':
    try:
        import sys
        sys.path.insert(0, str(in_path.parent.parent / 'scripts'))
        from pdf_parser_general import PDFParser
        config = {'lang': args.lang}
        processor = PDFParser(str(in_path), config)
        processor.run(str(out_dir))
    except ImportError:
        print("Error: PyMuPDF required for PDF support. Run: pip install pymupdf")
        raise SystemExit(1)
```

Actually simpler — since both files are in `scripts/`, use a direct relative import. Because they're in the same directory, just do:
```python
elif suffix == '.pdf':
    _scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(_scripts_dir))
    try:
        from pdf_parser_general import PDFParser
        processor = PDFParser(str(in_path), {'lang': args.lang})
        processor.run(str(out_dir))
    except ImportError:
        print("Error: PyMuPDF required for PDF. Run: pip install pymupdf")
        raise SystemExit(1)
```

Add `import sys` at top of file if not present.

- Update argparse description to include `.pdf` in supported formats.
- Update the error message for unsupported formats to include `.pdf`.

---

## Fix 4 — EPUB asset name collision (`ingest.py`)

**Problem:** When extracting EPUB assets, paths are flattened by replacing `/` with `_`. If two assets have paths that produce the same flattened name after replacement (e.g., `ch1/images/icon.png` and `ch2/images/icon.png` → both map differently, BUT if the EPUB happens to have files whose flattened name collides), assets overwrite each other silently.

**Fix in `ingest_epub()`:** Track used asset names and add a numeric suffix on collision.

Replace the asset extraction loop's naming logic:
```python
safe = href.replace('/', '_').replace('..', '')
```
With a dedup approach:
```python
_used_asset_names = {}  # defined before the asset extraction loop

# in the loop:
candidate = href.replace('/', '_').replace('..', '')
if candidate in _used_asset_names:
    base, ext = os.path.splitext(candidate)
    _used_asset_names[candidate] += 1
    candidate = f"{base}_{_used_asset_names[candidate]}{ext}"
else:
    _used_asset_names[candidate] = 0
safe = candidate
```

Also update `fix_asset_path()` to use the same dedup dict. Actually, `fix_asset_path` runs AFTER extraction, so it needs access to the same mapping. Better approach: build a `href_to_safe` dict during extraction and use it in `fix_asset_path`.

Implementation:
1. Before the asset extraction loop, declare `href_to_safe: dict[str, str] = {}` and `used_names: set[str] = set()`.
2. During extraction: compute `safe`, check for collision, add counter if needed, store `href_to_safe[href] = safe`.
3. In `fix_asset_path`, look up `resolved` in `href_to_safe` instead of recomputing.

---

## Fix 5 — Add `--version` flag to `bundle.cjs`

**Fix:** In `bundle.cjs`, add a version check before the `--help` block:
```js
if (args.includes('--version')) {
  const pkg = require('../package.json');
  console.log(`html-book-bundler v${pkg.version}`);
  process.exit(0);
}
```

Also update `--help` text to mention `--version` flag.

---

## Fix 6 — `dev_server.cjs` argument parsing bug

**Problem:** Lines 7-8 use index-based argument parsing:
```js
const inputDir  = args[args.indexOf('--input') + 1]  || './chapters';
const outputFile = args[args.indexOf('--output') + 1] || './preview.html';
```
If `--input` is absent but other flags are present (e.g., `node dev_server.cjs --port 4000`), then `args.indexOf('--input')` = -1, so `args[-1 + 1]` = `args[0]` = `'--port'`. Since `'--port'` is truthy, `inputDir = '--port'` instead of `'./chapters'`.

**Fix:** Add the same `getArg()` helper used in `bundle.cjs`:
```js
function getArg(flag, fallback = null) {
  const i = args.indexOf(flag);
  if (i === -1 || i + 1 >= args.length || args[i + 1].startsWith('--')) return fallback;
  return args[i + 1];
}
const inputDir   = getArg('--input',  './chapters');
const outputFile = getArg('--output', './preview.html');
```

Also add `--help` output to `dev_server.cjs` showing available flags: `--input`, `--output`, `--port`.

---

## Fix 7 — `autoCollapseLongParas` skips too few block-level tags (`chapter_processor.cjs`)

**Problem:** The guard that prevents collapsing paragraphs containing block elements only checks for `div|details|blockquote|table`. OCR and converter tools sometimes produce `<p>` tags wrapping `<ul>`, `<ol>`, `<pre>`, `<h2>`, `<section>`, `<figure>` — all block-level elements that would produce invalid HTML if the `<p>` wrapper is preserved inside a `<details>`.

**Fix:** Extend the bailout regex in `autoCollapseLongParas`:
```js
// current:
if (/<(?:div|details|blockquote|table)\b/.test(inner)) return match;
// fix:
if (/<(?:div|details|blockquote|table|ul|ol|pre|figure|section|h[1-6])\b/.test(inner)) return match;
```

---

## Version bump & tests

- `package.json`: bump to `8.3.0`
- `bundle.cjs` help text: update to v8.3
- `SKILL.md` and all sub-skill files: update version references from v8.2 to v8.3
- Add lessons learned entry for each fix:
  1. `autoEnrichLists` stats guard: label must be ≤ 35 chars and ≤ 5 words
  2. `ingest.py` now delegates `.pdf` to `pdf_parser_general.py` — unified entry point
  3. EPUB asset dedup: always build a `href_to_safe` mapping during extraction
  4. `dev_server.cjs` getArg pattern: never use raw `indexOf` arithmetic for CLI arg parsing
  5. `autoCollapseLongParas` block-tag guard: include all HTML5 block elements

- Run `node tests/test_bundler.cjs` — all tests must pass.

## Commit message
`fix: v8.3 - remaining fixes (stats guard, PDF unification, EPUB dedup, dev_server args, block-tag guard)`
