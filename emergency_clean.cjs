const fs = require('fs');
const path = require('path');
const dir = './outputs/pm_book_ru/chapters';

fs.readdirSync(dir).forEach(file => {
    if (!file.endsWith('.html')) return;
    const fullPath = path.join(dir, file);
    let content = fs.readFileSync(fullPath, 'utf8');

    console.log(`Deep cleaning ${file}...`);

    // 1. Remove recursive nested term-links (up to 5 levels)
    for(let i=0; i<5; i++) {
        content = content.replace(/<a[^>]*class="term-link"[^>]*>([\s\S]*?)<\/a>/gi, '$1');
    }

    // 2. Remove numeric artifacts stuck to Russian letters
    // Covers cases like "Спонсор432371", "ограничение142" etc.
    content = content.replace(/([а-яА-ЯёЁ])\d{2,10}/g, '$1');

    // 3. Remove numeric artifacts that might be wrapped in tags but are just noise
    // e.g. ">432371<"
    content = content.replace(/>\d{3,10}</g, '><');

    // 4. Clean up any broken tag fragments that might have resulted from previous failed replaces
    content = content.replace(/<a[^>]*class="term-link"[^>]*>/gi, '');
    content = content.replace(/<\/a>/gi, '');

    fs.writeFileSync(fullPath, content, 'utf8');
});
