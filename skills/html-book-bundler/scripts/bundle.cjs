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
  const content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  titles.push(titleMatch ? titleMatch[1] : file);
  
  // Simple search indexing: strip HTML tags and normalize spaces
  const textContent = content.replace(/<[^>]*>?/gm, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
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
