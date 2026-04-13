const fs = require('fs');
const path = require('path');
const { prepareChapter } = require('./chapter_processor.cjs');

const root = 'C:/Users/User/a_projects/no_complex_book';
const chaptersDir = path.join(root, 'chapters_ne_uslozhnyay');
const template = fs.readFileSync(
  path.join(root, 'skills/html-book-bundler/templates/default.html'),
  'utf-8'
);

// Always use the comprehensive bundler theme as the shared base.
// It covers all common components (stats, cards, accordion, canvas-wrap, translator, etc.)
// Chapters that have their own <style> blocks get them layered on top via CSS cascade.
const bundlerThemePath = path.join(root, 'skills/html-book-bundler/assets/theme.css');
const globalCSS = fs.readFileSync(bundlerThemePath, 'utf-8');
console.log(`Using theme: ${bundlerThemePath}`);

const chapterFiles = ['chapter1.html', 'chapter2.html', 'chapter3.html', 'chapter4.html', 'chapter5.html'];
const titles = [
  "Введение и смысл метода",
  "Схема P3.express: спираль",
  "NUP: принципы и оценка зрелости",
  "Раздел 3. Запуск проекта",
  "A01 — Назначить спонсора"
];

const b64Chapters = chapterFiles.map((file, i) => {
  const html = fs.readFileSync(path.join(chaptersDir, file), 'utf-8');
  console.log(`Processing chapter ${i + 1}: ${file}`);
  return prepareChapter(html, i, titles[i], chapterFiles.length, globalCSS);
});

const output = template
  .replace('{{BOOK_ID}}', 'ne_uslozhnyay_v6_final')
  .replace('{{GLOBAL_TITLES}}', JSON.stringify(titles))
  .replace('{{GLOBAL_SEARCH_INDEX}}', JSON.stringify(titles.map(t => t.toLowerCase())))
  .replace('{{LOCAL_B64_CHAPTERS}}', JSON.stringify(b64Chapters));

const outPath = path.join(root, 'ne-uslozhnyay-ULTIMATE-v6.html');
fs.writeFileSync(outPath, output);
console.log(`Done! Book written to: ${outPath}`);
