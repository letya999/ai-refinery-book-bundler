const fs = require('fs');
const path = require('path');

const OUT_DIR = '.bookruns/egyptian_cross/stages/06_design/chapters_designed';
if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

function saveSummaryChapter(id, title, content) {
    const fileName = `chapter${id}.html`;
    const html = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>${title}</title>
    <link rel="stylesheet" href="assets/theme.css">
</head>
<body class="chapter-content">
    <h1>${title}</h1>
    ${content}
</body>
</html>`;
    fs.writeFileSync(path.join(OUT_DIR, fileName), html);
    console.log(`Summary V4 Saved: ${fileName} - ${title}`);
}

// 1. DRAMATIS PERSONAE
saveSummaryChapter(1, "ДЕЙСТВУЮЩИЕ ЛИЦА", `
<div class="grid">
    <div class="card"><b>Эллери Куин</b><p>Мастер дедукции. Прошел путь от замешательства до полного прозрения.</p></div>
    <div class="card"><b>Эндрю Ван</b><p>Скромный учитель? Или гениальный кукловод, создавший миф о Т-загадке?</p></div>
    <div class="card"><b>Томас Брэд</b><p>Миллионер из Брэдвуда, вторая жертва в Т-образном списке.</p></div>
    <div class="card"><b>Стивен Мегара</b><p>Старший из братьев Твэр, погибший на собственной яхте.</p></div>
    <div class="card"><b>Велия Крозак</b><p>Призрак из прошлого, чьим именем прикрывался настоящий убийца.</p></div>
    <div class="card"><b>Профессор Ярдли</b><p>Интеллектуальная опора Эллери и фанат египтологии.</p></div>
</div>
`);

// 2. CASE 1: ARROYO
saveSummaryChapter(2, "Дело №1: Кровавое Рождество", `
<div class="vis-diag">
  <svg viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg">
    <rect x="180" y="20" width="40" height="140" fill="var(--bg-deep)" style="opacity: 0.5;"/>
    <rect x="20" y="20" width="360" height="40" fill="var(--bg-deep)" style="opacity: 0.5;"/>
    <line x1="200" y1="120" x2="200" y2="60" stroke="var(--acc)" stroke-width="4"/>
    <line x1="160" y1="60" x2="240" y2="60" stroke="var(--acc)" stroke-width="4"/>
    <circle cx="200" cy="60" r="8" fill="var(--acc)" style="opacity: 0.4;"/>
    <text x="50" y="100" class="diag-text">Место: Арройо</text>
  </svg>
  <div class="caption">Т-образный указатель — место первой казни</div>
</div>

<p>Все началось в Западной Виргинии. Обезглавленное тело было прибито к дорожному знаку. Убийца оставил кровавое Т на двери дома учителя Вана.</p>

<div class="formula-card">
  <b>ГЛАВНАЯ ПОДМЕНА</b>
  <p>Считалось, что убит слуга Клинг. На самом деле жертвой стал сам <b>Велия Крозак</b>, которого Ван заманил в ловушку. Отсечение головы позволило скрыть личность Крозака.</p>
</div>
`);

// 3. SHADOW OF THE PAST
saveSummaryChapter(3, "Тень прошлого: Братья Твэр", `
<div class="translator">
  <div class="tr-col bad">
    <div class="tr-head bad">ВЕНДЕТТА</div>
    <ul>
        <li>Семья Крозак против семьи Твэр.</li>
        <li>20 лет ожидания мести.</li>
        <li>Ритуальные казни.</li>
    </ul>
  </div>
  <div class="tr-col good">
    <div class="tr-head good">ПРАВДА</div>
    <ul>
        <li>Андреа Твэр (Ван).</li>
        <li>Стефан Твэр (Мегара).</li>
        <li>Томислав Твэр (Брэд).</li>
    </ul>
  </div>
</div>

<p>Братья Твэр бежали из Черногории после ограбления Крозаков. Эндрю Ван (Андреа) затаил обиду на старших братьев, которые не поделились добычей.</p>
`);

// 4. MURDER IN BRADWOOD
saveSummaryChapter(4, "Смерть в Брэдвуде: Партия в шашки", `
<p>Второе убийство — Томас Брэд. Его находят распятым в собственном саду. Снова Т-образная форма.</p>

<div class="grid">
  <div class="card">
    <b>УЛИКА: ШАШКИ</b>
    <p>Перед смертью Брэд играл в шашки. Эллери понимает: убийца был ему знаком и вхож в дом.</p>
  </div>
  <div class="card">
    <b>ЛОЖНЫЙ СЛЕД</b>
    <p>Чета Линнов — международные авантюристы. Их побег запутал следствие, но они были лишь мелкими воришками, а не маньяками.</p>
  </div>
</div>

<div class="callout">
  <b>МЫСЛЬ КУИНА:</b> "Т-символизм становится слишком навязчивым. Это почерк или маскировка?"
</div>
`);

// 5. TRAGEDY ON THE HELEN
saveSummaryChapter(5, "Трагедия на яхте «Хелен»", `
<p>Стивен Мегара пытается выманить Крозака, снимая охрану. Результат — его обезглавленное тело на мачте яхты.</p>

<div class="vis-timeline">
  <div class="tl-step">
    <div class="tl-num">1</div>
    <div class="tl-content">Снятие охраны по приказу Мегары.</div>
  </div>
  <div class="tl-step">
    <div class="tl-num">2</div>
    <div class="tl-content">Ночное проникновение убийцы (Вана).</div>
  </div>
  <div class="tl-step">
    <div class="tl-num">3</div>
    <div class="tl-content">Убийство старшего брата и похищение денег.</div>
  </div>
</div>

<p>Ван инсценирует собственное "исчезновение", чтобы окончательно стать невидимым для закона.</p>
`);

// 6. THE IODINE CLUE
saveSummaryChapter(6, "Лаборатория логики: Пузырек йода", `
<div class="formula-card">
  <b>КЛЮЧЕВАЯ ОШИБКА УБИЙЦЫ</b>
  <p>В хижине старого Питера Эллери находит опрокинутый пузырек йода <b>без этикетки</b>. Рядом стоял пузырек с этикеткой.</p>
  <p><i>Вывод:</i> Только хозяин хижины (Ван) мог знать, что в пузырьке без этикетки — йод, и взять его в темноте или в спешке.</p>
</div>

<p>Следы у хижины: входящие следы были глубже выходящих. Убийца вносил тяжелую ношу (тело Клинга), чтобы выдать его за себя.</p>
`);

// 7. THE ANKH MYTH
saveSummaryChapter(7, "Миф об Анхе: Египетский след", `
<div class="vis-diag">
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="60" r="40" fill="none" stroke="var(--acc)" stroke-width="8"/>
    <line x1="100" y1="100" x2="100" y2="180" stroke="var(--acc)" stroke-width="8"/>
    <line x1="60" y1="110" x2="140" y2="110" stroke="var(--acc)" stroke-width="8"/>
  </svg>
  <div class="caption">Анх — Египетский крест</div>
</div>

<p>Профессор Ярдли предполагал ритуальный характер убийств. Форма Т напоминала древний египетский символ жизни. Ван использовал эту мистику, чтобы полиция искала "фанатика-египтолога", в то время как он преследовал корыстные цели.</p>
`);

// 8. THE FINAL ARREST
saveSummaryChapter(8, "Финал: Маска сорвана", `
<p>Погоня завершается в Чикаго. Эндрю Ван схвачен в отеле «Рокфор». У него случается припадок эпилепсии, после которого он признается в содеянном.</p>

<div class="stats">
  <div class="stat">
    <b class="stat-num">4</b>
    <span class="stat-label">Убийства</span>
  </div>
  <div class="stat">
    <b class="stat-num">1</b>
    <span class="stat-label">Подмена</span>
  </div>
  <div class="stat">
    <b class="stat-num">∞</b>
    <span class="stat-label">Жажда мести</span>
  </div>
</div>

<div class="card">
  <b>ЭПИЛОГ</b>
  <p>Эллери Куин закрывает дело. Он решает написать об этом книгу и назвать ее "Тайна Египетского креста" — в честь своего самого яркого и опасного заблуждения.</p>
</div>

<p style="text-align: center; font-style: italic; margin-top: 3rem;">Si finis bonus est, Totum bonum erit.</p>
`);
