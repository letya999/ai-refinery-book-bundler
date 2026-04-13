# Plan: Skill upgrade — universal enrichment in chapter_processor.cjs

## Goal
Lift universal visual improvements into the skill itself so ANY book bundled through
`bundle.cjs` automatically gets them — without needing book-specific scripts.

## Files to modify

### 1. `skills/html-book-bundler/scripts/chapter_processor.cjs`

Add three post-processing passes that run on every chapter's HTML body,
AFTER CSS injection but BEFORE base64 encoding.

The current flow in `prepareChapter()`:
  1. Extract `<body>` content
  2. Inject shared CSS + chapter styles
  3. Inject nav script
  4. Base64 encode

New flow:
  1. Extract `<body>` content
  2. Inject shared CSS + chapter styles
  3. **autoCollapseLongParas(bodyContent)**  ← new
  4. **autoInjectInsights(bodyContent)**     ← new
  5. **styleFirstPara(bodyContent)**         ← new
  6. Inject nav script
  7. Base64 encode

---

#### Pass 1: `autoCollapseLongParas(html)`

Regex-replace every `<p>...</p>` whose text content exceeds 480 characters
with a `<details class="long-para"><summary>{preview}</summary><p>...</p></details>`.

Preview = first 120 chars of text content (strip inner tags) + "…"

Skip `<p>` tags that are already inside `.letter-q`, `.letter-a`, `.summary-box`,
`.success-story`, `.workbook`, `blockquote`, or `details` — check by testing that
the `<p>` is a direct child context (use a simple heuristic: don't replace `<p>`
that appears inside another block element in the same match).

Implementation approach: parse with regex `/<p>([^<]{480,}(?:<[^>]+>[^<]*<\/[^>]+>)*[^<]*)<\/p>/g`
is fragile — instead use a line-by-line state machine: collect all `<p>...</p>` blocks
(potentially multi-line), measure stripped text length, wrap if > 480.

```javascript
function autoCollapseLongParas(html) {
  // Match standalone <p>...</p> blocks (not inside special divs)
  // Use a simple approach: find <p> blocks and check length
  const LIMIT = 480;
  return html.replace(/<p>([\s\S]*?)<\/p>/g, (match, inner) => {
    // Skip if inside a special container (heuristic: inner contains class= divs)
    if (/<div\s|<blockquote|<details/.test(inner)) return match;
    const text = inner.replace(/<[^>]+>/g, '');
    if (text.length <= LIMIT) return match;
    const preview = text.slice(0, 120).replace(/\s+\S*$/, '') + '…';
    return `<details class="long-para"><summary>${preview}</summary><p>${inner}</p></details>`;
  });
}
```

---

#### Pass 2: `autoInjectInsights(html)`

Scan the HTML for short (45–150 char), sentence-complete text nodes that look like
key principles. Inject a `<blockquote class="insight">` after every 6th direct `<p>`
in the content body using the extracted sentence as the quote.

If no good sentence is found, use a placeholder from the chapter title.

Algorithm:
1. Find all `<p>text</p>` blocks where stripped text is 200–800 chars
2. From each, extract first sentence ending in [.!?] that is 45–150 chars
3. Collect up to 2 candidates (skip ones with OCR garbage: >15% non-Cyrillic/non-space)
4. Insert first candidate after the 4th `<p>`, second after the 10th `<p>` (if exists)

