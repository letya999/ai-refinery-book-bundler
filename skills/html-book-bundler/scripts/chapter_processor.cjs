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

  const parts = html.split('</p>');
  if (candidates[1] && parts.length > 10) {
    parts[10] = `\n<blockquote class="insight"><p>${candidates[1]}</p></blockquote>\n` + parts[10];
  }
  if (candidates[0] && parts.length > 4) {
    parts[4] = `\n<blockquote class="insight"><p>${candidates[0]}</p></blockquote>\n` + parts[4];
  }
  return parts.join('</p>');
}

/** Add lead-para class to the first <p> in the document. */
function styleFirstPara(html) {
  let done = false;
  return html.replace(/<p(\s[^>]*)?>/i, (match, attrs) => {
    if (done) return match;
    done = true;
    if (attrs && attrs.includes('lead-para')) return match;
    const newAttrs = attrs ? attrs.replace(/class="([^"]*)"/, 'class="$1 lead-para"') : ' class="lead-para"';
    if (attrs && !attrs.includes('class=')) {
        return `<p${attrs} class="lead-para">`;
    }
    return `<p${newAttrs}>`;
  });
}

/** 
 * Automatically transform simple lists (3-6 items) into visual grids/cards.
 * Heuristic: if items are short and there's no nested markup.
 */
function autoEnrichLists(html) {
  return html.replace(/<(ul|ol)>([\s\S]*?)<\/\1>/g, (match, tag, inner) => {
    const items = inner.match(/<li>([\s\S]*?)<\/li>/g);
    if (!items || items.length < 3 || items.length > 6) return match;
    
    // Check if items are "clean" (short text, no complex tags)
    const isSimple = items.every(li => {
      const text = li.replace(/<[^>]+>/g, '').trim();
      return text.length > 0 && text.length < 120 && !/<(?:table|blockquote|details|div|ul|ol)\b/.test(li);
    });

    if (!isSimple) return match;

    // Pattern 1: Stats (Key: Value)
    const stats = items.map(li => {
      const text = li.replace(/<[^>]+>/g, '').trim();
      const m = text.match(/^([^:—]+)[:—]\s*(.+)$/);
      return m ? { label: m[1].trim(), val: m[2].trim() } : null;
    });

    if (stats.every(s => s !== null)) {
      const cards = stats.map(s => 
        `<div class="stat"><b class="stat-num">${s.label}</b><span class="stat-label">${s.val}</span></div>`
      ).join('\n');
      return `<div class="stats">\n${cards}\n</div>`;
    }

    // Pattern 2: Simple cards
    const cards = items.map(li => {
      const text = li.replace(/<[^>]+>/g, '').trim();
      // If it has a bold prefix, use it as card title
      const m = li.match(/<li><b>(.*?)<\/b>[:.\s]*(.*?)<\/li>/i);
      if (m) {
        return `<div class="card"><b>${m[1]}</b><p>${m[2] || ''}</p></div>`;
      }
      return `<div class="card"><p>${text}</p></div>`;
    }).join('\n');
    
    return `<div class="grid">\n${cards}\n</div>`;
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
 * @param {string[]} filesArray  - ordered array of chapter filenames (e.g. ['chapter1.html', ...])
 * @param {string} globalCSS     - CSS to inject as shared theme base
 * @param {string} bookTitle     - book title for the kicker line (optional)
 * @param {boolean} skipInsights - whether to skip auto-injecting insights
 * @param {string} langCode      - UI language code (e.g., 'ru' or 'en')
 */
function prepareChapter(html, index, title, filesArray, globalCSS = '', bookTitle = '', skipInsights = false, langCode = 'ru') {
  let content = html;

  const hasOwnStyles = /<style[\s\S]*?<\/style>/i.test(content);

  // Inter-chapter navigation script.
  // The closing </script> tag is appended via concatenation so the template literal
  // never contains the raw closing tag sequence (which causes issues in certain parsers).
  const navScriptClose = '</' + 'script>';
  const navScript = `
<script>
(function() {
  const fileArray = ${JSON.stringify(filesArray)};
  const chapterMap = {};
  fileArray.forEach((f, i) => {
    chapterMap[f] = i;
    chapterMap[f.toLowerCase()] = i;  // case-insensitive fallback
    // Keep support for padded links
    const m = f.match(/chapter(\\d+)\\.html/);
    if (m) {
      const padded = String(m[1]).padStart(3, '0') + '.html';
      chapterMap[padded] = i;
    }
  });

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
` + navScriptClose;

  // Extract body content
  const bodyMatch = content.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  let bodyContent = bodyMatch ? bodyMatch[1] : content;

  // Universal enrichment passes
  bodyContent = autoCollapseLongParas(bodyContent);
  if (!skipInsights) bodyContent = autoInjectInsights(bodyContent);
  bodyContent = styleFirstPara(bodyContent);
  bodyContent = autoEnrichLists(bodyContent);

  // Semantic Quality Check (v5.5)
  const visualTags = /class=["'][^"']*\b(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)\b[^"']*["']|<table>/i;
  if (!visualTags.test(bodyContent)) {
    console.warn(`[Semantic Warning] Chapter ${index + 1} ("${title}") is a "wall of text" with no visual components.`);
  }

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

      const chapterWord = langCode === 'en' ? 'Chapter' : 'Глава';
      const kicker = bookTitle
        ? `${bookTitle} \u2022 ${chapterWord} ${index + 1}`
        : `${chapterWord} ${index + 1}`;
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

  const finalHtml = [
    '<!DOCTYPE html>',
    `<html lang="${langCode}">`,
    '<head>',
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    styleBlock,
    '</head>',
    `<body>${bodyContent}${navScript}</body>`,
    '</html>',
  ].join('\n');

  // Return the plain HTML. The bundler (bundle.cjs) is responsible for escaping
  // </script> in the JSON serialization step to prevent premature script termination.
  return finalHtml;
}

module.exports = { prepareChapter };
