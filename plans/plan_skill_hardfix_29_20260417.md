# Plan: HTML Book Bundler — 29-Issue Hardfix (v8.1)

**Date:** 2026-04-17  
**Scope:** `skills/html-book-bundler/` (all sub-paths relative to repo root `C:\Users\User\a_projects\no_complex_book`)  
**Goal:** Fix all 29 critical/high/medium/low issues found during deep audit. Do NOT add new features beyond what is described.

---

## CRITICAL FIXES (must do first)

### Fix 1 — `scripts/lint_book.py:82` — Python SyntaxError in visual_tags regex

The raw string `r'...[^"']*...'` has an unescaped single-quote inside the character class that prematurely terminates the raw string, causing a Python SyntaxError on import. The entire linter is dead.

**Action:** Replace the `visual_tags` variable in `_audit_chapter` method (around line 82) with a properly escaped version. Use a triple-quoted raw string or escape the inner quote:

```python
visual_tags = r"""class=["'][^"']*\b(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)\b[^"']*["']|<table>"""
```

---

### Fix 2 — `scripts/bundle.cjs:149-157` — STOP_WORDS broken (operator precedence)

`.split()` is called only on the last string literal, not the concatenated whole. The Set receives a single giant string and stop words don't work at all.

**Action:** Wrap the entire concatenated string in parentheses so `.split()` is called on the full combined string:

```js
const STOP_WORDS = new Set(
  ('и в на не с а но из к по за то как что так же это да уж вот ' +
   'он она оно они мы вы я ни ли бы до при про над под без через для ' +
   'the a an of to in is it on at be by this that with from are was were ' +
   'have has had will would can could should may might do does did not ')
  .split(/\s+/).filter(Boolean)
);
```

---

### Fix 3 — `scripts/chapter_processor.cjs:217` — Hardcoded "Глава" ignores langCode

The hero-block kicker always uses the Unicode-escaped Russian word "Глава" regardless of the `langCode` parameter passed to `prepareChapter`.

**Action:** Add a simple inline lookup for the chapter word based on `langCode`, defaulting to Russian:

```js
const chapterWord = langCode === 'en' ? 'Chapter' : 'Глава';
const kicker = bookTitle
  ? `${bookTitle} \u2022 ${chapterWord} ${index + 1}`
  : `${chapterWord} ${index + 1}`;
```

---

### Fix 4 — `templates/default.html:389,417` — XSS via innerHTML with raw chapter title T[i]

Chapter titles from `T[i]` (extracted from `<title>` or `<h1>`) are injected directly into `innerHTML`. A malicious title with HTML tags creates XSS.

**Action:** Add a helper function `esc(s)` at the top of the shell `<script>` block:

```js
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
```

