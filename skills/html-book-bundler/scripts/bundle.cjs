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

if (!fs.existsSync(templateFile)) {
  console.error(`Ошибка: Файл шаблона не найден по пути ${templateFile}`);
  process.exit(1);
}

const files = fs.readdirSync(inputDir)
  .filter(f => f.endsWith('.html'))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));

const titles = [];
const base64Chapters = [];
const searchIndex = [];

files.forEach(file => {
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  titles.push(titleMatch ? titleMatch[1] : file);
  
  // Inject navigation bridge script
  const bridgeScript = `
<script>
document.addEventListener('click', e => {
  const a = e.target.closest('a');
  if (a && a.getAttribute('href')) {
    const href = a.getAttribute('href');
    if (href.startsWith('http') || href.startsWith('mailto:')) return;
    
    e.preventDefault();
    // Logic: find chapter index by filename or keyword in href
    let targetIdx = -1;
    let anchor = null;
    
    const parts = href.split('#');
    const pathPart = parts[0].toLowerCase();
    anchor = parts[1] || null;
    
    if (pathPart.includes('chapter')) {
       const m = pathPart.match(/chapter(\\d+)/);
       if (m) targetIdx = parseInt(m[1]) - 1;
    } else if (!pathPart) {
       // Just anchor in current chapter
       const el = document.getElementById(anchor);
       if (el) el.scrollIntoView({behavior:'smooth'});
       return;
    }
    
    if (targetIdx !== -1 && window.parent) {
      window.parent.postMessage({ action: 'bookGo', chapterIdx: targetIdx, anchorId: anchor }, '*');
    }
  }
});
</script>
  `;
  content = content.replace('</body>', bridgeScript + '</body>');

  // Simple search indexing: strip HTML tags and normalize spaces
  const textContent = content.replace(/<[^>]*>?/gm, ' ').replace(/\\s+/g, ' ').trim().toLowerCase();
  searchIndex.push(textContent);

  base64Chapters.push(Buffer.from(content).toString('base64'));
});

let templateContent = fs.readFileSync(templateFile, 'utf8');
templateContent = templateContent
  .replace('{{B64_CHAPTERS}}', JSON.stringify(base64Chapters))
  .replace('{{TITLES}}', JSON.stringify(titles))
  .replace('{{SEARCH_INDEX}}', JSON.stringify(searchIndex));

fs.writeFileSync(outputFile, templateContent);
console.log(`Книга успешно собрана: ${outputFile} (${files.length} глав)`);
