const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Universal enrichment helpers (run on every chapter regardless of source)
// ---------------------------------------------------------------------------

/** Wrap <p> blocks longer than LIMIT chars in a collapsible <details>. */
function autoCollapseLongParas(html) {
  const LIMIT = 480;
  // Match <p>...</p> blocks (non-greedy, may span lines)
  return html.replace(/<p>([\s\S]*?)<\/p>/g, (match, inner) => {
    // Skip if inner already contains block-level special containers
    if (/<(?:div|details|blockquote|table)\b/.test(inner)) return match;
    const text = inner.replace(/<[^>]+>/g, '');
    if (text.length <= LIMIT) return match;
    const preview = text.slice(0, 120).replace(/\s+\S*$/, '') + '\u2026';
    return `<details class="long-para"><summary>${preview}</summary><p>${inner}</p></details>`;
  });
}

/** Extract clean Cyrillic sentences and inject as insight pullquotes. */
function isCleanText(s) {
  const good = (s.match(/[а-яёА-ЯЁ\s,.\-—«»""''!?]/g) || []).length;
  return s.length > 0 && good / s.length > 0.72;
}

function autoInjectInsights(html) {
  const candidates = [];
  const paraRe = /<p[^>]*>([\s\S]*?)<\/p>/g;
  let m;
  while ((m = paraRe.exec(html)) !== null && candidates.length < 2) {
    const text = m[1].replace(/<[^>]+>/g, '').trim();
    if (text.length < 160 || text.length > 1000) continue;
    const sents = text.split(/(?<=[.!?])\s+/);
    for (const s of sents) {
      const clean = s.trim();
      if (clean.length >= 45 && clean.length <= 160 && isCleanText(clean)) {
        candidates.push(clean);
        break;
      }
    }
  }
  if (!candidates.length) return html;

  const insertAt = { 4: candidates[0], 10: candidates[1] };
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
 * Prepares a chapter HTML for embedding:
 * 1. Preserves chapter's own styles (or injects globalCSS if none)
 * 2. Wraps body in .wrap if needed, auto-generates hero block if absent
 * 3. Injects inter-chapter navigation script
 * 4. Returns base64-encoded final HTML
 *
 * @param {string} html - raw chapter HTML
 * @param {number} index - 0-based chapter index
 * @param {string} title - chapter title
 * @param {number} totalChapters - total number of chapters (for nav script)
 * @param {string} globalCSS - CSS to inject when chapter has no own styles
 */
function prepareChapter(html, index, title, totalChapters, globalCSS = '') {
  let content = html;

  // Whether chapter already ships its own <style> block(s)
  const hasOwnStyles = /<style[\s\S]*?<\/style>/i.test(content);

  // Inter-chapter navigation: intercepts <a href="chapterN.html"> clicks
  // and routes them through the parent shell via postMessage
  const navScript = `
<script>
(function() {
  const chapterMap = {};
  for (let i = 1; i <= ${totalChapters}; i++) chapterMap['chapter' + i + '.html'] = i - 1;

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

  // Universal enrichment passes (structural, content-agnostic)
  bodyContent = autoCollapseLongParas(bodyContent);
  bodyContent = autoInjectInsights(bodyContent);
  bodyContent = styleFirstPara(bodyContent);

  // Ensure .wrap container exists
  if (!bodyContent.includes('class="wrap"')) {
    if (bodyContent.includes('class="hero"')) {
      // Chapter has a hero block but no .wrap wrapper
      bodyContent = `<main class="wrap">${bodyContent}</main>`;
    } else {
      // Auto-generate hero + wrap
      const h1Match = bodyContent.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
      const leadMatch = bodyContent.match(/<(p|div)[^>]*class="lead"[^>]*>([\s\S]*?)<\/\1>/i);
      const h1 = h1Match ? h1Match[1] : title;
      const lead = leadMatch ? leadMatch[2] : '';
      let clean = bodyContent;
      if (h1Match) clean = clean.replace(h1Match[0], '');
      if (leadMatch) clean = clean.replace(leadMatch[0], '');

      bodyContent = `
<main class="wrap">
  <section class="hero">
    <div class="kicker">Методология P3.express • Глава ${index + 1}</div>
    <h1>${h1}</h1>
    <p class="lead">${lead}</p>
  </section>
  <div class="content-body">${clean}</div>
</main>`;
    }
  }

  // Build <head> styles — additive layering:
  // 1. Shared theme always injected first (base variables + all common components)
  // 2. Chapter-specific styles appended after (override via CSS cascade as needed)
  // This ensures consistent base AND full chapter richness for all chapters.
  const sharedBlock = globalCSS ? `<style>\n/* === SHARED THEME === */\n${globalCSS}\n</style>` : '';
  const chapterStyles = hasOwnStyles
    ? (content.match(/<style[\s\S]*?<\/style>/gi) || []).join('\n')
    : '';
  const styleBlock = [sharedBlock, chapterStyles].filter(Boolean).join('\n');

  const finalHtml = [
    '<!DOCTYPE html>',
    '<html lang="ru">',
    '<head>',
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    styleBlock,
    '</head>',
    `<body>${bodyContent}${navScript}</body>`,
    '</html>',
  ].join('\n');

  return Buffer.from(finalHtml, 'utf8').toString('base64');
}

module.exports = { prepareChapter };