Then replace all `${T[i] || ''}` inside innerHTML assignments with `${esc(T[i] || '')}`. Specifically:
- Line `tt.innerHTML = \`<i>${chLabel}</i> ${T[i] || ''}\`` → `${esc(T[i] || '')}`
- Line `btn.innerHTML = \`<b>${chLabel}</b>${t}...\`` where `t = T[i]` (or however it's referenced) → `${esc(t)}`
- Line in `buildBookmarkList`: `btn.textContent = ...` (already uses textContent — leave as-is)

---

## HIGH PRIORITY FIXES

### Fix 5 — `references/single-file-architecture.md` — Outdated, describes Blob URL not srcdoc

The entire document describes the OLD architecture (Base64 + Blob URL) that was replaced by srcdoc. The linter even flags `URL.createObjectURL` as legacy.

**Action:** Rewrite the document to accurately describe the current srcdoc architecture. Keep it in Russian to match its existing language. Key points to update:
- Replace "Base64 + Blob URL" with "UTF-8 strings in CHAPTERS array, loaded via `iframe.srcdoc`"
- Remove references to `URL.revokeObjectURL()`
- Mention that `</script>` inside chapter HTML is escaped as `<\/script>` in JSON
- Keep the security/offline-first philosophy sections

---

### Fix 6 — `README.md` — References non-existent `audit_single_file_html.py`

The file structure section lists `audit_single_file_html.py` which does not exist. 

**Action:** Remove that line from the file structure listing in `README.md`.

---

### Fix 7 — `scripts/bundle.cjs:13` — `--help` shows "v5.0" instead of v8.0

**Action:** Change the version string in the `--help` console.log output from `v5.0` to `v8.0`.

---

### Fix 8 — `scripts/ingest.py` (ingest_epub function) — EPUB CSS assets silently dropped

EPUB CSS files are saved to `assets/` then `bundleAssets()` converts them to `data:text/css;base64,...` in `href` attributes. But browsers don't apply CSS through `<link href="data:...">` — styles are silently lost.

**Action:** In `ingest_epub`, after reading each spine chapter's HTML, find all `<link rel="stylesheet" href="...">` tags that reference local CSS files (now in `assets/`). Load the CSS file content, inline it as a `<style>` block in the `<head>`, and remove the `<link>` tag.

Implementation sketch in `ingest_epub`:
```python
import re as _re

# After fixing asset paths in html_data, inline linked CSS:
def inline_css(html: str, assets_dir: Path) -> str:
    def replace_link(m):
        href = m.group(1)
        if href.startswith('assets/'):
            css_path = assets_dir / href[len('assets/'):]
            if css_path.exists():
                css_content = css_path.read_text(encoding='utf-8', errors='replace')
                return f'<style>{css_content}</style>'
        return m.group(0)
    return _re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\'][^>]*/?>',
                   replace_link, html, flags=_re.I)

html_data = inline_css(html_data, assets_dir)
```

---

## MEDIUM PRIORITY FIXES

### Fix 9 — `scripts/chapter_processor.cjs:129-134` — JSDoc mismatch

The JSDoc says `@param {number} totalChapters` but the actual parameter is `filesArray` (array of filename strings).

**Action:** Update the JSDoc comment for `prepareChapter` to correctly document `filesArray`:
```js
/**
 * @param {string[]} filesArray - ordered array of chapter filenames (e.g. ['chapter1.html', ...])
 */
```

---

### Fix 10 — `templates/default.html:5` — `user-scalable=no` violates WCAG 1.4.4

**Action:** Change the viewport meta tag from:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```
to:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

---

### Fix 11 — `designer/SKILL.md` — Duplicate item `5.`

Two bullet points are both numbered `5.` (Arrowheads and Vector Scaling).

**Action:** Renumber the second `5.` to `6.` and check that subsequent items are also renumbered correctly (currently no items after the duplicate 5, but verify).

---

### Fix 12 — `assets/theme.css` — Missing `.translator` CSS class

The `.translator` class is checked by the linter, mentioned in SKILL.md as a valid visual component, but has no CSS definition in `theme.css`.

**Action:** Add a `.translator` class definition to `theme.css`. It should be styled as a two-column comparison table (original vs translated concept), consistent with the book's dark/light theme. Example:

```css
/* ── Translator / Concept Map ── */
.translator {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  margin: 24px 0;
}
.translator-from,
.translator-to {
  padding: 16px 20px;
}
.translator-from {
  background: rgba(15,31,56,.5);
  border-right: 1px solid var(--line);
}
.translator-to {
  background: rgba(114,216,255,.06);
}
.translator-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted);
  margin-bottom: 8px;
  font-weight: 700;
}
```

---

### Fix 13 — `scripts/bundle.cjs:92` — `python` vs `python3`

**Action:** Change `spawnSync('python', ...)` to use a cross-platform resolver. Try `python3` first, fall back to `python`:

```js
const pyCmd = (() => {
  const { spawnSync } = require('child_process');
  const r = spawnSync('python3', ['--version'], { stdio: 'pipe' });
  return r.status === 0 ? 'python3' : 'python';
})();
// then use pyCmd instead of 'python' in the spawnSync call
```

---

### Fix 14 — `tests/test_bundler.cjs` — README says 17 tests, only 11 exist

**Action:** Add 6 missing tests to cover:
- Test 12: `--optimize` flag doesn't crash (smoke test, no images present)
- Test 13: `--skip-insights` flag works (verify no `<blockquote class="insight">` auto-injected)
- Test 14: Chapter nav script present (`postMessage` bridge exists in output)
- Test 15: Bookmarks key present in output JS (`getBookmarks` or `bm_`)
- Test 16: Theme toggle button present (`theme-btn`)
- Test 17: `glossary.html` is sorted last when present (create a glossary.html test file, bundle, verify it comes last in CHAPTERS array)

Update `README.md` count: "17 tests" (or update to actual count if some tests are better removed).

---

### Fix 15 — `scripts/pdf_parser_general.py` — Hardcoded `lang="ru"`

**Action:** 
1. Add `--lang` argument to the CLI parser (default `"ru"`)
2. Pass `lang` through `PDFParser.__init__` and `self.config`
3. Use it in the template string: `<html lang="{lang}">`

---

### Fix 16 — `scripts/bundle.cjs` — `--template` flag undocumented in `--help`

**Action:** Add `--template` to the help text in the `console.log` block:
```
  --template <file>   Custom HTML template (default: templates/default.html)
```

---

### Fix 17 — Light theme CSS variable mismatch between shell and theme.css

Shell `default.html` and `theme.css` have slightly different light theme values:

| Variable | default.html | theme.css | Correct value |
|---|---|---|---|
| `--panel` light | `#e4ecf5` | `#dce8f2` | Use `#dce8f2` (theme.css value — more consistent) |
| `--panel2` light | `#d4e2ee` | `#ccdeed` | Use `#ccdeed` (theme.css value) |

