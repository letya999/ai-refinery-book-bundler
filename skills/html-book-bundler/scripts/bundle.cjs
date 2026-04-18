#!/usr/bin/env node
'use strict';
const fs   = require('fs');
const path = require('path');
const crypto = require('crypto');
const { prepareChapter } = require('./chapter_processor.cjs');

// ---------------------------------------------------------------------------
// HTML entity decoder — used for sidebar titles extracted from <title>/<h1>
// ---------------------------------------------------------------------------
function decodeHtmlEntities(str) {
  return String(str)
    .replace(/&amp;/gi,  '&')
    .replace(/&lt;/gi,   '<')
    .replace(/&gt;/gi,   '>')
    .replace(/&quot;/gi, '"')
    .replace(/&apos;/gi, "'")
    .replace(/&nbsp;/gi, ' ')
    .replace(/&mdash;/gi, '—')
    .replace(/&ndash;/gi, '–')
    .replace(/&laquo;/gi, '«')
    .replace(/&raquo;/gi, '»')
    .replace(/&ldquo;/gi, '“')
    .replace(/&rdquo;/gi, '”')
    .replace(/&#(\d+);/gi,      (_, n) => String.fromCharCode(+n))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16)));
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Safely injects JSON into a script tag by escaping </script>
 */
function safeJsonInject(obj) {
  return JSON.stringify(obj).replace(/<\/script>/gi, '<\\/script>');
}

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);
const VERSION = '8.5';

if (args.includes('--version') || args.includes('-v')) {
  console.log(`HTML Book Bundler v${VERSION}`);
  process.exit(0);
}

if (args.includes('--help') || args.length === 0) {
  console.log(`
HTML Book Bundler v${VERSION}
Bundles chapter HTML files into a single offline-first reading app.

Usage:
  node bundle.cjs --input <dir> --output <file.html> [options]

Required:
  --input  <dir>      Directory containing chapter HTML files (chapterN.html)
  --output <file>     Output HTML file path

Options:
  --title    <string> Book title shown in sidebar and browser tab
  --lang     <code>   UI language: ru | en  (default: ru)
  --template <file>   Custom HTML template (default: templates/default.html)
  --dev               Inject live-reload script
  --optimize          Run optimize_assets.py on input dir before bundling
  --skip-insights     Disable auto-generated pullquotes
  --split-limit <n>   Max chapter size in bytes before splitting (default: 2097152 / 2MB)
  --help              Show this help
`);
  process.exit(0);
}

function getArg(flag, fallback = null) {
  const i = args.indexOf(flag);
  if (i === -1) return fallback;
  if (i + 1 >= args.length || args[i + 1].startsWith('--')) {
    console.error(`Error: ${flag} requires a value`);
    process.exit(1);
  }
  return args[i + 1];
}

const inputDir  = getArg('--input');
const outputFile = getArg('--output');
const splitLimit = parseInt(getArg('--split-limit', '2097152'), 10);

if (!inputDir || !outputFile) {
  console.error('Error: --input and --output are required.');
  process.exit(1);
}

const inputDirAbs  = path.resolve(inputDir);
const outputFileAbs = path.resolve(outputFile);

const fallbackTitle = path.basename(outputFileAbs, '.html').replace(/[-_]/g, ' ');
const bookTitle = escHtml(getArg('--title', fallbackTitle));
let langCode    = getArg('--lang', 'ru');

const langDir = path.join(__dirname, '../lang');
const SUPPORTED_LANGS = fs.existsSync(langDir) 
  ? fs.readdirSync(langDir).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''))
  : ['ru', 'en'];

if (!SUPPORTED_LANGS.includes(langCode)) {
  langCode = 'ru';
}

const devMode      = args.includes('--dev');
const optimize     = args.includes('--optimize');
const skipInsights = args.includes('--skip-insights');
const templateFile = path.resolve(getArg('--template', path.join(__dirname, '../templates/default.html')));

const pyCmd = (() => {
  const { spawnSync } = require('child_process');
  const r = spawnSync('python3', ['--version'], { stdio: 'pipe' });
  return r.status === 0 ? 'python3' : 'python';
})();

const langFile = path.join(__dirname, `../lang/${langCode}.json`);
const LANG = fs.existsSync(langFile)
  ? JSON.parse(fs.readFileSync(langFile, 'utf8'))
  : JSON.parse(fs.readFileSync(path.join(__dirname, '../lang/ru.json'), 'utf8'));

