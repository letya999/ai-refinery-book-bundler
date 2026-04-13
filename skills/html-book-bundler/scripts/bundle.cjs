const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const inputDir = path.resolve(args[args.indexOf('--input') + 1]);
const outputFile = path.resolve(args[args.indexOf('--output') + 1]);
const templateFile = path.resolve(args.includes('--template') ? args[args.indexOf('--template') + 1] : path.join(__dirname, '../templates/default.html'));

const localTheme = path.join(inputDir, 'theme.css');
const defaultTheme = path.join(__dirname, '../assets/theme.css');
const themePath = fs.existsSync(localTheme) ? localTheme : defaultTheme;

console.log(`🎨 Используется тема: ${themePath}`);
const globalCSS = fs.readFileSync(themePath, 'utf8');

function bundleAssets(htmlContent, baseDir) {
  return htmlContent.replace(/(src|href)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    const abs = path.resolve(baseDir, src);
    if (fs.existsSync(abs)) {
      const ext = path.extname(abs).slice(1);
      const mimeMap = { 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml', 'webp': 'image/webp' };
      const data = fs.readFileSync(abs).toString('base64');
      return `${attr}="data:${mimeMap[ext] || 'application/octet-stream'};base64,${data}"`;
    }
    return match;
  });
}

const files = fs.readdirSync(inputDir).filter(f => f.endsWith('.html')).sort((a,b) => a.localeCompare(b, undefined, {numeric: true}));
const globalTitles = [], globalSearch = [], b64Chapters = [];

files.forEach((file, idx) => {
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  content = content.replace(/<style[\s\S]*?<\/style>/gi, '');
  content = content.replace('</head>', `<style>${globalCSS}</style></head>`);
  
  if (!content.includes('class="wrap"')) {
    content = content.replace('<body>', '<body><main class="wrap">').replace('</body>', '</main></body>');
  }

  content = bundleAssets(content, inputDir);
  globalTitles.push(content.match(/<title>(.*?)<\/title>/i)?.[1] || file);
  globalSearch.push(content.replace(/<[^>]*>?/gm, ' ').toLowerCase());
  b64Chapters.push(Buffer.from(content, 'utf8').toString('base64'));
});

const template = fs.readFileSync(templateFile, 'utf8')
  .replace('{{BOOK_ID}}', path.basename(outputFile, '.html'))
  .replace('{{GLOBAL_TITLES}}', JSON.stringify(globalTitles))
  .replace('{{GLOBAL_SEARCH_INDEX}}', JSON.stringify(globalSearch))
  .replace('{{VOL_MAP}}', JSON.stringify(new Array(files.length).fill(1)))
  .replace('{{VOL_FILES}}', JSON.stringify({1: path.basename(outputFile)}))
  .replace('{{CURRENT_VOL}}', 1)
  .replace('{{LOCAL_START_IDX}}', 0)
  .replace('{{LOCAL_B64_CHAPTERS}}', JSON.stringify(b64Chapters)); // ПЕРЕДАЕМ ТОЛЬКО МАССИВ СТРОК

fs.writeFileSync(outputFile, template);
console.log(`✅ Книга собрана: ${outputFile}`);
