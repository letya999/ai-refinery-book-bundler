# Research Notes (2026-04-11)

Цель: улучшить стратегию single-file интерактивных книг (без библиотек или с controlled injection).

## Выводы

1. Базовый режим должен оставаться `Zero-Dependency`.
2. Для shell с `Blob`-главами обязательно вызывать `URL.revokeObjectURL()` при переключении главы.
3. Для доступности нужно учитывать `prefers-reduced-motion`.
4. Для тяжелых страниц и секций применять `content-visibility` и сокращать лишний рендер.
5. Для анимаций и графиков предпочтительнее native APIs (`canvas`, `requestAnimationFrame`, WAAPI), библиотеки — только при явной выгоде.

## Источники

### MDN / web.dev
- URL.revokeObjectURL: https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static
- URL.createObjectURL: https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static
- requestAnimationFrame: https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
- prefers-reduced-motion: https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- Web Animations API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API
- modulepreload: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/modulepreload
- content-visibility: https://web.dev/articles/content-visibility
- animations and performance: https://web.dev/animations-and-performance/
- code splitting: https://web.dev/articles/code-split-javascript

### Context7
- Anime.js (`/websites/animejs`): timeline control (`pause`, `remove`, `cancel`, `seek`) для управляемого lifecycle анимаций.
- Chart.js (`/chartjs/chart.js`): tree-shaking через выборочные импорты + `Chart.register(...)`; cleanup через `chart.destroy()`.