// ---------------------------------------------------------------------------
// Optionally optimize images
// ---------------------------------------------------------------------------
if (optimize) {
  const optimizer = path.join(__dirname, 'optimize_assets.py');
  if (fs.existsSync(optimizer)) {
    console.log('Optimizing assets in-place...');
    const { spawnSync } = require('child_process');
    spawnSync(pyCmd, [optimizer, '--dir', inputDirAbs], { stdio: 'inherit' });
  }
}

const localTheme   = path.join(inputDirAbs, 'theme.css');
const defaultTheme = path.join(__dirname, '../assets/theme.css');
const themePath    = fs.existsSync(localTheme) ? localTheme : defaultTheme;
const globalCSS = fs.readFileSync(themePath, 'utf8');

// ---------------------------------------------------------------------------
// Asset inlining
// ---------------------------------------------------------------------------
const ASSETS = {};

function bundleAssets(htmlContent, baseDir) {
  const mimeMap = {
    png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg',
    gif: 'image/gif', svg: 'image/svg+xml', webp: 'image/webp',
    woff: 'font/woff', woff2: 'font/woff2',
  };

  const processAsset = (src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return null;
    if (/\.html?$/i.test(src) || /\.css$/i.test(src)) return null;
    const abs = path.resolve(baseDir, src);
    if (fs.existsSync(abs)) {
      const ext = path.extname(abs).slice(1).toLowerCase();
      const mime = mimeMap[ext] || 'application/octet-stream';
      const fileHash = crypto.createHash('md5').update(fs.readFileSync(abs)).digest('hex').slice(0, 10);
      const assetKey = `asset_${fileHash}_${path.basename(src)}`;
      if (!ASSETS[assetKey]) {
        ASSETS[assetKey] = `data:${mime};base64,${fs.readFileSync(abs).toString('base64')}`;
      }
      return assetKey;
    }
    return null;
  };

  let content = htmlContent.replace(/src=["']([^"']+)["']/gi, (match, src) => {
    const assetKey = processAsset(src);
    return assetKey ? `src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" data-src="${assetKey}"` : match;
  });

  content = content.replace(/srcset=["']([^"']+)["']/gi, (match, srcset) => {
    srcset.split(',').forEach(entry => {
      const src = entry.trim().split(/\s+/)[0];
      if (src) processAsset(src);
    });
    return `data-srcset="${srcset}"`;
  });

  content = content.replace(/<a\s+([^>]*?)href=["']([^"']+)["']/gi, (match, before, src) => {
    const assetKey = processAsset(src);
    return assetKey ? `<a ${before}href="#" data-href="${assetKey}"` : match;
  });

  content = content.replace(/url\(["']?([^"'\)]+)["']?\)/gi, (match, src) => {
    const assetKey = processAsset(src);
    return assetKey ? `url("${ASSETS[assetKey]}")` : match;
  });

  return content;
}

function inlineStylesheets(htmlContent, baseDir) {
  return htmlContent.replace(/<link([^>]*)\/?>(\s*<\/link>)?/gi, (match, attrs) => {
    const relM  = /rel=["']([^"']+)["']/i.exec(attrs);
    const hrefM = /href=["']([^"']+)["']/i.exec(attrs);
    if (!relM || !relM[1].toLowerCase().includes('stylesheet') || !hrefM) return match;
    const abs = path.resolve(baseDir, hrefM[1]);
    if (!fs.existsSync(abs)) return match;
    return `<style>\n${fs.readFileSync(abs, 'utf8')}\n</style>`;
  });
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------
function tokenize(text) {
  const STOP_WORDS = new Set((LANG.stop_words || []).map(w => w.toLowerCase()));
  return text.replace(/<[^>]+>/g, ' ').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, ' ').split(/\s+/).filter(w => w.length > 2 && !STOP_WORDS.has(w));
}

function buildSearchIndex(chapterTexts) {
  const idx = {};
  chapterTexts.forEach((text, ci) => {
    const tokens = tokenize(text);
    const tf = {};
    tokens.forEach(tok => tf[tok] = (tf[tok] || 0) + 1);
    Object.keys(tf).forEach(tok => {
      if (!idx[tok]) idx[tok] = [];
      idx[tok].push([ci, tf[tok]]);
    });
  });
  for (const tok in idx) {
    idx[tok].sort((a, b) => b[1] - a[1]);
    idx[tok] = idx[tok].map(entry => entry[0]);
  }
  return idx;
}

