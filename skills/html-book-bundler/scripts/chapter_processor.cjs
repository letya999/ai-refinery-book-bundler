const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

// ---------------------------------------------------------------------------
// Universal enrichment helpers (run on every chapter regardless of source)
// ---------------------------------------------------------------------------

function isCleanText(s) {
  if (s.length < 30 || s.length > 200) return false;
  if (s === s.toUpperCase() && s.length > 20) return false;
  const wordChars = (s.match(/[\p{L}\p{N}\s,.\-!?]/gu) || []).length;
  return wordChars / s.length > 0.75;
}

function processWithCheerio(html, skipInsights) {
  const $ = cheerio.load(html, { decodeEntities: false }, false);

  // 0. Robust Sanitization (AST-based)
  // Strip dangerous elements
  $('script, object, embed, applet, iframe, meta, base, link[rel="import"]').remove();
  // Strip dangerous attributes (inline event handlers and javascript: URIs)
  $('*').each((_, el) => {
    const attribs = el.attribs;
    if (!attribs) return;
    for (const attr in attribs) {
      if (attr.startsWith('on')) {
        $(el).removeAttr(attr);
      } else if ((attr === 'href' || attr === 'src') && attribs[attr].trim().toLowerCase().startsWith('javascript:')) {
        $(el).attr(attr, '#');
      }
    }
  });

  // 1. autoCollapseLongParas
  const LIMIT = 480;
  const blockTags = ['div', 'details', 'blockquote', 'table', 'section', 'article', 'aside', 'header', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li'];
  
  $('p').each((_, el) => {
    const $p = $(el);
    const hasBlock = blockTags.some(tag => $p.find(tag).length > 0);
    if (hasBlock) return;

    const text = $p.text();
    if (text.length > LIMIT) {
      const preview = text.slice(0, 120).replace(/\s+\S*$/, '') + '\u2026';
      const $details = $('<details class="long-para"><summary></summary></details>');
      $details.find('summary').text(preview);
      $p.wrap($details);
    }
  });

  // 2. autoInjectInsights
  if (!skipInsights) {
    const candidates = [];
    const $topParas = $('body > p, .content-body > p'); // Only top-level or main content paragraphs
    
    $topParas.each((_, el) => {
      if (candidates.length >= 2) return false;
      const $p = $(el);
      const text = $p.text().trim();
      if (text.length < 80 || text.length > 1200) return;
      
      const sents = text.split(/(?<=[.!?])\s+/);
      for (const s of sents) {
        const clean = s.trim();
        if (clean.length >= 45 && clean.length <= 180 && isCleanText(clean)) {
          candidates.push({ text: clean, el: el });
          break;
        }
      }
    });

    if (candidates[1] && $topParas.length > 10) {
      const $target = $($topParas[10]);
      $target.before(`\n<blockquote class="insight"><p>${candidates[1].text}</p></blockquote>\n`);
    }
    if (candidates[0] && $topParas.length > 4) {
      const $target = $($topParas[4]);
      $target.before(`\n<blockquote class="insight"><p>${candidates[0].text}</p></blockquote>\n`);
    }
  }

  // 3. styleFirstPara
  const $firstP = $('p').first();
  if ($firstP.length && !$firstP.hasClass('lead-para')) {
    $firstP.addClass('lead-para');
  }

  // 4. autoEnrichLists
  $('ul').each((_, el) => {
    const $ul = $(el);
    if ($ul.attr('class')) return; // author explicitly styled this

    const $items = $ul.children('li');
    if ($items.length < 3 || $items.length > 6) return;

    let isSimple = true;
    $items.each((i, li) => {
      const $li = $(li);
      const text = $li.text().trim();
      if (text.length === 0 || text.length >= 120 || $li.find('table, blockquote, details, div, ul, ol').length > 0) {
        isSimple = false;
        return false; // break
      }
    });

    if (!isSimple) return;

    // Pattern 1: Stats (Key: Value)
    const stats = [];
    let isStats = true;
    $items.each((i, li) => {
      const text = $(li).text().trim();
      const m = text.match(/^([^:—]+)[:—]\s*(.+)$/);
      if (!m) { isStats = false; return false; }
      const label = m[1].trim();
      const val = m[2].trim();
      if (label.length > 35 || label.split(/\s+/).length > 5) { isStats = false; return false; }
      stats.push({ label, val });
    });

    if (isStats && stats.length === $items.length) {
      const $grid = $('<div class="stats"></div>');
      stats.forEach(s => {
        $grid.append(`\n<div class="stat"><b class="stat-num">${s.label}</b><span class="stat-label">${s.val}</span></div>`);
      });
      $ul.replaceWith($grid);
      return;
    }

    // Pattern 2: Simple cards
    const $grid = $('<div class="grid"></div>');
    $items.each((i, li) => {
      const $li = $(li);
      const text = $li.text().trim();
      // Check if starts with bold
      const $b = $li.find('b').first();
      if ($b.length && $li.html().startsWith('<b>')) {
        const title = $b.text();
        const content = $li.html().replace(/<b>.*?<\/b>[:.\s]*/i, '');
        $grid.append(`\n<div class="card"><b>${title}</b><p>${content}</p></div>`);
      } else {
        $grid.append(`\n<div class="card"><p>${text}</p></div>`);
      }
    });
    $ul.replaceWith($grid);
  });

  return $.html();
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
 * @param {string} chapterLabel  - Internationalized label for "Chapter" (optional)
 */
function prepareChapter(html, index, title, filesArray, globalCSS = '', bookTitle = '', skipInsights = false, langCode = 'ru', chapterLabel = null) {
  let content = html;

  const hasOwnStyles = /<style[\s\S]*?<\/style>/i.test(content);
  const effectiveChapterLabel = chapterLabel || (langCode === 'en' ? 'Chapter' : 'Глава');

  // Inter-chapter navigation script.
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

  // Universal enrichment passes with Cheerio (includes sanitization)
  bodyContent = processWithCheerio(bodyContent, skipInsights);

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
      const $ = cheerio.load(bodyContent, null, false);
      const $h1 = $('h1').first();
      let h1Text = title;
      if ($h1.length) {
        h1Text = $h1.html();
        $h1.remove();
      }
      const $lead = $('p.lead, div.lead').first();
      let leadText = '';
      if ($lead.length) {
        leadText = $lead.html();
        $lead.remove();
      }
      
      let clean = $.html();

      const kicker = bookTitle
        ? `${bookTitle} \u2022 ${effectiveChapterLabel} ${index + 1}`
        : `${effectiveChapterLabel} ${index + 1}`;
      bodyContent = `
<main class="wrap">
  <section class="hero">
    <div class="kicker">${kicker}</div>
    <h1>${h1Text}</h1>
    <p class="lead">${leadText}</p>
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

  return finalHtml;
}

module.exports = { prepareChapter };
