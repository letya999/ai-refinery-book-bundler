const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

const RAW_DIR = '.bookruns/egyptian_cross/stages/01_ingest/chapters_raw';
const OUT_DIR = '.bookruns/egyptian_cross/stages/06_design/chapters_designed';

if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

let chapterCounter = 1;

function saveChunk(title, content) {
    const displayTitle = title.replace(/(Глава\s+\d+)([^\s:]+)/, '$1: $2').trim();
    
    const fileName = `chapter${chapterCounter++}.html`;
    const html = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>${displayTitle}</title>
    <link rel="stylesheet" href="assets/theme.css">
</head>
<body class="chapter-content">
    <h1>${displayTitle}</h1>
    ${content}
</body>
</html>`;
    fs.writeFileSync(path.join(OUT_DIR, fileName), html);
    console.log(`Saved: ${fileName} - ${displayTitle}`);
}

const files = fs.readdirSync(RAW_DIR).filter(f => f.endsWith('.html')).sort((a, b) => {
    const numA = parseInt(a.match(/\d+/)[0]);
    const numB = parseInt(b.match(/\d+/)[0]);
    return numA - numB;
});

files.forEach(file => {
    const filePath = path.join(RAW_DIR, file);
    const content = fs.readFileSync(filePath, 'utf8');
    const $ = cheerio.load(content);
    
    $('h1, h2, h3').first().remove();
    const body = $('body');

    if (file === 'chapter1.html') {
        let gridHtml = '<div class="grid">';
        $('p').each((i, el) => {
            const text = $(el).text();
            const parts = text.split(' — ');
            if (parts.length > 1) {
                gridHtml += `<div class="card"><b>${parts[0].trim()}</b><p>${parts[1].trim()}</p></div>`;
            } else {
                gridHtml += `<div class="card"><b>ИНФО</b><p>${text}</p></div>`;
            }
        });
        gridHtml += '</div>';
        saveChunk("ДЕЙСТВУЮЩИЕ ЛИЦА", gridHtml);
        return;
    }

    let currentTitle = $('title').text() || "Chapter";
    let currentContent = '';

    // INJECT SVG IN SPECIFIC CHAPTERS (based on sequence)
    if (file === 'chapter3.html') { // First mention of the T-crossroad
         currentContent += `<div class="vis-diag">
  <svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
    <rect x="180" y="20" width="40" height="180" fill="var(--bg-deep)" style="opacity: 0.5;"/>
    <rect x="20" y="20" width="360" height="40" fill="var(--bg-deep)" style="opacity: 0.5;"/>
    <line x1="200" y1="140" x2="200" y2="80" class="diag-link" style="stroke-width: 4;"/>
    <line x1="160" y1="80" x2="240" y2="80" class="diag-link" style="stroke-width: 4;"/>
    <text x="120" y="75" class="diag-text">Пагтаун</text>
    <text x="210" y="75" class="diag-text">Нью-Камберленд</text>
    <text x="205" y="135" class="diag-text">Арройо</text>
    <circle cx="200" cy="80" r="10" fill="var(--acc)" style="opacity: 0.3;"/>
  </svg>
  <div class="caption">Схема Т-образного перекрестка у Арройо</div>
</div>`;
    }

    body.children().each((i, el) => {
        const tagName = el.tagName.toLowerCase();
        const text = $(el).text();

        if (tagName === 'h1' || tagName === 'h2') {
            if (currentContent.trim()) saveChunk(currentTitle, currentContent);
            currentTitle = text.trim();
            currentContent = ''; 
            
            // Inject Ankh SVG if title matches Chapter 19 or similar
            if (currentTitle.includes('Глава 19')) {
                 currentContent += `<div class="vis-diag">
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="60" r="40" fill="none" stroke="var(--acc)" stroke-width="8"/>
    <line x1="100" y1="100" x2="100" y2="180" stroke="var(--acc)" stroke-width="8"/>
    <line x1="60" y1="110" x2="140" y2="110" stroke="var(--acc)" stroke-width="8"/>
  </svg>
  <div class="caption">Древний Египетский Крест (Анх) — символ жизни и Т-загадки</div>
</div>`;
            }
            return;
        }

        if (text.toLowerCase().includes('улика') || text.toLowerCase().includes('загадка') || (text.includes(' Т ') && text.length < 200)) {
             currentContent += `<div class="formula-card"><b>ЗАЦЕПКА</b><p>${text}</p></div>`;
             return;
        }

        if (text.startsWith('Эллери') && (text.includes('задумался') || text.includes('заметил') || text.includes('понял'))) {
             currentContent += `<div class="callout"><b>МЫСЛЬ КУИНА</b><p>${text}</p></div>`;
             return;
        }

        if (text.length > 250 && (text.startsWith('Дорога') || text.startsWith('Дом') || text.startsWith('Место') || text.startsWith('Труп'))) {
            currentContent += `<div class="card"><b>ОПИСАНИЕ</b><p>${text}</p></div>`;
            return;
        }

        currentContent += $(el).prop('outerHTML');
    });

    if (currentContent.trim()) saveChunk(currentTitle, currentContent);
});
