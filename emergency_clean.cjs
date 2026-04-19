const fs = require('fs');
const path = require('path');
const dir = './outputs/pm_book_ru/chapters';

fs.readdirSync(dir).forEach(file => {
    if (!file.endsWith('.html')) return;
    const fullPath = path.join(dir, file);
    let content = fs.readFileSync(fullPath, 'utf8');

    console.log(`Cleaning ${file}...`);

    // 1. Remove ANY nested or simple term-link tags entirely, keeping ONLY the text inside
    // We do this multiple times to catch nested structures
    for(let i=0; i<5; i++) {
        content = content.replace(/<a[^>]*class="term-link"[^>]*>([\s\S]*?)<\/a>/gi, '$1');
    }

    // 2. Remove any other stray HTML tags that might have been partially injected
    // (Except for the core structure tags)
    
    // 3. Remove numeric artifacts stuck to Russian letters
    content = content.replace(/([а-яА-ЯёЁ])\d+/g, '$1');

    // 4. Remove duplicate nested text if it appeared
    // e.g. "Тройственное ограничениеТройственное ограничение"
    // (This is a heuristic, but safe for this specific book)
    // content = content.replace(/(Тройственное ограничение)\1/g, '$1');

    fs.writeFileSync(fullPath, content, 'utf8');
});
