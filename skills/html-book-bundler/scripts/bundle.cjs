const fs = require('fs');
const path = require('path');
const { prepareChapter } = require('./chapter_processor.cjs');

const args = process.argv.slice(2);
const inputDir = path.resolve(args[args.indexOf('--input') + 1]);
const outputFile = path.resolve(args[args.indexOf('--output') + 1]);
const templateFile = path.resolve(
  args.includes('--template')
    ? args[args.indexOf('--template') + 1]
    : path.join(__dirname, '../templates/default.html')
);
const bookId = path.basename(outputFile, '.html');
// --title "Book Title" overrides the kicker; falls back to output filename
const bookTitle = args.includes('--title')
  ? args[args.indexOf('--title') + 1]
  : bookId.replace(/[-_]/g, ' ');

// Prefer local theme.css from the chapters directory
const localTheme = path.join(inputDir, 'theme.css');
const defaultTheme = path.join(__dirname, '../assets/theme.css');
const themePath = fs.existsSync(localTheme) ? localTheme : defaultTheme;
console.log(`Using theme: ${themePath}`);
const globalCSS = fs.readFileSync(themePath, 'utf8');

function bundleAssets(htmlContent, baseDir) {
  return htmlContent.replace(/(src|href)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    const abs = path.resolve(baseDir, src);
    if (fs.existsSync(abs)) {
      const ext = path.extname(abs).slice(1);
      const mimeMap = {
        png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg',
        svg: 'image/svg+xml', webp: 'image/webp',
      };
      const data = fs.readFileSync(abs).toString('base64');
      return `${attr}="data:${mimeMap[ext] || 'application/octet-stream'};base64,${data}"`;
    }
    return match;
  });
}

const files = fs
  .readdirSync(inputDir)
  .filter(f => f.endsWith('.html'))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

const globalTitles = [];
const globalSearch = [];
const b64Chapters = [];

files.forEach((file, idx) => {
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  content = bundleAssets(content, inputDir);

  const title = content.match(/<title>(.*?)<\/title>/i)?.[1] || file;
  globalTitles.push(title);
  // Trim search index to 800 chars per chapter — enough for keyword search, avoids megabytes
  const plainText = content.replace(/<[^>]*>?/gm, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  globalSearch.push(plainText.slice(0, 800));

  // prepareChapter handles style preservation, .wrap injection, nav script, and base64
  b64Chapters.push(prepareChapter(content, idx, title, files.length, globalCSS, bookTitle));
});

const template = fs.readFileSync(templateFile, 'utf8')
  .replace('{{BOOK_ID}}', bookId)
  .replaceAll('{{BOOK_TITLE}}', bookTitle)
  .replace('{{GLOBAL_TITLES}}', JSON.stringify(globalTitles))
  .replace('{{GLOBAL_SEARCH_INDEX}}', JSON.stringify(globalSearch))
  .replace('{{LOCAL_B64_CHAPTERS}}', JSON.stringify(b64Chapters));

fs.writeFileSync(outputFile, template);
console.log(`Book assembled: ${outputFile}`);
