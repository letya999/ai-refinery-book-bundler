const fs = require('fs');
const path = require('path');

const sourceDir = '.bookruns/sql_gruber/stages/01_ingest';
const destDir = '.bookruns/sql_gruber/stages/02_consolidated';

const modules = [
  { name: 'Модуль 1: Основы и Синтаксис', chapters: [2, 3, 4] },
  { name: 'Модуль 2: Фильтрация и Сортировка', chapters: [5, 6, 7] },
  { name: 'Модуль 3: Группировка и Агрегация', chapters: [8, 9, 10] },
  { name: 'Модуль 4: Работа с Несколькими Таблицами', chapters: [11, 12, 13] },
  { name: 'Модуль 5: Подзапросы и Объединения', chapters: [14, 15, 16] },
  { name: 'Модуль 6: Манипуляция Данными (DML)', chapters: [17, 18, 19, 20, 21] },
  { name: 'Модуль 7: Проектирование и Администрирование', chapters: [22, 23, 24, 25, 26, 27, 28, 29, 30] }
];

modules.forEach((mod, idx) => {
  let combinedBody = '';
  mod.chapters.forEach(chNum => {
    const f = path.join(sourceDir, `chapter${chNum}.html`);
    if (fs.existsSync(f)) {
      const html = fs.readFileSync(f, 'utf8');
      // Extract content between <body> tags
      const match = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
      let bodyContent = match ? match[1] : html;
      
      // Clean up internal document tags if any were accidentally included
      bodyContent = bodyContent.replace(/<(head|title|style|script)[\s\S]*?<\/\1>/gi, '');
      bodyContent = bodyContent.replace(/<\/?(html|body)[^>]*>/gi, '');
      
      combinedBody += `\n<section class="chapter-unit" data-original-chapter="${chNum}">\n${bodyContent}\n</section>\n`;
    }
  });

  const finalHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${mod.name}</title>
</head>
<body>
  <div class="wrap">
    <h1>${mod.name}</h1>
    ${combinedBody}
  </div>
</body>
</html>`;

  fs.writeFileSync(path.join(destDir, `chapter${idx + 1}.html`), finalHtml);
});

console.log('Consolidation with REGEX complete.');