```javascript
function isCleanSentence(s) {
  const cyrCount = (s.match(/[а-яёА-ЯЁ\s,—«»""'']/g) || []).length;
  return cyrCount / s.length > 0.75;
}

function autoInjectInsights(html) {
  // Extract candidate sentences
  const candidates = [];
  const paraRegex = /<p>([\s\S]*?)<\/p>/g;
  let m;
  while ((m = paraRegex.exec(html)) !== null) {
    const text = m[1].replace(/<[^>]+>/g, '').trim();
    if (text.length < 150 || text.length > 900) continue;
    // Split into sentences
    const sents = text.split(/(?<=[.!?])\s+/);
    for (const s of sents) {
      if (s.length >= 45 && s.length <= 150 && isCleanSentence(s)) {
        candidates.push(s.trim());
        break;
      }
    }
    if (candidates.length >= 2) break;
  }

  if (candidates.length === 0) return html;

  // Insert insights after Nth <p>
  const positions = [4, 10]; // after 4th and 10th <p>
  let pCount = 0;
  const insertions = {};
  positions.forEach((pos, i) => {
    if (candidates[i]) insertions[pos] = candidates[i];
  });

  return html.replace(/<\/p>/g, (match) => {
    pCount++;
    const quote = insertions[pCount];
    if (quote) {
      return `</p>\n<blockquote class="insight"><p>${quote}</p></blockquote>`;
    }
    return match;
  });
}
```

---

#### Pass 3: `styleFirstPara(html)`

Add `class="lead-para"` to the very first `<p>` inside `.content-body` (or the
first `<p>` in body if no `.content-body`). This makes the opening paragraph
slightly larger and more prominent.

```javascript
function styleFirstPara(html) {
  let done = false;
  return html.replace(/<p>/, (match) => {
    if (done) return match;
    done = true;
    return '<p class="lead-para">';
  });
}
```

---

#### Integration into `prepareChapter()`:

After the existing CSS injection block and before the navScript injection,
add the three passes on `bodyContent`:

```javascript
bodyContent = autoCollapseLongParas(bodyContent);
bodyContent = autoInjectInsights(bodyContent);
bodyContent = styleFirstPara(bodyContent);
```

---

### 2. `skills/html-book-bundler/assets/theme.css`

Append new CSS rules for the three new components:

```css
/* === UNIVERSAL ENRICHMENTS (chapter_processor) === */

/* Long-paragraph collapse */
details.long-para {
  margin-bottom: 14px;
  border-left: 2px solid var(--line);
  padding-left: 14px;
}
details.long-para summary {
  cursor: pointer;
  color: var(--acc);
  font-size: .88rem;
  padding: 4px 0;
  list-style: none;
  user-select: none;
  outline: none;
}
details.long-para summary::marker { display: none; content: ''; }
details.long-para[open] summary { display: none; }
details.long-para[open] > p { margin-top: 8px; }

/* Auto-extracted insight pullquotes */
blockquote.insight {
  margin: 24px 0;
  padding: 16px 20px;
  border-left: 4px solid var(--acc);
  background: rgba(114, 216, 255, 0.06);
  border-radius: 0 12px 12px 0;
}
blockquote.insight p {
  margin: 0;
  font-size: 1.05rem;
  font-style: italic;
  line-height: 1.65;
  color: var(--fg);
}

/* Lead paragraph (first para of chapter) */
.lead-para {
  font-size: 1.08rem;
  line-height: 1.8;
  color: var(--fg);
  opacity: .95;
}
```

---

## Execution order

1. Edit `skills/html-book-bundler/scripts/chapter_processor.cjs`:
   - Add `isCleanSentence()`, `autoCollapseLongParas()`, `autoInjectInsights()`, `styleFirstPara()` functions
   - Call all three inside `prepareChapter()` on `bodyContent` before nav script injection

2. Edit `skills/html-book-bundler/assets/theme.css`:
   - Append the new CSS block at the end

3. Verify by running:
   `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_ne_uslozhnyay --output ne-uslozhnyay-ULTIMATE-v6.html`
   and also:
   `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_nravites --output nravites-book.html`
   Both should show collapsed long paragraphs and insight quotes in Playwright.

## Important notes
- The `autoCollapseLongParas` must NOT double-wrap — if a `<p>` is already inside a `<details>`, skip it
- The `autoInjectInsights` should only inject if `candidates.length > 0` — never inject empty blockquotes
- These passes are additive: book-specific scripts (like convert_book.py) can pre-generate their own insights/collapses; the skill's passes will skip already-short paragraphs and add further auto-insights from the remaining text
- Do NOT modify `bundle_v6_final.cjs` — it is a legacy script
