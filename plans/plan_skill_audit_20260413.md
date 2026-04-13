# Plan: Full Skill Audit & Improvement

## Problems Found

### Critical Bugs
1. `theme.css` uses `var(--fg)` in `blockquote.insight p` — variable never defined (should be `--txt`)
2. `chapter_processor.cjs:150` — hero kicker hardcoded to "Методология P3.express" — wrong for every other book
3. `lint_book.py` regex: `r'const\s+LOCAL_B64\s*='` never matches — bundler outputs `LOCAL_B64_CHAPTERS`
4. `test_bundler.cjs` structural check is logically inverted — passes when it should fail

### Shell Problems
5. `default.html` — no CSP meta tag (lint_book.py flags it as ERROR on every run)
6. `default.html` — title hardcoded to "Интерактивная книга"
7. `bundle.cjs` — replaces dead placeholders `{{VOL_MAP}}`, `{{VOL_FILES}}`, `{{CURRENT_VOL}}`, `{{LOCAL_START_IDX}}` that `default.html` doesn't use

### Quality
8. No `@media (prefers-reduced-motion: reduce)` in theme.css — audit script warns every time
9. Search index stores full raw HTML-stripped text of all chapters — can be 500KB+, slow initial parse
10. `chapter_processor.cjs` — kicker title not configurable; bundle.cjs doesn't pass book title to prepareChapter

### Clutter
11. Dead files: `bundle_v6_final.cjs`, `bundle_logic_update.txt`, `example_script.cjs`, `example_asset.txt`, `example_reference.md`

### Documentation
12. `SKILL.md` outdated: doesn't mention chapter_processor.cjs, visual types, PDF/OCR workflow, lessons learned

---

## Fixes

### theme.css
- Change `color: var(--fg)` to `color: var(--txt)` in `blockquote.insight p`
- Add `@media (prefers-reduced-motion: reduce) { *, .hero { animation: none !important; transition: none !important; } }`

### chapter_processor.cjs
- `prepareChapter()`: add `bookTitle` param (5th param, default `''`)
- Use it in kicker: `Методология P3.express` → `${bookTitle ? bookTitle + ' • ' : ''}Глава ${index + 1}`
- bundle.cjs: pass the BOOK_ID (or deduce from output filename) as bookTitle

### default.html
- Add `<meta http-equiv="Content-Security-Policy" ...>` with `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'data: blob:'; media-src 'data: blob:'; connect-src 'none';`
- Set `<title>` to use BOOK_ID: `<title>{{BOOK_ID}}</title>`

### bundle.cjs
- Remove dead `{{VOL_MAP}}`, `{{VOL_FILES}}`, `{{CURRENT_VOL}}`, `{{LOCAL_START_IDX}}` replacements
- Search index: strip to max 800 chars per chapter (enough for search, not megabytes of text)
- Pass book title to prepareChapter: `prepareChapter(content, idx, title, files.length, globalCSS, bookTitle)`

### lint_book.py
- Fix regex: `LOCAL_B64` → `LOCAL_B64_CHAPTERS`

### test_bundler.cjs
- Fix inverted logic: check `out.includes('window.parent')` (should be present from nav script)

### Clean up
- Delete: `bundle_v6_final.cjs`, `bundle_logic_update.txt`, `example_script.cjs`, `example_asset.txt`, `example_reference.md`

### SKILL.md
- Rewrite to v4.0: document chapter_processor.cjs enrichment pipeline
- Document visual types system (for custom book scripts)
- Document PDF/OCR → chapters workflow (new lesson from this session)
- Add Lessons Learned section
- Correct all command examples and variable names