// ---------------------------------------------------------------------------
// Split large chapters
// ---------------------------------------------------------------------------
function splitChapter(html, limit) {
  if (Buffer.byteLength(html, 'utf8') <= limit) return [html];
  
  console.log(`  Splitting large chapter (${(Buffer.byteLength(html, 'utf8') / 1024 / 1024).toFixed(1)} MB)...`);
  const parts = [];
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  if (!bodyMatch) return [html];
  
  const head = html.split(/<body/i)[0] + '<body' + (html.match(/<body([^>]*)>/i)?.[1] || '') + '>';
  const foot = '</body></html>';
  const body = bodyMatch[1];
  
  // Naive split by paragraph/section/div tags to keep structure
  const chunks = body.split(/(?=<p|<div|<section|<blockquote|<table|<h[1-6]|<details)/i);
  let currentPart = '';
  
  for (const chunk of chunks) {
    if (Buffer.byteLength(currentPart + chunk, 'utf8') > limit && currentPart) {
      parts.push(head + currentPart + foot);
      currentPart = chunk;
    } else {
      currentPart += chunk;
    }
  }
  if (currentPart) parts.push(head + currentPart + foot);
  return parts;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const files = fs.readdirSync(inputDirAbs).filter(f => f.endsWith('.html')).sort((a, b) => {
  if (a.toLowerCase() === 'glossary.html') return 1;
  if (b.toLowerCase() === 'glossary.html') return -1;
  return a.localeCompare(b, undefined, { numeric: true });
});

if (files.length === 0) { console.error('No chapters found.'); process.exit(1); }

const globalTitles = [];
const globalFiles = [];
const chapterTexts = [];
const chapters = [];

files.forEach((file, idx) => {
  let content = fs.readFileSync(path.join(inputDirAbs, file), 'utf8');
  let title = decodeHtmlEntities(content.match(/<title[^>]*>(.*?)<\/title>/i)?.[1] || '');
  if (!title) {
    const h1 = content.match(/<h1[^>]*>(.*?)<\/h1>/i)?.[1];
    title = h1 ? decodeHtmlEntities(h1.replace(/<[^>]+>/g, '').trim()) : file.replace(/\.html$/, '');
  }

  content = bundleAssets(content, inputDirAbs);
  content = inlineStylesheets(content, inputDirAbs);
  
  const rendered = prepareChapter(content, idx, title, files, globalCSS, bookTitle, skipInsights, langCode, LANG.chapter, LANG.dir || 'ltr');
  const splitParts = splitChapter(rendered, splitLimit);
  
  splitParts.forEach((part, pIdx) => {
    const partTitle = splitParts.length > 1 ? `${title} (${pIdx + 1}/${splitParts.length})` : title;
    globalTitles.push(partTitle);
    globalFiles.push(file.toLowerCase());
    chapters.push(part);
    // Use raw text for search
    chapterTexts.push(part.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim());
  });
});

const searchIndex = buildSearchIndex(chapterTexts);
const devScript = devMode ? `<script>new EventSource('/events').onmessage=function(){location.reload()}</script>` : '';

const bookId = 'book_' + crypto.createHash('md5').update(bookTitle + '_' + chapters.length).digest('hex').slice(0, 8);

let template = fs.readFileSync(templateFile, 'utf8');
const replacements = {
  '{{BOOK_ID}}':        bookId,
  '{{BOOK_TITLE}}':     bookTitle,
  '{{LANG_CODE}}':      LANG.code || langCode,
  '{{LANG_DIR}}':       LANG.dir || 'ltr',
  '{{LANG_JSON}}':      safeJsonInject(LANG),
  '{{GLOBAL_TITLES}}':  safeJsonInject(globalTitles),
  '{{GLOBAL_FILES}}':   safeJsonInject(globalFiles),
  '{{LOCAL_CHAPTERS}}': safeJsonInject(chapters),
  '{{ASSETS}}':         safeJsonInject(ASSETS),
  '{{SEARCH_IDX}}':     safeJsonInject(searchIndex),
  '{{DEV_SCRIPT}}':     devScript,
};

for (const [p, v] of Object.entries(replacements)) template = template.split(p).join(v);
template = template.replace('</head>', `  <meta name="generator" content="HTML Book Bundler v${VERSION}">\n</head>`);

fs.mkdirSync(path.dirname(outputFileAbs), { recursive: true });
fs.writeFileSync(outputFileAbs, template);
console.log(`Book assembled: ${outputFileAbs} (${(fs.statSync(outputFileAbs).size / 1024 / 1024).toFixed(2)} MB, ${chapters.length} chunks)`);
