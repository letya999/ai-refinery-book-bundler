const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const inputDirRaw = args[args.indexOf('--input') + 1];
const outputFile = args[args.indexOf('--output') + 1];
const templateFile = args.includes('--template') ? args[args.indexOf('--template') + 1] : path.join(__dirname, '../templates/default.html');
const maxVolSizeMB = args.includes('--max-size') ? parseFloat(args[args.indexOf('--max-size') + 1]) : 15;

if (!inputDirRaw || !outputFile) {
  console.log('Использование: node bundle.cjs --input <папка> --output <файл.html> [--max-size 15]');
  process.exit(1);
}

const inputDir = path.resolve(inputDirRaw);
const MAX_VOL_BYTES = maxVolSizeMB * 1024 * 1024;
const assetCache = new Map();

function getAssetData(assetPath, baseDir) {
  const absolutePath = path.resolve(baseDir, assetPath);
  if (!absolutePath.startsWith(inputDir) && !absolutePath.startsWith(path.dirname(templateFile))) return null;
  if (assetCache.has(absolutePath)) return assetCache.get(absolutePath);
  if (fs.existsSync(absolutePath)) {
    const ext = path.extname(absolutePath).toLowerCase().slice(1);
    const mimeMap = { 'webp': 'image/webp', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml', 'gif': 'image/gif', 'woff2': 'font/woff2', 'css': 'text/css', 'js': 'application/javascript' };
    const mime = mimeMap[ext] || 'application/octet-stream';
    const data = fs.readFileSync(absolutePath).toString('base64');
    const result = `data:${mime};base64,${data}`;
    assetCache.set(absolutePath, result);
    return result;
  }
  return null;
}

function bundleAssets(htmlContent, baseDir, depth = 0) {
  if (depth > 12) return htmlContent;
  htmlContent = htmlContent.replace(/(src|data-src|poster|href)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#') || src.startsWith('mailto:') || src.startsWith('tel:')) return match;
    const data = getAssetData(src, baseDir);
    return data ? `${attr}="${data}"` : match;
  });
  htmlContent = htmlContent.replace(/(@import\s+(?:url\()?["']([^"']+)["']\)?|url\(["']?([^"')]+)["']?\))/gi, (match, full, importSrc, urlSrc) => {
    const src = importSrc || urlSrc;
    if (!src || src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    if (full.startsWith('@import')) {
      const assetPath = path.resolve(baseDir, src);
      if (fs.existsSync(assetPath)) return bundleAssets(fs.readFileSync(assetPath, 'utf8'), path.dirname(assetPath), depth + 1);
    } else {
      const data = getAssetData(src, baseDir);
      return data ? `url("${data}")` : match;
    }
    return match;
  });
  htmlContent = htmlContent.replace(/<link\s+([^>]*?)href=["']([^"']+)["']([^>]*?)>|<script\s+([^>]*?)src=["']([^"']+)["']([^>]*?)><\/script>/gi, (match, lp1, lsrc, lp3, sp1, ssrc, sp3) => {
    const src = lsrc || ssrc;
    if (!src || src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (!fs.existsSync(assetPath)) return match;
    if (lsrc && (lp1 + lp3).includes('stylesheet')) return `<style>${bundleAssets(fs.readFileSync(assetPath, 'utf8'), path.dirname(assetPath), depth + 1)}</style>`;
    if (ssrc) return `<script>${fs.readFileSync(assetPath, 'utf8')}</script>`;
    return match;
  });
  return htmlContent;
}

const defaultChapterCSS = `
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Variable", Roboto, Helvetica, Arial, sans-serif; font-size: clamp(16px, 2.5vw + 12px, 22px); line-height: 1.65; color: #202124; max-width: 800px; margin: 0 auto; padding: clamp(16px, 5vw, 48px); background: transparent; word-wrap: break-word; }
  img, svg, video { max-width: 100%; height: auto; display: block; margin: 2em auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .table-wrapper { overflow-x: auto; width: 100%; margin: 2em 0; -webkit-overflow-scrolling: touch; border-radius: 8px; border: 1px solid #dadce0; }
  table { width: 100%; border-collapse: collapse; min-width: 500px; }
  th, td { border-bottom: 1px solid #dadce0; padding: 12px 16px; text-align: left; }
  th { background: #f8f9fa; font-weight: 600; }
  h1, h2, h3, h4 { line-height: 1.25; color: #111; margin-top: 1.8em; margin-bottom: 0.6em; }
  a { color: #1a73e8; text-decoration: none; border-bottom: 1px dashed rgba(26,115,232,0.4); }
  .book-nav-bottom { margin-top: 60px; padding: 40px 10px; text-align: center; border-top: 1px solid #eee; }
  .book-nav-bottom button { padding: 18px 36px; font-size: 18px; border-radius: 100px; background: #1a73e8; color: white; border: none; cursor: pointer; font-weight: 600; width: 100%; max-width: 340px; box-shadow: 0 6px 16px rgba(26,115,232,0.25); transition: transform 0.2s, background 0.2s; }
  .book-nav-bottom button:active { transform: scale(0.96); background: #1557b0; }
  @media (prefers-color-scheme: dark) {
    body { color: #e8eaed; }
    h1, h2, h3, h4 { color: #fff; }
    th, td { border-color: #3c4043; }
    th { background: #202124; }
    a { color: #8ab4f8; border-color: rgba(138,180,248,0.4); }
    .table-wrapper { border-color: #3c4043; }
    .book-nav-bottom { border-top-color: #333; }
    img { opacity: 0.9; } /* Reduce glare in dark mode */
  }
</style>
`;

const files = fs.readdirSync(inputDir).filter(f => f.endsWith('.html')).sort((a,b) => a.localeCompare(b, undefined, {numeric: true}));
const globalTitles = [], globalSearch = [], rawChapters = [], manifest = {};

files.forEach((file, globalIdx) => {
  manifest[file.toLowerCase()] = globalIdx;
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  if (!content.includes('charset=')) content = content.replace('<head>', '<head><meta charset="utf-8">');
  if (!content.includes('<style')) content = content.replace('</head>', defaultChapterCSS + '</head>');
  
  content = content.replace(/<table/g, '<div class="table-wrapper"><table').replace(/<\/table>/g, '</table></div>');
  content = bundleAssets(content, inputDir);
  
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  globalTitles.push(titleMatch ? titleMatch[1] : file);

  const nextBtn = `<div class="book-nav-bottom"><button onclick="window.parent.postMessage({action:'bookNext'},'*')">Следующая глава →</button></div>`;
  const bridge = `<script>(function(){const m=${JSON.stringify(manifest)};document.addEventListener('click',e=>{const a=e.target.closest('a');if(a&&a.href){const h=a.getAttribute('href');if(!h||h.startsWith('http')||h.startsWith('mailto:')||h.startsWith('data:'))return;if(!h.includes('.html')&&!h.startsWith('#'))return;e.preventDefault();const p=h.split('#'),f=p[0].split('/').pop().toLowerCase(),anc=p[1]||null;if(m[f]!==undefined&&window.parent){window.parent.postMessage({action:'bookGo',chapterIdx:m[f],anchorId:anc},'*');}else if(anc){const el=document.getElementById(anc);if(el)el.scrollIntoView({behavior:'smooth'});}}});})();</script>`;
  content = content.replace('</body>', nextBtn + bridge + '</body>');

  const cleanText = content.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<[^>]*>?/gm, ' ')
    .toLowerCase().replace(/[^a-zа-я0-9\s]/g, ' ').split(/\s+/).filter(w => w.length > 2);
  globalSearch.push([...new Set(cleanText)].join(' '));
  
  rawChapters.push({ globalIdx, b64: Buffer.from(content, 'utf8').toString('base64') });
});

// Нарезка на Тома (Volumes)
const vols = [];
let curVol = { id: 1, chapters: [], size: 0 };
vols.push(curVol);

rawChapters.forEach(ch => {
  const size = Buffer.byteLength(ch.b64, 'utf8');
  if (curVol.size + size > MAX_VOL_BYTES && curVol.chapters.length > 0) {
    curVol = { id: curVol.id + 1, chapters: [], size: 0 };
    vols.push(curVol);
  }
  curVol.chapters.push(ch);
  curVol.size += size;
});

const baseOutputName = path.basename(outputFile, '.html');
const outputDir = path.dirname(outputFile);
const VOL_MAP = [];
const VOL_FILES = {};

vols.forEach(v => {
   const filename = vols.length === 1 ? `${baseOutputName}.html` : `${baseOutputName}_vol${v.id}.html`;
   VOL_FILES[v.id] = filename;
   v.chapters.forEach(ch => VOL_MAP[ch.globalIdx] = v.id);
});

const templateContent = fs.readFileSync(templateFile, 'utf8');

vols.forEach(v => {
   const localB64 = v.chapters.map(c => c.b64);
   const localStartIdx = v.chapters[0].globalIdx;
   
   let html = templateContent
      .replace('{{BOOK_ID}}', baseOutputName)
      .replace('{{GLOBAL_TITLES}}', JSON.stringify(globalTitles))
      .replace('{{GLOBAL_SEARCH_INDEX}}', JSON.stringify(globalSearch))
      .replace('{{VOL_MAP}}', JSON.stringify(VOL_MAP))
      .replace('{{VOL_FILES}}', JSON.stringify(VOL_FILES))
      .replace('{{CURRENT_VOL}}', v.id)
      .replace('{{LOCAL_START_IDX}}', localStartIdx)
      .replace('{{LOCAL_B64_CHAPTERS}}', JSON.stringify(localB64));
      
   fs.writeFileSync(path.join(outputDir, VOL_FILES[v.id]), html);
   console.log(`✅ Создан том ${v.id}: ${VOL_FILES[v.id]} (${v.chapters.length} глав)`);
});
