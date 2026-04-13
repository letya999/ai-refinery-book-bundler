# Visual Bank: HTML Book Bundler Components

Use these CSS-only components in your chapter HTML files to make the book more engaging. All classes are defined in `assets/theme.css`.

## 1. Stats and Quick Info
Perfect for "Inputs", "Outputs", or key metrics.

```html
<div class="stats">
  <div class="stat">
    <b class="stat-num">ВХОД</b>
    <span class="stat-label">Устав проекта</span>
  </div>
  <div class="stat">
    <b class="stat-num">ВЫХОД</b>
    <span class="stat-label">План управления</span>
  </div>
</div>
```

## 2. Comparison (Good vs Bad / Myth vs Reality)
Ideal for contrasting approaches or clearing misconceptions.

```html
<div class="translator">
  <div class="tr-col bad">
    <div class="tr-head bad">КАК НЕ НАДО</div>
    <ul>
      <li>Писать план для галочки</li>
      <li>Скрывать риски от спонсора</li>
    </ul>
  </div>
  <div class="tr-col good">
    <div class="tr-head good">КАК ПРАВИЛЬНО</div>
    <ul>
      <li>План — это инструмент общения</li>
      <li>Риски — это повод для маневра</li>
    </ul>
  </div>
</div>
```

## 3. Info Cards
Use for definitions, key concepts, or "Red Flags".

```html
<div class="grid">
  <div class="card">
    <b>УСТАВ</b>
    <p>Документ, легитимизирующий власть менеджера проекта.</p>
  </div>
  <div class="card">
    <b>СОДЕРЖАНИЕ</b>
    <p>То, что ВХОДИТ и то, что НЕ ВХОДИТ в рамки работ.</p>
  </div>
</div>
```

## 4. Accordion (Expandable Content)
Great for detailed examples or Q&A.

```html
<div class="acc-item">
  <div class="acc-head">Пример из практики (нажми, чтобы развернуть)</div>
  <div class="acc-body">
    <p>Здесь может быть длинный текст истории или детальный кейс...</p>
  </div>
</div>
<script>
// Logic handled by default.html shell, or add simple toggle:
document.querySelectorAll('.acc-head').forEach(h => {
  h.onclick = () => h.parentElement.classList.toggle('open');
});
</script>
```

## 5. Badges
Small inline or block labels for status/types.

```html
<span class="badge">КРИТИЧНО</span>
<span class="badge" style="border-color:var(--acc2);color:var(--acc2)">СОВЕТ</span>
```

## 6. Timeline / Steps
(Custom CSS added to chapter)

```html
<div class="vis-timeline">
  <div class="tl-step">
    <div class="tl-num">1</div>
    <div class="tl-content"><b>Инициация</b>: Подпишите устав.</div>
  </div>
  <div class="tl-step">
    <div class="tl-num">2</div>
    <div class="tl-content"><b>Планирование</b>: Соберите требования.</div>
  </div>
</div>
```