**Action:** In `templates/default.html`, in the `[data-theme="light"]` block, update:
- `--panel: #e4ecf5` → `--panel: #dce8f2`
- `--panel2: #d4e2ee` → `--panel2: #ccdeed`

---

### Fix 18 — Version strings out of sync across files

**Action:** Update version strings to `v8.0` / `8.0.0` everywhere:
- `scripts/bundle.cjs`: `--help` text: `v5.0` → `v8.0` (already covered in Fix 7)
- `assets/theme.css`: comment header `v7.1` → `v8.0`
- `scripts/ingest.py`: docstring `v5.0` → `v8.0`

---

### Fix 19 — No `glossary.html` template or example

**Action:** Create `examples/glossary.html` — a minimal but functional glossary chapter template with:
- Correct structure for bundler (`<title>Glossary</title>`)
- At least 3 example terms with proper `id="term_id"` anchors
- Uses `.acc-item`/`.acc-body` accordion pattern for term definitions
- Comment at top explaining the naming convention for term IDs

---

### Fix 20 — Mixed language in `references/` (single-file-architecture.md is in Russian, others in English)

**Action:** Add a note at the top of `references/single-file-architecture.md` (or translate key sections to English). Given the file is being rewritten in Fix 5, write the new version in English to match the other reference docs.

Note: Fix 5 and Fix 20 operate on the same file — combine them: rewrite `single-file-architecture.md` in English with correct srcdoc architecture.

---

## LOW PRIORITY FIXES

### Fix 21 — `scripts/chapter_processor.cjs` — `autoInjectInsights` counter off-by-one

When the first insight is inserted after the 4th `</p>`, the injected blockquote contains `</p>` which the replacement counter counts, shifting the position of the second insight.

**Action:** Change the injection logic to use an index-based approach instead of counting `</p>` replacements. Split by `</p>`, insert at positions 4 and 10 in the array, then rejoin:

```js
function autoInjectInsights(html) {
  // ... (candidate extraction stays the same)
  if (!candidates.length) return html;
  
  const parts = html.split('</p>');
  if (candidates[0] && parts.length > 4) {
    parts[4] = parts[4] + `\n<blockquote class="insight"><p>${candidates[0]}</p></blockquote>`;
  }
  if (candidates[1] && parts.length > 10) {
    parts[10] = parts[10] + `\n<blockquote class="insight"><p>${candidates[1]}</p></blockquote>`;
  }
  return parts.join('</p>');
}
```

Wait — this changes the logic slightly (inserts AFTER the Nth `</p>` segment instead of replacing). Implement carefully to preserve semantics.

---

### Fix 22 — `scripts/optimize_assets.py` — `./` prefix in src attributes breaks path matching

`update_html_references` matches exact filename strings. If HTML has `src="./assets/cover.jpg"` but `rel_old = "assets/cover.jpg"`, the replacement misses.

**Action:** In `update_html_references`, also try replacing with the `./` prefixed version:

```python
content = content.replace(f'"{old_name}"', f'"{new_name}"')
content = content.replace(f'"./{old_name}"', f'"./{new_name}"')
content = content.replace(f"'{old_name}'", f"'{new_name}'")
content = content.replace(f"'./{old_name}'", f"'./{new_name}'")
content = content.replace(f'({old_name})', f'({new_name})')
content = content.replace(f'(./{old_name})', f'(./{new_name})')
```

---

### Fix 23 — `scripts/chapter_processor.cjs` — `styleFirstPara` misses `<p class="...">`

`html.replace(/<p>/, ...)` only matches bare `<p>` without attributes.

**Action:** Change to match `<p>` with optional attributes, and only add `lead-para` if the paragraph doesn't already have that class:

```js
function styleFirstPara(html) {
  let done = false;
  return html.replace(/<p(\s[^>]*)?>/i, (match, attrs) => {
    if (done) return match;
    done = true;
    if (attrs && attrs.includes('lead-para')) return match;
    const newAttrs = attrs ? attrs.replace(/class="([^"]*)"/, 'class="$1 lead-para"') : ' class="lead-para"';
    return `<p${newAttrs}>`;
  });
}
```

---

### Fix 24 — `scripts/chapter_processor.cjs` navScript — case-insensitive chapterMap lookup

`pathPart` is lowercased but `chapterMap` keys are original filenames (may be mixed case).

**Action:** When building `chapterMap`, also add lowercase versions of each key:

```js
fileArray.forEach((f, i) => {
  chapterMap[f] = i;
  chapterMap[f.toLowerCase()] = i;  // case-insensitive fallback
  // ... padded chapter support stays
});
```

---

### Fix 25 — Already covered by Fix 19 (glossary template). Skip.

---

