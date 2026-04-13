const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const args = process.argv.slice(2);
const inputDirRaw = args[args.indexOf('--input') + 1];
const outputFile = args[args.indexOf('--output') + 1];
const templateFile = args.includes('--template') ? args[args.indexOf('--template') + 1] : path.join(__dirname, '../templates/default.html');

if (!inputDirRaw || !outputFile) {
  console.log('Использование: node bundle.cjs --input <папка> --output <файл.html>');
  process.exit(1);
}

const inputDir = path.resolve(inputDirRaw);
const assetCache = new Map();
const visitedStyles = new Set();

// Безопасное чтение ассетов с защитой от Path Traversal
function getAssetData(assetPath, baseDir) {
  const absolutePath = path.resolve(baseDir, assetPath);
  
  // ЗАЩИТА: Путь не должен выходить за пределы входной директории
  if (!absolutePath.startsWith(inputDir) && !absolutePath.startsWith(path.dirname(templateFile))) {
    console.warn(`[Security Warning] Blocked access to file outside project: ${absolutePath}`);
    return null;
  }

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

function bundleAssets(htmlContent, baseDir, depth = 0) {
  if (depth > 10) return htmlContent;

  // 1. src/data-src
  htmlContent = htmlContent.replace(/(src|data-src)=["']([^"']+)["']/gi, (match, attr, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#') || src.startsWith('mailto:') || src.startsWith('tel:')) return match;
    const data = getAssetData(src, baseDir);
    return data ? `${attr}="${data}"` : match;
  });

  // 2. srcset
  htmlContent = htmlContent.replace(/srcset=["']([^"']+)["']/gi, (match, srcset) => {
    const parts = srcset.split(',').map(part => {
      const trimmed = part.trim();
      const [url, descriptor] = trimmed.split(/\s+/);
      if (url && !url.startsWith('http') && !url.startsWith('data:')) {
        const data = getAssetData(url, baseDir);
        return data ? `${data}${descriptor ? ' ' + descriptor : ''}` : trimmed;
      }
      return trimmed;
    });
    return `srcset="${parts.join(', ')}"`;
  });

  // 3. Стили <link>
  htmlContent = htmlContent.replace(/<link\s+([^>]*?)href=["']([^"']+)["']([^>]*?)>/gi, (match, p1, src, p3) => {
    if (!p1.includes('stylesheet') && !p3.includes('stylesheet')) return match;
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath) && assetPath.startsWith(inputDir)) {
      if (visitedStyles.has(assetPath)) return '';
      visitedStyles.add(assetPath);
      let css = fs.readFileSync(assetPath, 'utf8');
      css = bundleAssets(css, path.dirname(assetPath), depth + 1);
      const attrs = (p1 + p3).replace(/rel=["']stylesheet["']/gi, '').trim();
      return `<style ${attrs}>${css}</style>`;
    }
    return match;
  });

  // 4. CSS @import
  htmlContent = htmlContent.replace(/@import\s+(?:url\()?["']([^"']+)["']\)?\s*;?/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath) && assetPath.startsWith(inputDir)) {
      if (visitedStyles.has(assetPath)) return '';
      visitedStyles.add(assetPath);
      let css = fs.readFileSync(assetPath, 'utf8');
      css = bundleAssets(css, path.dirname(assetPath), depth + 1);
      return css;
    }
    return match;
  });

  // 5. Скрипты
  htmlContent = htmlContent.replace(/<script\s+([^>]*?)src=["']([^"']+)["']([^>]*?)><\/script>/gi, (match, p1, src, p3) => {
    if (src.startsWith('http') || src.startsWith('data:')) return match;
    const assetPath = path.resolve(baseDir, src);
    if (fs.existsSync(assetPath) && assetPath.startsWith(inputDir)) {
      const js = fs.readFileSync(assetPath, 'utf8');
      const attrs = (p1 + p3).trim();
      return `<script ${attrs}>${js}</script>`;
    }
    return match;
  });

  // 6. CSS url()
  htmlContent = htmlContent.replace(/url\(["']?([^"')]+)["']?\)/gi, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('#')) return match;
    const data = getAssetData(src, baseDir);
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
  visitedStyles.clear();
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
      const parts = href.split('#');
      const pathPart = parts[0].toLowerCase();
      const anchor = parts[1] || null;
      const fileName = pathPart.split('/').pop();
      if (manifest[fileName] !== undefined) targetIdx = manifest[fileName];
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
  
  let attrText = '';
  const attrRegex = /(?:alt|title)=["']([^"']+)["']/gi;
  let m;
  while ((m = attrRegex.exec(content)) !== null) { attrText += ' ' + m[1]; }

  const cleanForSearch = (content + attrText)
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]*>?/gm, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
    
  searchIndex.push(cleanForSearch);
  base64Chapters.push(Buffer.from(content).toString('base64'));
});

// БЕЗОПАСНАЯ ВСТАВКА В SCRIPT: Экранируем </script>
function safeJson(obj) {
  return JSON.stringify(obj).replace(/<\/script/gi, '<\\/script');
}

let templateContent = fs.readFileSync(templateFile, 'utf8')
  .replace('{{B64_CHAPTERS}}', safeJson(base64Chapters))
  .replace('{{TITLES}}', safeJson(titles))
  .replace('{{SEARCH_INDEX}}', safeJson(searchIndex));

fs.writeFileSync(outputFile, templateContent);
console.log(`Книга собрана: ${outputFile} (${files.length} глав). Безопасность: OK.`);
