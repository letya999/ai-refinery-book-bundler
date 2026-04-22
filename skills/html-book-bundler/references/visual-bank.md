# Visual Bank: HTML Book Bundler Components (v7.0)

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

## 4. Accordion (Expandable Content) - NATIVE ONLY 🚨
Great for detailed examples or Q&A. **NEVER use JS-driven div elements**. Always use native `<details>` and `<summary>`.

```html
<details class="acc-item">
  <summary class="acc-head">Пример из практики (нажми, чтобы развернуть)</summary>
  <div class="acc-body">
    <p>Здесь может быть длинный текст истории или детальный кейс...</p>
  </div>
</details>
```

## 5. Badges
Small inline or block labels for status/types. Can be added to cards or lists.

```html
<span class="badge warn">КРИТИЧНО</span>
<span class="badge bad">ОШИБКА</span>
<span class="badge">СОВЕТ</span>
```

## 6. Timeline / Steps
Used for describing stages, sequences, and historical paths.

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

## 8. Classic Detective / Noir (v9.0)
Special preset for mystery, vintage, and archive-style books.

### Typography
- **Primary:** `EB Garamond` or `Lora` (Serif).
- **Display:** `Playfair Display` (Bold/Black).

### Photo Frame V2 (Evidence Style)
```html
<div class="photo-frame">
  <img src="assets/clue1.webp" alt="Улика">
  <div class="photo-label">ВЕЩЕСТВЕННОЕ ДОКАЗАТЕЛЬСТВО: НОЖ</div>
</div>
```
- **Filter:** `filter: grayscale(1) contrast(1.1) sepia(0.05);`

### Evidence Card
```html
<div class="evidence-card">
  <b>ВЕЩЕСТВЕННОЕ ДОКАЗАТЕЛЬСТВО</b>
  <p>Описание улики или показания свидетеля...</p>
</div>
```
- **CSS:** `border-left: 5px solid var(--acc); background: var(--bg-deep); padding: 1.5rem;`