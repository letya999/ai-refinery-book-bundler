const fs = require('fs');
const path = require('path');

const glossary = {
    'term-sponsor': /Спонсор[ауе]?/g,
    'term-customer': /Заказчик[ауе]?/g,
    'term-pm': /(?:^|[^а-яА-ЯёЁ])(ПМ(?:-[ауе])?)(?=[^а-яА-ЯёЁ]|$)/g, // More robust for Russian word boundaries
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
            const match = args[0]; // full match with potential prefix
            const subMatch = args[1]; // the actual word if group used
            const offset = args[args.length - 2];
            const string = args[args.length - 1];
            
            // Adjust for prefix if we captured it
            let actualWord = match;
            let actualOffset = offset;
            if (subMatch && match !== subMatch) {
                const prefix = match.split(subMatch)[0];
                actualWord = subMatch;
                actualOffset = offset + prefix.length;
            }

            const before = string.slice(0, actualOffset);
            const after = string.slice(actualOffset + actualWord.length);
            
            // 1. Skip if inside ANY tag
            const openIdx = before.lastIndexOf('<');
            const closeIdx = before.lastIndexOf('>');
            if (openIdx > closeIdx) return match; 
            
            // 2. Skip if inside a header block
            const tagMatch = before.match(/<([a-zA-Z1-6]+)[^>]*>$/);
            if (tagMatch && /h[1-6]/i.test(tagMatch[1])) return match;

            // 3. Skip if already linked
            if (before.match(/<a[^>]*>$/) && after.match(/^[^<]*<\/a>/)) return match;
            
            modified = true;
            // Return with the prefix preserved if any
            const prefix = match.split(actualWord)[0];
            return `${prefix}<a href="#" class="term-link" data-term="${id}">${actualWord}</a>`;
        });
    }

    if (modified) {
        fs.writeFileSync(path.join(dir, file), content, 'utf8');
        console.log(`Linked terms in ${file}`);
    }
});
