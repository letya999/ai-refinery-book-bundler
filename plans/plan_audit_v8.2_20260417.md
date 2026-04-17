# Plan: HTML Book Bundler v8.2 Audit Fixes

**Date:** 2026-04-17  
**Scope:** Fix all issues found in the deep audit pass. No new features — only bug fixes, linter improvements, documentation corrections, and lessons learned.

---

## Files to modify

### 1. `skills/html-book-bundler/scripts/bundle.cjs`

**Fix 1.1 — Version string in --help**  
Line 14: Change `"HTML Book Bundler v8.0"` → `"HTML Book Bundler v8.1"`

**Fix 1.2 — Expand Russian (and English) stop words**  
In the `STOP_WORDS` Set, add these missing high-frequency Russian words:
`это который если когда такой всё было стало может нет есть один два три первый второй каждый всегда уже ещё тоже только после перед между через много других самый просто очень хотя чтобы потому поэтому когда всего лишь никто никогда ведь всем была были`

Also add common English words missing from list:
`you your we our they their its also just more some what when where which who how all any been but get got had has have here him his her into its just like me more most my no now one only our out own said she so some than their them then there these they this too up use was way were what when which who will with`

---

### 2. `skills/html-book-bundler/scripts/chapter_processor.cjs`

**Fix 2.1 — Replace hardcoded `chapterWord` ternary with LANG parameter**  
Current code (around line 223):
```js
const chapterWord = langCode === 'en' ? 'Chapter' : 'Глава';
const kicker = bookTitle
  ? `${bookTitle} • ${chapterWord} ${index + 1}`
  : `${chapterWord} ${index + 1}`;
```

Problem: bypasses i18n system, breaks on any language other than en/ru.

Fix: Load the LANG JSON from the lang directory using `langCode` and use `LANG.chapter`. Since `chapter_processor.cjs` is a module (not the CLI entry), it can't easily load files — instead, add a new parameter `chapterLabel` to `prepareChapter()`:

New signature:
```
prepareChapter(html, index, title, filesArray, globalCSS, bookTitle, skipInsights, langCode, chapterLabel)
```

Where `chapterLabel` defaults to the old ternary fallback if not provided (for backward compat with tests).

In `bundle.cjs`, pass `LANG.chapter` as the `chapterLabel` argument when calling `prepareChapter()`.

Inside `prepareChapter`, use `chapterLabel` in place of `chapterWord`.

Also update `navScript` kicker generation to use the same parameter.

---

### 3. `skills/html-book-bundler/scripts/pdf_parser_general.py`

**Fix 3.1 — Escape chapter title in HTML output**  
In `run()` method, the `full_html` f-string uses `{title}` unescaped in `<title>` and `<h1>` tags.

Change:
```python
f"<title>{title}</title>"
f"<h1>{title}</h1>"
```
To:
```python
f"<title>{html_lib.escape(title)}</title>"
f"<h1>{html_lib.escape(title)}</h1>"
```

---

### 4. `skills/html-book-bundler/scripts/ingest.py`

**Fix 4.1 — Add `lang` attribute to FB2 HTML output**  
In `ingest_fb2()`, the generated HTML uses `<html>` without lang. The function does not receive a lang param. Solution: add optional `lang: str = 'ru'` parameter to `ingest_fb2()`, pass `config.get('lang', 'ru')` from `main()`. 

Actually `ingest_fb2` receives `input_path` and `out_dir`. The lang should come from args. Change the function signature to:
```python
def ingest_fb2(input_path: Path, out_dir: Path, lang: str = 'ru'):
```
And in the HTML template change `<html>` to `<html lang="{lang}">`.

In `main()`, pass `args.lang` (add `--lang` argument to argparse, default `'ru'`).

Also update `ingest_docx()` and `ingest_epub()` similarly — check if EPUB already has lang set, if not set it from args.

Actually for EPUB: the EPUB chapters have their own `<html lang="...">` already — leave them. For DOCX: add `lang` parameter and emit `<html lang="{lang}">`.

**Fix 4.2 — Warn when `.doc` format is passed (binary Word 97)**  
In `main()`, change the `suffix in ('.docx', '.doc')` branch to:
```python
if suffix == '.docx':
    ingest_docx(in_path, out_dir, lang)
elif suffix == '.doc':
    print("Error: .doc (Word 97 binary) is not supported. Please save as .docx and retry.")
    raise SystemExit(1)
```

**Fix 4.3 — Warn about missing DOCX images**  
In `ingest_docx()`, after building paragraphs, check if the Document has any InlineShapes and print a warning:
```python
total_shapes = sum(len(p.runs) for p in doc.paragraphs 
                   if any(hasattr(r, '_element') for r in p.runs))
```
Actually simpler — after the loop, check `doc.inline_shapes`:
```python
if len(doc.inline_shapes) > 0:
    print(f"  Warning: {len(doc.inline_shapes)} inline image(s) detected in DOCX but not extracted (not supported).")
```

---

### 5. `skills/html-book-bundler/scripts/lint_book.py`

**Fix 5.1 — Add `viewBox` check for all SVG elements**  
In `_audit_chapter()`, after the hex color SVG check, add:
```python
# viewBox enforcement
for svg_match in re.finditer(r'<svg([^>]*)>', html, re.I):
    attrs = svg_match.group(1)
    if 'viewBox' not in attrs and 'viewbox' not in attrs.lower():
        self.errors.append(f"{label}: <svg> missing viewBox attribute (required for mobile responsiveness)")
        break  # one error per chapter is enough
```

