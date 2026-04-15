#!/usr/bin/env node
'use strict';
const fs   = require('fs');
const path = require('path');
const { prepareChapter } = require('./chapter_processor.cjs');

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------
const args = process.argv.slice(2);

if (args.includes('--help') || args.length === 0) {
  console.log(`
HTML Book Bundler v5.0
Bundles chapter HTML files into a single offline-first reading app.

Usage:
  node bundle.cjs --input <dir> --output <file.html> [options]

Required:
  --input  <dir>      Directory containing chapter HTML files (chapterN.html)
  --output <file>     Output HTML file path

Options:
  --title  <string>   Book title shown in sidebar and browser tab
                      (default: output filename with hyphens replaced by spaces)
  --lang   <code>     UI language: ru | en  (default: ru)
  --dev               Inject live-reload script (for use with dev_server.cjs)
  --optimize          Run optimize_assets.py on input dir before bundling
  --skip-insights     Disable auto-generated pullquotes (use when you insert <blockquote class="insight"> manually)
  --help              Show this help

Examples:
  node bundle.cjs --input ./chapters --output book.html --title "My Book"
  node bundle.cjs --input ./chapters --output book.html --lang en
  node bundle.cjs --input ./chapters --output preview.html --dev
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

if (!inputDir || !outputFile) {
  console.error('Error: --input and --output are required. Run with --help for usage.');
  process.exit(1);
}

const inputDirAbs  = path.resolve(inputDir);
const outputFileAbs = path.resolve(outputFile);

if (!fs.existsSync(inputDirAbs)) {
  console.error(`Error: input directory not found: ${inputDirAbs}`);
  process.exit(1);
}

const bookId    = path.basename(outputFileAbs, '.html');
const bookTitle = getArg('--title', bookId.replace(/[-_]/g, ' '));
const langCode  = getArg('--lang', 'ru');
const devMode      = args.includes('--dev');
const optimize     = args.includes('--optimize');
const skipInsights = args.includes('--skip-insights');

const templateFile = path.resolve(
  args.includes('--template')
    ? getArg('--template')
    : path.join(__dirname, '../templates/default.html')
);

// ---------------------------------------------------------------------------
// Load language strings
// ---------------------------------------------------------------------------
const langFile = path.join(__dirname, `../lang/${langCode}.json`);
const LANG = fs.existsSync(langFile)
  ? JSON.parse(fs.readFileSync(langFile, 'utf8'))
  : JSON.parse(fs.readFileSync(path.join(__dirname, '../lang/ru.json'), 'utf8'));

// ---------------------------------------------------------------------------
// Optionally optimize images
// ---------------------------------------------------------------------------
if (optimize) {
  const { spawnSync } = require('child_process');
  const optimizer = path.join(__dirname, 'optimize_assets.py');
  if (fs.existsSync(optimizer)) {
    console.log('Optimizing assets...');
    spawnSync('python', [optimizer, '--dir', inputDirAbs], { stdio: 'inherit' });
  }
}

// ---------------------------------------------------------------------------
// Theme / CSS loading
// ---------------------------------------------------------------------------
const localTheme   = path.join(inputDirAbs, 'theme.css');
const defaultTheme = path.join(__dirname, '../assets/theme.css');
const themePath    = fs.existsSync(localTheme) ? localTheme : defaultTheme;
console.log(`Using theme: ${themePath}`);
const globalCSS = fs.readFileSync(themePath, 'utf8');

// ---------------------------------------------------------------------------
// Asset inlining (images referenced in chapter HTML)
// ---------------------------------------------------------------------------
function bundleAssets(htmlContent, baseDir) {
  return htmlContent.replace(/(src|href)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    const abs = path.resolve(baseDir, src);
    if (fs.existsSync(abs)) {
      const ext = path.extname(abs).slice(1).toLowerCase();
      const mimeMap = {
        png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg',
        gif: 'image/gif', svg: 'image/svg+xml', webp: 'image/webp',
        woff: 'font/woff', woff2: 'font/woff2',
      };
      const mime = mimeMap[ext] || 'application/octet-stream';
      const data = fs.readFileSync(abs).toString('base64');
      return `${attr}="data:${mime};base64,${data}"`;
    }
    return match;
  });
}

// ---------------------------------------------------------------------------
// Search index builder (inverted index, language-agnostic)
// ---------------------------------------------------------------------------
const STOP_WORDS = new Set(
  // Russian
  'и в на не с а но из к по за то как что так же это да уж вот ' +
  'он она оно они мы вы я ни ли бы до при про над под без через для ' +
  // English
  'the a an of to in is it on at be by this that with from are was were ' +
  'have has had will would can could should may might do does did not '
  .split(/\s+/).filter(Boolean)
);

function tokenize(text) {
  return text
    .replace(/<[^>]+>/g, ' ')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w));
}

function buildSearchIndex(chapterTexts) {
  const idx = {};
  chapterTexts.forEach((text, ci) => {
    const tokens = new Set(tokenize(text));
    tokens.forEach(tok => {
      if (!idx[tok]) idx[tok] = [];
      idx[tok].push(ci);
    });
  });
  return idx;
}

// ---------------------------------------------------------------------------
// Process chapters
// ---------------------------------------------------------------------------
const files = fs
  .readdirSync(inputDirAbs)
  .filter(f => f.endsWith('.html'))
  .sort((a, b) => {
    if (a === 'glossary.html') return 1;
    if (b === 'glossary.html') return -1;
    return a.localeCompare(b, undefined, { numeric: true });
  });

if (files.length === 0) {
  console.error(`Error: no .html files found in ${inputDirAbs}`);
  process.exit(1);
}

const globalTitles  = [];
const chapterTexts  = []; // for search index
const chapters      = []; // HTML strings for srcdoc
let totalImageBytes = 0;

files.forEach((file, idx) => {
  let content = fs.readFileSync(path.join(inputDirAbs, file), 'utf8');

  // Count image data before inlining (for warning)
  const imgMatches = content.match(/src=["'][^"']+["']/gi) || [];
  imgMatches.forEach(m => {
    const src = m.slice(5, -1).replace(/^["']|["']$/g, '');
    if (!src.startsWith('http') && !src.startsWith('data:')) {
      const abs = path.resolve(inputDirAbs, src);
      if (fs.existsSync(abs)) totalImageBytes += fs.statSync(abs).size;
    }
  });

  content = bundleAssets(content, inputDirAbs);

  // Title extraction: <title> first, then <h1>, then filename
  let title = content.match(/<title>(.*?)<\/title>/i)?.[1] || '';
  if (!title) {
    const h1 = content.match(/<h1[^>]*>(.*?)<\/h1>/i)?.[1];
    title = h1 ? h1.replace(/<[^>]+>/g, '').trim() : file.replace(/\.html$/, '');
  }
  globalTitles.push(title);

  // Plain text for search index (full text, not truncated)
  chapterTexts.push(content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim());

  // Prepare chapter HTML string (srcdoc-ready)
  chapters.push(prepareChapter(content, idx, title, files.length, globalCSS, bookTitle, skipInsights, langCode));
});

// Warn about large image payloads
if (totalImageBytes > 500_000) {
  const mb = (totalImageBytes / 1_048_576).toFixed(1);
  console.warn(`Warning: ${mb}MB of images detected. Run with --optimize to compress, or output file may be large.`);
}

const searchIndex = buildSearchIndex(chapterTexts);

// ---------------------------------------------------------------------------
// Inject dev live-reload script if --dev
// ---------------------------------------------------------------------------
const devScript = devMode
  ? `<script>new EventSource('/events').onmessage=function(){location.reload()}</script>`
  : '';

// ---------------------------------------------------------------------------
// Assemble final HTML from template
// ---------------------------------------------------------------------------
let template = fs.readFileSync(templateFile, 'utf8');

// Replace all placeholders
const replacements = {
  '{{BOOK_ID}}':        bookId,
  '{{BOOK_TITLE}}':     bookTitle,
  '{{LANG_CODE}}':      LANG.code || langCode,
  '{{LANG_JSON}}':      JSON.stringify(LANG),
  '{{GLOBAL_TITLES}}':  JSON.stringify(globalTitles),
  // Escape </script> so it never terminates the outer <script> block prematurely.
  // In JSON, <\/ is parsed as </ by JS (the \/ escape = /) giving correct srcdoc HTML.
  '{{LOCAL_CHAPTERS}}': JSON.stringify(chapters).replace(/<\/script>/gi, '<\\/script>'),
  '{{SEARCH_IDX}}':     JSON.stringify(searchIndex),
  '{{DEV_SCRIPT}}':     devScript,
};

for (const [placeholder, value] of Object.entries(replacements)) {
  // Use split/join for global replace without regex escaping issues
  template = template.split(placeholder).join(value);
}

// Verify all placeholders are resolved
const remaining = template.match(/\{\{[A-Z_]+\}\}/g);
if (remaining) {
  console.warn(`Warning: unresolved template placeholders: ${[...new Set(remaining)].join(', ')}`);
}

fs.mkdirSync(path.dirname(outputFileAbs), { recursive: true });
fs.writeFileSync(outputFileAbs, template);

const sizeMb = (fs.statSync(outputFileAbs).size / 1_048_576).toFixed(2);
console.log(`Book assembled: ${outputFileAbs} (${sizeMb} MB, ${files.length} chapters)`);
