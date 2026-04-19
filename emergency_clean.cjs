const fs = require('fs');
const path = require('path');
const dir = './outputs/pm_book_ru/chapters';

fs.readdirSync(dir).forEach(file => {
    if (!file.endsWith('.html')) return;
    const fullPath = path.join(dir, file);
    let content = fs.readFileSync(fullPath, 'utf8');

    console.log(`Smart cleaning ${file}...`);

    // 1. Remove recursive nested term-links (Safety pass)
    for(let i=0; i<3; i++) {
        content = content.replace(/<a[^>]*class="term-link"[^>]*>([\s\S]*?)<\/a>/gi, '$1');
    }

    // 2. Remove numeric artifacts stuck to Russian or English letters 
    // BUT only if NOT inside an attribute (using a simplified lookbehind-like check)
    // We target numbers that appear in plain text
    content = content.replace(/([а-яА-ЯёЁa-zA-Z])\d{3,15}(?![^<]*>)/g, '$1');

    // 3. Remove numeric artifacts stuck to closing tags (text nodes only)
    content = content.replace(/(<\/a>|<\/span>|<\/h[1-6]>)\d{3,15}/g, '$1');

    // 4. Remove numeric artifacts that are just "floating" in tags
    content = content.replace(/>\d{4,15}</g, '><');

    fs.writeFileSync(fullPath, content, 'utf8');
});
