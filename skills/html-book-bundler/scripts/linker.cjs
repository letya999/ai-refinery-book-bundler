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
    let modified = false;

    for (const [id, regex] of Object.entries(glossary)) {
        content = content.replace(regex, (...args) => {
            const match = args[0];
            const offset = args[args.length - 2];
            const string = args[args.length - 1];
            
            const before = string.slice(0, offset);
            const after = string.slice(offset + match.length);
            
            // 1. Skip if inside ANY tag (especially H1-H6)
            const openIdx = before.lastIndexOf('<');
            const closeIdx = before.lastIndexOf('>');
            if (openIdx > closeIdx) return match; 
            
            // 2. EXTRA: Skip if inside a header block entirely
            // Look for the closest opening tag and check if it's h1-h6
            const tagMatch = before.match(/<([a-zA-Z1-6]+)[^>]*>$/);
            if (tagMatch && /h[1-6]/i.test(tagMatch[1])) return match;

            // 3. Skip if already linked
            if (before.match(/<a[^>]*>$/) && after.match(/^[^<]*<\/a>/)) return match;
            
            modified = true;
            return `<a href="#" class="term-link" data-term="${id}">${match}</a>`;
        });
    }

    if (modified) {
        fs.writeFileSync(path.join(dir, file), content, 'utf8');
        console.log(`Linked terms in ${file}`);
    }
});
