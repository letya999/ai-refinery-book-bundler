const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Universal enrichment helpers (run on every chapter regardless of source)
// ---------------------------------------------------------------------------

/** Wrap <p> blocks longer than LIMIT chars in a collapsible <details>. */
function autoCollapseLongParas(html) {
  const LIMIT = 480;
  return html.replace(/<p>([\s\S]*?)<\/p>/g, (match, inner) => {
    if (/<(?:div|details|blockquote|table)\b/.test(inner)) return match;
    const text = inner.replace(/<[^>]+>/g, '');
    if (text.length <= LIMIT) return match;
    const preview = text.slice(0, 120).replace(/\s+\S*$/, '') + '\u2026';
    return `<details class="long-para"><summary>${preview}</summary><p>${inner}</p></details>`;
  });
}

/**
 * Language-agnostic text quality check.
 * A sentence is clean if: not too short, not ALL-CAPS, mostly word characters.
 */
function isCleanText(s) {
  if (s.length < 30 || s.length > 200) return false;
  if (s === s.toUpperCase() && s.length > 20) return false;
  const wordChars = (s.match(/[\p{L}\p{N}\s,.\-!?]/gu) || []).length;
  return wordChars / s.length > 0.75;
}

/** Extract clean sentences and inject as insight pullquotes after 4th and 10th </p>. */
function autoInjectInsights(html) {
  const candidates = [];
  const paraRe = /<p[^>]*>([\s\S]*?)<\/p>/g;
  let m;
  while ((m = paraRe.exec(html)) !== null && candidates.length < 2) {
    const text = m[1].replace(/<[^>]+>/g, '').trim();
    if (text.length < 80 || text.length > 1200) continue;
    const sents = text.split(/(?<=[.!?])\s+/);
    for (const s of sents) {
      const clean = s.trim();
      if (clean.length >= 45 && clean.length <= 180 && isCleanText(clean)) {
        candidates.push(clean);
        break;
      }
    }
  }
  if (!candidates.length) return html;

  const insertAt = {};
  if (candidates[0]) insertAt[4]  = candidates[0];
  if (candidates[1]) insertAt[10] = candidates[1];

  let pCount = 0;
  return html.replace(/<\/p>/g, end => {
    pCount++;
    const quote = insertAt[pCount];
    if (quote) return `</p>\n<blockquote class="insight"><p>${quote}</p></blockquote>`;
    return end;
  });
}

/** Add lead-para class to the first <p> in the document. */
function styleFirstPara(html) {
  let done = false;
  return html.replace(/<p>/, match => {
    if (done) return match;
    done = true;
    return '<p class="lead-para">';
  });
}

// ---------------------------------------------------------------------------

/**
 * Prepares a chapter HTML for embedding in the shell via srcdoc:
 * 1. Preserves chapter's own styles (or injects globalCSS if none)
 * 2. Wraps body in .wrap if needed, auto-generates hero block if absent
 * 3. Injects inter-chapter navigation script
 * 4. Returns final HTML as a UTF-8 string (not base64 — caller uses srcdoc)
 *
 * @param {string} html          - raw chapter HTML
 * @param {number} index         - 0-based chapter index
 * @param {string} title         - chapter title
 * @param {number} totalChapters - total number of chapters (for nav script)
 * @param {string} globalCSS     - CSS to inject as shared theme base
 * @param {string} bookTitle     - book title for the kicker line (optional)
 */
function prepareChapter(html, index, title, totalChapters, globalCSS = '', bookTitle = '', skipInsights = false) {
  let content = html;

  const hasOwnStyles = /<style[\s\S]*?<\/style>/i.test(content);

  // Inter-chapter navigation: intercept <a href="chapterN.html"> clicks
  // and route through parent shell via postMessage
  const navScript = `
<script>
(function() {
  // Map both chapter1.html and 001.html patterns to 0-based indices
  const chapterMap = {};
  for (let i = 1; i <= ${totalChapters}; i++) {
    chapterMap['chapter' + i + '.html'] = i - 1;
    const padded = String(i).padStart(3, '0') + '.html';
    chapterMap[padded] = i - 1;
  }

  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('data:')) return;

    e.preventDefault();
    const parts = href.split('#');
    const pathPart = parts[0].toLowerCase();
    const anchor = parts[1] || null;

    let targetIdx = chapterMap[pathPart];
    if (targetIdx === undefined && pathPart.includes('chapter')) {
      const m = pathPart.match(/chapter(\\d+)/);
      if (m) targetIdx = parseInt(m[1]) - 1;
    }

    if (targetIdx !== undefined) {
      window.parent.postMessage({ action: 'bookGo', chapterIdx: targetIdx, anchorId: anchor }, '*');
    } else if (anchor) {
      const el = document.getElementById(anchor);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  });
})();
</script>`;

  // Extract body content
  const bodyMatch = content.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  let bodyContent = bodyMatch ? bodyMatch[1] : content;

  // Universal enrichment passes
  bodyContent = autoCollapseLongParas(bodyContent);
  if (!skipInsights) bodyContent = autoInjectInsights(bodyContent);
  bodyContent = styleFirstPara(bodyContent);

  // Ensure .wrap container exists
  if (!bodyContent.includes('class="wrap"')) {
    if (bodyContent.includes('class="hero"')) {
      bodyContent = `<main class="wrap">${bodyContent}</main>`;
    } else {
      const h1Match = bodyContent.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
      const leadMatch = bodyContent.match(/<(p|div)[^>]*class="lead"[^>]*>([\s\S]*?)<\/\1>/i);
      const h1 = h1Match ? h1Match[1] : title;
      const lead = leadMatch ? leadMatch[2] : '';
      let clean = bodyContent;
      if (h1Match) clean = clean.replace(h1Match[0], '');
      if (leadMatch) clean = clean.replace(leadMatch[0], '');

      const kicker = bookTitle ? `${bookTitle} \u2022 \u0413\u043b\u0430\u0432\u0430 ${index + 1}` : `\u0413\u043b\u0430\u0432\u0430 ${index + 1}`;
      bodyContent = `
<main class="wrap">
  <section class="hero">
    <div class="kicker">${kicker}</div>
    <h1>${h1}</h1>
    <p class="lead">${lead}</p>
  </section>
  <div class="content-body">${clean}</div>
</main>`;
    }
  }

  // Build <head>: shared theme first, then chapter overrides (cascade)
  const sharedBlock = globalCSS ? `<style>\n/* === SHARED THEME === */\n${globalCSS}\n</style>` : '';
  const chapterStyles = hasOwnStyles
    ? (content.match(/<style[\s\S]*?<\/style>/gi) || []).join('\n')
    : '';
  const styleBlock = [sharedBlock, chapterStyles].filter(Boolean).join('\n');

  return [
    '<!DOCTYPE html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    styleBlock,
    '</head>',
    `<body>${bodyContent}${navScript}</body>`,
    '</html>',
  ].join('\n');
}

module.exports = { prepareChapter };