**Fix 5.2 — Add `user-scalable=no` check in chapters**  
In `_audit_chapter()`, check for viewport meta with user-scalable=no:
```python
if re.search(r'user-scalable\s*=\s*no', html, re.I):
    self.errors.append(f"{label}: viewport meta has user-scalable=no (WCAG 1.4.4 violation)")
```

**Fix 5.3 — Extend SVG hex color check to include `stop-color`, `lighting-color`, `flood-color`**  
In the SVG hex check section, extend the regex to also catch these properties:
```python
attr_hex = re.search(
    r'(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*["\']#[0-9a-fA-F]{3,6}["\']',
    svg, re.I
)
style_hex = re.search(
    r'style\s*=\s*["\'][^"\']*(?:fill|stroke|stop-color|flood-color|lighting-color)\s*:\s*#[0-9a-fA-F]{3,6}',
    svg, re.I
)
```

**Fix 5.4 — Add check for `<html>` missing `lang` attribute in chapters**  
```python
if re.search(r'<html(?![^>]*\blang\s*=)', html, re.I):
    self.warnings.append(f"{label}: <html> element missing lang attribute (accessibility)")
```

---

### 6. `skills/html-book-bundler/assets/theme.css`

**Fix 6.1 — Add `.hero` background override inside `@media (prefers-color-scheme: light)` block**  
Currently the `@media (prefers-color-scheme: light)` block (around line 39-57) updates `:root` vars and `body` background but has no `.hero` override.

Inside the `@media (prefers-color-scheme: light)` block, add:
```css
:root:not([data-theme="dark"]) .hero {
  background: rgba(176,200,224,.3);
}
```
This matches the existing `[data-theme="light"] .hero` override.

---

### 7. `skills/html-book-bundler/templates/default.html`

**Fix 7.1 — Add origin validation to postMessage bridge**  
Current:
```js
window.addEventListener('message', e => {
  if (e.data && e.data.action === 'bookGo') go(e.data.chapterIdx, e.data.anchorId);
});
```

Change to:
```js
window.addEventListener('message', e => {
  if (e.source !== fr.contentWindow) return;
  if (e.data && e.data.action === 'bookGo') go(e.data.chapterIdx, e.data.anchorId);
});
```

**Fix 7.2 — Remove legacy `blob:` from CSP img-src**  
Change:
```
img-src 'self' data: blob:
```
To:
```
img-src 'self' data:
```

---

### 8. `skills/html-book-bundler/SKILL.md`

**Fix 8.1 — Update audit trail**  
- Change `## AUDIT TRAIL / Open` section from "_(none)_" to list the new issues being fixed in v8.2.
- Add a new `## Lessons Learned (2026-04-17, v8.2 audit)` block with these lessons:
  1. **DOCX images are `InlineShape` objects, not paragraphs** — `doc.paragraphs` iteration silently skips all embedded images. Always check `doc.inline_shapes` count and warn.
  2. **Always `html.escape()` ALL config-sourced strings going into HTML** — including chapter titles, not just extracted body content.
  3. **`chapterWord` i18n** — never use hardcoded language ternaries; always route through the LANG object so new languages work automatically.
  4. **FB2/DOCX ingesters must emit `lang` attribute on `<html>`** — inconsistency with `pdf_parser_general.py` was a silent a11y violation.
  5. **`theme.css` hero override must exist in both `[data-theme]` AND `@media (prefers-color-scheme)`** — the OS preference fallback and the explicit toggle are two separate CSS paths.
  6. **Linter must enforce `viewBox` on all SVGs** — a designer rule without linter enforcement is an honor system, not a rule.

**Fix 8.2 — Mark the new resolved issues in audit trail**

---

### 9. `skills/html-book-bundler/ingester/SKILL.md`

**Fix 9.1 — Document PDF pipeline correctly**  
Add a note that PDF files use `../scripts/pdf_parser_general.py` (not `ingest.py`). Mention `extract_pdf_visuals.py` for visual extraction from PDFs.

---

### 10. `skills/html-book-bundler/README.md`

**Fix 10.1 — Fix supported formats table**  
Change the PDF row from listing `ingest.py` to `pdf_parser_general.py`. Add the correct command example.

---

### 11. `skills/html-book-bundler/architect/SKILL.md`

**Fix 11.1 — Clarify blueprint.json is a design artifact, not pipeline input**  
Add a note: "Note: `blueprint.json` is a design communication artifact for the Designer role. It is NOT read by `bundle.cjs` — it guides manual SVG creation in the next step."

---

## Tests to verify
After all changes, run:
```bash
node skills/html-book-bundler/tests/test_bundler.cjs
```
All 17 tests must still pass. The new `chapterLabel` parameter has a default fallback so existing tests are unaffected.

## Version bump
- `package.json`: bump to `8.2.0`
- All SKILL.md files: update version references from v8.1 to v8.2
- `bundle.cjs` help text: update to v8.2

## Commit
Single commit: `fix: audit pass v8.2 - 11 issues resolved`
No AI co-authorship. No emojis.
