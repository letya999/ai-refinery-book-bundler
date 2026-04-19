const fs = require('fs');
const path = require('path');

const glossary = {
    'term-sponsor': /Спонсор[ауе]?/g,
    'term-customer': /Заказчик[ауе]?/g,
    'term-pm': /\bПМ(?:-[ауе])?\b/g,
    'term-charter': /Устав(?:а|е|ом)? проекта|Устав(?:а|е|ом)?/g,
    'term-wbs': /ИСР|WBS/g,
    'term-triple': /Тройственн(?:ое|ому|ого) ограничени(?:е|я|ю)/g,
    'term-pert': /PERT/g
};

const dir = './outputs/pm_book_ru/chapters';

fs.readdirSync(dir).forEach(file => {
    if (!file.endsWith('.html') || file === 'chapter16.html') return;
    
    let content = fs.readFileSync(path.join(dir, file), 'utf8');
    
    // Clean up previous mess (any numbers followed by tags or just stray numbers injected by previous run)
    content = content.replace(/([а-яА-ЯёЁ])\d{3,}/g, '$1'); 
    
    let modified = false;

    for (const [id, regex] of Object.entries(glossary)) {
        // Use a simpler replace without complex group logic to avoid offset injection
        content = content.replace(regex, (match, offset, string) => {
            // Check if we are inside a tag
            const before = string.slice(0, offset);
            const after = string.slice(offset + match.length);
            
            if (before.lastIndexOf('<') > before.lastIndexOf('>')) return match;
            if (before.match(/<([a-zA-Z1-6]+)[^>]*>$/) && /h[1-6]/i.test(before.match(/<([a-zA-Z1-6]+)[^>]*>$/)[1])) return match;
            if (before.match(/<a[^>]*>$/) && after.match(/^[^<]*<\/a>/)) return match;

            modified = true;
            return `<a href="#${id}" class="term-link" data-term="${id}">${match}</a>`;
        });
    }

    if (modified) {
        fs.writeFileSync(path.join(dir, file), content, 'utf8');
        console.log(`Fixed and linked terms in ${file}`);
    }
});
