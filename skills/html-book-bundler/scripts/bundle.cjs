const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const inputDir = args[args.indexOf('--input') + 1];
const outputFile = args[args.indexOf('--output') + 1];
const templateFile = args.includes('--template') ? args[args.indexOf('--template') + 1] : path.join(__dirname, '../templates/default.html');

if (!inputDir || !outputFile) {
  console.log('Использование: node bundle.cjs --input <папка> --output <файл.html> [--template <файл.html>]');
  process.exit(1);
}

const assetCache = new Map();

function getAssetData(assetPath) {
  const absolutePath = path.resolve(assetPath);
  if (assetCache.has(absolutePath)) return assetCache.get(absolutePath);
  if (fs.existsSync(absolutePath)) {
    const ext = path.extname(absolutePath).toLowerCase().slice(1);
    const mime = ext === 'svg' ? 'image/svg+xml' : (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext) ? `image/${ext}` : 'application/octet-stream');
    const data = fs.readFileSync(absolutePath).toString('base64');
    const result = `data:${mime};base64,${data}`;
    assetCache.set(absolutePath, result);
    return result;
  }
  return null;
}

function bundleAssets(htmlContent, baseDir) {
  htmlContent = htmlContent.replace(/(src|data-src)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#') || src.startsWith('mailto:') || src.startsWith('tel:')) return match;
    const data = getAssetData(path.resolve(baseDir, src));
    return data ? `${attr}="${data}"` : match;
  });

  htmlContent = htmlContent.replace(/srcset=["']([^"']+)["']/gi, (match, srcset) => {
    const parts = srcset.split(',').map(part => {
      const trimmed = part.trim();
      const [url, descriptor] = trimmed.split(/\s+/);
      if (url && !url.startsWith('http') && !url.startsWith('data:')) {
        const data = getAssetData(path.resolve(baseDir, url));
        return data ? `${data}${descriptor ? ' ' + descriptor : ''}` : trimmed;
      }
      return trimmed;
    });
    return `srcset="${parts.join(', ')}"`;
  });

  htmlContent = htmlContent.replace(/<link[^>]+rel=["']stylesheet["'][^>]+href=["']([^"']+)["'][^>]*>/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath)) {
      let css = fs.readFileSync(assetPath, 'utf8');
      css = bundleAssets(css, path.dirname(assetPath)); 
      return `<style>${css}</style>`;
    }
    return match;
  });

  htmlContent = htmlContent.replace(/@import\s+["']([^"']+)["']/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath)) {
      let css = fs.readFileSync(assetPath, 'utf8');
      css = bundleAssets(css, path.dirname(assetPath)); 
      return css;
    }
    return match;
  });

  htmlContent = htmlContent.replace(/<script[^>]+src=["']([^"']+)["'][^>]*><\/script>/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath)) {
      const js = fs.readFileSync(assetPath, 'utf8');
      return `<script>${js}</script>`;
    }
    return match;
  });

  htmlContent = htmlContent.replace(/url\(["']?([^"')]+)["']?\)/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    const data = getAssetData(path.resolve(baseDir, src));
    return data ? `url("${data}")` : match;
  });

  return htmlContent;
}

const files = fs.readdirSync(inputDir)
  .filter(f => f.endsWith('.html'))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));

const titles = [];
const base64Chapters = [];
const searchIndex = [];
const manifest = {};

files.forEach((file, index) => {
  manifest[file.toLowerCase()] = index;
});

files.forEach((file, index) => {
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  content = bundleAssets(content, inputDir);
  
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  titles.push(titleMatch ? titleMatch[1] : file);
  
  const bridgeScript = `
<script>
(function() {
  const manifest = ${JSON.stringify(manifest)};
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (a && a.getAttribute('href')) {
      const href = a.getAttribute('href');
      if (href.startsWith('http') || href.startsWith('mailto:') || href.startsWith('data:') || href.startsWith('tel:')) return;
      e.preventDefault();
      let targetIdx = -1;
      let anchor = null;
      const parts = href.split('#');
      const pathPart = parts[0].toLowerCase();
      anchor = parts[1] || null;
      const fileName = pathPart.split('/').pop();
      if (manifest[fileName] !== undefined) {
        targetIdx = manifest[fileName];
      } else if (pathPart.includes('chapter')) {
        const m = pathPart.match(/chapter(\\d+)/);
        if (m) targetIdx = parseInt(m[1]) - 1;
      }
      if (targetIdx !== -1 && window.parent) {
        window.parent.postMessage({ action: 'bookGo', chapterIdx: targetIdx, anchorId: anchor }, '*');
      } else if (anchor) {
        const el = document.getElementById(anchor);
        if (el) el.scrollIntoView({behavior:'smooth'});
      }
    }
  });
})();
</script>
  `;
  
  content = content.includes('</body>') ? content.replace('</body>', bridgeScript + '</body>') : content + bridgeScript;
  
  const cleanForSearch = content
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]*>?/gm, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
    
  searchIndex.push(cleanForSearch);
  base64Chapters.push(Buffer.from(content).toString('base64'));
});

let templateContent = fs.readFileSync(templateFile, 'utf8')
  .replace('{{B64_CHAPTERS}}', JSON.stringify(base64Chapters))
  .replace('{{TITLES}}', JSON.stringify(titles))
  .replace('{{SEARCH_INDEX}}', JSON.stringify(searchIndex));

fs.writeFileSync(outputFile, templateContent);
console.log(`Книга собрана: ${outputFile} (${files.length} глав). Уникальных ассетов: ${assetCache.size}.`);