### Fix 26 — `assets/theme.css` — No `prefers-color-scheme` fallback (JS-off scenario)

When JS is disabled, `data-theme` attribute is never set on the chapter iframe's `<html>`, so the theme defaults to dark even on a light system.

**Action:** Add a `@media (prefers-color-scheme: light)` block to `theme.css` that mirrors the `[data-theme="light"]` variable definitions:

```css
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --bg:    #f0f4f8;
    --bg2:   #e8eef5;
    /* ... all light theme variables ... */
  }
}
```

This uses `:root:not([data-theme="dark"])` so that explicit dark mode selection from JS overrides the media query.

---

### Fix 27 — `templates/default.html` — Add `chapter_label` LANG key for hero via kicker

This is already handled by Fix 3 in `chapter_processor.cjs`. No separate action needed in `default.html`. But verify that `en.json` and `ru.json` both already have `"chapter_label"` key (they do — confirmed in audit). Mark as done via Fix 3.

---

### Fix 28 — `scripts/bundle.cjs` — No validation of `--lang` value

**Action:** After reading `langCode`, add a validation check:

```js
const SUPPORTED_LANGS = ['ru', 'en'];
if (!SUPPORTED_LANGS.includes(langCode)) {
  console.warn(`Warning: unsupported --lang value "${langCode}". Falling back to "ru". Supported: ${SUPPORTED_LANGS.join(', ')}`);
  // langCode will fall back because langFile won't exist, which already falls back to ru.json
}
```

---

### Fix 29 — `scripts/dev_server.cjs` — No graceful handling of EADDRINUSE

**Action:** Read `dev_server.cjs` first to understand its server setup, then wrap the `server.listen()` call with an error handler:

```js
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`Error: port ${PORT} is already in use. Try a different port with --port <N>`);
    process.exit(1);
  }
  throw err;
});
```

Also add `--port` CLI argument support if not already present.

---

## SKILL.md Updates

After all code fixes are applied, update `SKILL.md` by appending to the "Lessons Learned" section:

```markdown
## Lessons Learned (2026-04-17):
- **STOP_WORDS JS bug:** `.split()` chain must be wrapped in `()` when building from concatenated string literals — operator precedence calls `.split()` only on the last literal otherwise.
- **Python raw string quotes:** In `r'...'` strings, an unescaped `'` inside `[^"']` terminates the raw string. Use `r"""..."""` triple quotes or escape as `[^"\'` for character classes containing single quotes.
- **langCode propagation:** `prepareChapter` receives `langCode` but had no access to LANG object for hero block generation. Chapter-level i18n strings must be derived from `langCode` directly or LANG must be passed down.
- **`user-scalable=no` is WCAG 1.4.4 violation:** Never disable pinch-to-zoom; users with low vision need it.
- **EPUB CSS via data URI href doesn't work:** Browsers ignore `<link href="data:text/css;base64,...">` as stylesheets. CSS must be inlined as `<style>` blocks.
- **Non-existent files in README:** Always verify all referenced filenames exist before committing documentation.
```

---

## Execution Order

1. Fixes 1-4 (Critical) — standalone, no dependencies
2. Fixes 5+20 (combined — same file), 6, 7, 8 (High)
3. Fixes 9-16 (Medium) — any order
4. Fix 17, 18 (CSS sync, version strings) — cosmetic
5. Fix 19 (new file glossary.html example)
6. Fixes 21-29 (Low) — any order
7. SKILL.md update — last

---

## Files to Modify

| File | Fixes Applied |
|---|---|
| `scripts/lint_book.py` | 1 |
| `scripts/bundle.cjs` | 2, 7, 13, 16, 28 |
| `scripts/chapter_processor.cjs` | 3, 9, 21, 23, 24 (navScript inline in prepareChapter) |
| `templates/default.html` | 4, 10, 17 |
| `references/single-file-architecture.md` | 5, 20 |
| `README.md` | 6 |
| `scripts/ingest.py` | 8, 18 |
| `designer/SKILL.md` | 11 |
| `assets/theme.css` | 12, 18, 26 |
| `scripts/pdf_parser_general.py` | 15 |
| `tests/test_bundler.cjs` | 14 |
| `scripts/optimize_assets.py` | 22 |
| `scripts/dev_server.cjs` | 29 |
| `SKILL.md` | Lessons Learned update |
| **NEW** `examples/glossary.html` | 19 |

---

## Constraints

- Do NOT change any book-output visual design beyond the `.translator` CSS addition and CSS variable sync.
- Do NOT refactor code beyond what is required to fix each specific issue.
- Do NOT add new CLI flags beyond `--port` for dev_server and `--lang` validation (which is a warning only).
- All Python files must remain compatible with Python 3.9+.
- All JS must remain CommonJS (`.cjs`), no ES modules.
- Do not add any `console.log` beyond what's needed for the fixes.
