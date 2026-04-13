const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const inputDir = path.resolve(args[args.indexOf('--input') + 1]);
const outputFile = path.resolve(args[args.indexOf('--output') + 1]);
const templateFile = path.resolve(args[args.indexOf('--template') + 1]);

console.log('Using Template:', templateFile);

const files = fs.readdirSync(inputDir).filter(f => f.endsWith('.html')).sort((a,b) => a.localeCompare(b, undefined, {numeric: true}));
const b64Chapters = [], titles = [], searchIndex = [];

files.forEach(file => {
  let content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  titles.push(titleMatch ? titleMatch[1] : file);
  searchIndex.push(file); // Упрощенный индекс для теста
  b64Chapters.push(Buffer.from(content, 'utf8').toString('base64'));
});

let template = fs.readFileSync(templateFile, 'utf8');
template = template.replace('{{B64_CHAPTERS}}', JSON.stringify(b64Chapters));
template = template.replace('{{TITLES}}', JSON.stringify(titles));
template = template.replace('{{SEARCH_INDEX}}', JSON.stringify(searchIndex));

fs.writeFileSync(outputFile, template);
console.log('Book Build Done!');
