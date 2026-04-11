const fs = require('fs');
const path = require('path');

const template = (titles, base64Chapters) => `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Интерактивная книга</title>
<style>
:root{--bg:#081423;--panel:#0f1f38;--panel2:#163056;--line:#395f9d;--text:#eef5ff;--muted:#adc2e1;--acc:#72d8ff;--acc2:#87efc9}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:radial-gradient(circle at 85% -20%,#2e5e9d 0,#152846 36%,#081423 72%);color:var(--text);font-family:"Trebuchet MS","Segoe UI Variable",Tahoma,sans-serif;overflow:hidden}
.app{display:grid;grid-template-columns:280px 1fr;height:100vh}
.app.side-hide{grid-template-columns:1fr}
.side{border-right:1px solid #2a4a7d;background:linear-gradient(180deg,var(--panel),#0b162d);display:flex;flex-direction:column}
.app.side-hide .side{display:none}
.brand{padding:16px 14px;border-bottom:1px solid #223258}
.brand h1{font-size:16px;line-height:1.2;margin-bottom:6px}
.brand p{font-size:12px;color:var(--muted)}
.list{padding:10px;display:grid;gap:8px;overflow:auto}
.ch{all:unset;cursor:pointer;padding:10px 12px;border-radius:10px;border:1px solid #3f66a6;background:rgba(17,31,57,.72);font-size:13px;line-height:1.35;color:#dce9ff}
.ch:hover{border-color:var(--acc)}
.ch.on{background:linear-gradient(135deg,rgba(114,216,255,.2),rgba(135,239,201,.14));border-color:var(--acc)}
.foot{margin-top:auto;padding:10px;border-top:1px solid #223258;color:var(--muted);font-size:12px}
.main{display:flex;flex-direction:column;min-width:0}
.top{height:48px;flex-shrink:0;border-bottom:1px solid #2c4d80;background:#0d1931;display:flex;align-items:center;gap:10px;padding:0 10px}
.top button{all:unset;cursor:pointer;padding:6px 10px;border:1px solid #456fb0;border-radius:8px;color:#d6e7ff;font-size:12px}
.top button:hover{border-color:var(--acc);color:#fff}
.tt{font-size:13px;color:#cfe0ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tt b{color:#fff;font-weight:700}
.prog{height:4px;background:#234071;position:relative}
.prog>i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--acc),var(--acc2));transition:width .25s}
.frame{flex:1;min-height:0}
.frame iframe{width:100%;height:100%;border:none;background:#0c1831;display:block}
.mob{display:inline-block}
@media (prefers-reduced-motion: reduce){
  *{animation:none!important;transition:none!important}
}
@media (max-width:900px){
  .app{grid-template-columns:1fr}
  .side{position:fixed;left:0;top:0;bottom:0;width:86vw;max-width:320px;transform:translateX(-100%);transition:.25s;z-index:20;box-shadow:10px 0 30px rgba(0,0,0,.4)}
  .side.open{transform:translateX(0)}
  .app.side-hide .side{display:flex}
}
</style>
</head>
<body>
<div class="app">
  <aside class="side" id="side">
    <div class="brand">
      <h1>Интерактивная книга</h1>
      <p>Ознакомительный фрагмент</p>
    </div>
    <div class="list" id="list"></div>
    <div class="foot">Навигация: главы, кнопки, клавиши ← →</div>
  </aside>

  <section class="main">
    <div class="top">
      <button class="mob" id="menu">☰</button>
      <button id="prev">← Назад</button>
      <button id="next">Вперед →</button>
      <div class="tt" id="tt"></div>
    </div>
    <div class="prog"><i id="bar"></i></div>
    <div class="frame"><iframe id="fr"></iframe></div>
  </section>
</div>

<script>
const B64 = ${JSON.stringify(base64Chapters)};
const T = ${JSON.stringify(titles)};
let cur = 0;
let curBlobUrl = null;

const fr = document.getElementById('fr');
const tt = document.getElementById('tt');
const bar = document.getElementById('bar');
const list = document.getElementById('list');
const side = document.getElementById('side');
const menu = document.getElementById('menu');
const app = document.querySelector('.app');

menu.onclick = (e) => {
  e.stopPropagation();
  if (window.matchMedia('(max-width: 900px)').matches) {
    side.classList.toggle('open');
  } else {
    app.classList.toggle('side-hide');
  }
};

function buildList() {
  list.innerHTML = '';
  T.forEach((t, i) => {
    const b = document.createElement('button');
    b.className = 'ch';
    b.dataset.i = i;
    b.innerHTML = '<b>Глава ' + (i + 1) + '</b><br>' + t;
    b.onclick = () => go(i, true);
    list.appendChild(b);
  });
}

function go(i, close = false) {
  if (i < 0 || i >= B64.length) return;
  cur = i;

  const bin = atob(B64[i]);
  const bytes = new Uint8Array(bin.length);
  for (let j = 0; j < bin.length; j++) bytes[j] = bin.charCodeAt(j);

  const blob = new Blob([bytes], { type: 'text/html;charset=utf-8' });
  if (curBlobUrl) URL.revokeObjectURL(curBlobUrl);
  curBlobUrl = URL.createObjectURL(blob);
  fr.src = curBlobUrl;

  tt.innerHTML = '<b>Глава ' + (i + 1) + '</b>&ensp;' + T[i];
  bar.style.width = ((i + 1) / B64.length * 100) + '%';

  document.querySelectorAll('.ch').forEach(el => {
    el.classList.toggle('on', Number(el.dataset.i) === i);
  });

  localStorage.setItem('book_last_chapter', String(i));
  if (close) side.classList.remove('open');
}

document.getElementById('prev').onclick = () => go(cur - 1);
document.getElementById('next').onclick = () => go(cur + 1);
window.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') go(cur - 1);
  if (e.key === 'ArrowRight') go(cur + 1);
});
document.addEventListener('click', (e) => {
  if (!window.matchMedia('(max-width: 900px)').matches) return;
  if (!side.classList.contains('open')) return;
  if (e.target.closest('#side') || e.target.closest('#menu')) return;
  side.classList.remove('open');
});

buildList();
const saved = Number(localStorage.getItem('book_last_chapter'));
go(Number.isFinite(saved) ? saved : 0);
</script>
</body>
</html>`;

const args = process.argv.slice(2);
const inputDir = args[args.indexOf('--input') + 1];
const outputFile = args[args.indexOf('--output') + 1];

if (!inputDir || !outputFile) {
  console.log('Использование: node bundle.cjs --input <папка> --output <файл.html>');
  process.exit(1);
}

const files = fs.readdirSync(inputDir)
  .filter(f => f.endsWith('.html'))
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));

const titles = [];
const base64Chapters = [];

files.forEach(file => {
  const content = fs.readFileSync(path.join(inputDir, file), 'utf8');
  const titleMatch = content.match(/<title>(.*?)<\/title>/i);
  titles.push(titleMatch ? titleMatch[1] : file);
  base64Chapters.push(Buffer.from(content).toString('base64'));
});

fs.writeFileSync(outputFile, template(titles, base64Chapters));
console.log(`Книга успешно собрана: ${outputFile} (${files.length} глав)`);
