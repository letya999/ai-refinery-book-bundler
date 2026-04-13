
const fs = require('fs');
const content = fs.readFileSync('pm-book.html', 'utf8');
const lines = content.split('\n');
const line = lines[230];
let escapes = 0;
let results = [];
for (let i = 0; i < line.length; i++) {
  if (line[i] === '\\') {
    escapes++;
  } else {
    if (line[i] === '"') {
      if (escapes % 2 === 0) {
        results.push({ pos: i, snippet: line.substring(i - 30, i + 30) });
      }
    }
    escapes = 0;
  }
}
console.log(JSON.stringify(results, null, 2));
