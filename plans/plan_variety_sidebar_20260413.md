# Plan: Visual variety + sidebar scroll fix

## Problem 1: Sidebar does not scroll with 11 chapters
`.side` has `display: flex; flex-direction: column` but no `height` constraint.
`.list { flex: 1; overflow-y: auto }` needs a bounded parent height to activate scrolling.

**Fix in `skills/html-book-bundler/templates/default.html`:**
Change `.side` rule — add `height: 100vh; overflow: hidden;`:
```css
.side { 
  border-right: 1px solid var(--line); 
  background: linear-gradient(180deg, rgba(15, 31, 56, 0.95), rgba(11, 22, 45, 0.98)); 
  display: flex; flex-direction: column; backdrop-filter: blur(12px);
  height: 100vh; overflow: hidden;
}
```

---

## Problem 2: Every chapter has the same compare-grid (Оправдание/Правда)
Currently `build_infographic()` always generates: stats → callout → compare-grid.
11 chapters all look the same — monotonous.

**Fix in `scripts/convert_book.py`:**
Replace the single `compare` key with a `visual` key that specifies WHICH visual type to render.
Each chapter gets a unique visual block type.

### Visual types to implement (CSS-only, no canvas):

**`red_flags`** — numbered red warning signs list
```html
<div class="red-flags">
  <div class="rf-title">Красные флаги</div>
  <div class="rf-list">
    <div class="rf-item"><span class="rf-num">1</span><p>текст</p></div>
    ...
  </div>
</div>
```

**`compare_grid`** (existing) — Оправдание / Правда two columns

**`status_badge`** — one large centered status indicator
```html
<div class="status-badge">
  <div class="sb-icon">🔒</div>
  <div class="sb-label">ЖЕНАТ = НЕДОСТУПЕН</div>
  <div class="sb-sub">Не «немного», не «почти» — полностью</div>
</div>
```

**`checklist`** — "You deserve" list with colored bullets
```html
<div class="checklist">
  <div class="cl-title">Вы заслуживаете</div>
  <div class="cl-item yes"><span>✓</span><p>текст</p></div>
  <div class="cl-item no"><span>✗</span><p>текст</p></div>
</div>
```

**`timeline`** — horizontal step progression
```html
<div class="vis-timeline">
  <div class="tl-step"><div class="tl-dot"></div><p>текст</p></div>
  <div class="tl-arrow">→</div>
  ...
</div>
```

**`truth_scale`** — two columns but asymmetric: myth (crossed out) vs reality (highlighted)
```html
<div class="truth-scale">
  <div class="ts-col myth"><div class="ts-head">Миф</div><p>текст</p></div>
  <div class="ts-col reality"><div class="ts-head">Реальность</div><p>текст</p></div>
</div>
```

### Chapter visual assignments:

```python
CHAPTER_VISUALS = {
    1: None,  # Preface — no visual, just callout
    2: {
        'type': 'red_flags',
        'title': 'Красные флаги',
        'items': [
            'Прошло больше 7 дней — он не позвонил',
            'Пишет только поздно ночью или в выходные',
            'Всегда «очень занят», но в соцсетях активен',
            'Предлагает встретиться, но никогда не назначает конкретное время',
        ]
    },
    3: {
        'type': 'checklist',
        'title': 'Признаки настоящих отношений',
        'items': [
            ('yes', 'Он называет вас своей девушкой'),
            ('yes', 'Он знакомит вас с друзьями и семьёй'),
            ('yes', 'Он строит с вами планы на будущее'),
            ('no', '«Мы просто общаемся» или «не торопи события»'),
            ('no', 'Он избегает слова «отношения»'),
        ]
    },
    4: {
        'type': 'truth_scale',
        'myth': ('«Он больше не повторит»', 'Он раскаялся, это была ошибка, всё изменится'),
        'reality': ('Измена — это выбор', 'Паттерн не меняется без серьёзной работы над собой'),
    },
    5: {
        'type': 'timeline',
        'steps': [
            ('Пьяный звонок', 'Поздно ночью, после алкоголя'),
            ('Трезвое молчание', 'Днём — тишина, не звонит'),
            ('Снова пьяный', 'История повторяется'),
            ('Вывод', 'Трезвый — настоящий'),
        ]
    },
    6: {
        'type': 'red_flags',
        'title': 'Признаки что он не женится',
        'items': [
            'Вы вместе больше 2 лет, но тема брака «не поднималась»',
            'Он говорит «когда-нибудь» или «не сейчас»',
            'Он против официальных отношений, но живёт с вами',
            'Каждый раз когда вы поднимаете тему — он уходит от разговора',
        ]
    },
    7: {
        'type': 'compare_grid',
        'excuse': ('«Он вернётся, если я постараюсь»', 'Надо дать ему время, он просто запутался'),
        'truth': ('Он уже принял решение', 'Расставание — это не переговоры. Первое «нет» — окончательное'),
    },
    8: {
        'type': 'status_badge',
        'icon': '👻',
        'label': 'ИСЧЕЗ = ОТВЕТИЛ',
        'sub': 'Самый трусливый ответ, но вполне однозначный',
    },
    9: {
        'type': 'status_badge',
        'icon': '🔒',
        'label': 'ЖЕНАТ = НЕДОСТУПЕН',
        'sub': 'Не «немного», не «почти» — целиком принадлежит другой',
    },
    10: {
        'type': 'truth_scale',
        'myth': ('«Он хороший человек»', 'Добрый, умный, талантливый — просто иногда ведёт себя плохо'),
        'reality': ('Поступки важнее потенциала', 'Хорошие качества не отменяют плохого поведения. Судить по делам'),
    },
    11: {
        'type': 'checklist',
        'title': 'Вы заслуживаете',
        'items': [
            ('yes', 'Мужчину, который без ума от вас'),
            ('yes', 'Отношения, в которых вам не нужно угадывать его чувства'),
            ('yes', 'Человека, который сам звонит, сам предлагает встречу'),
            ('no', 'Ждать, гадать, оправдывать'),
            ('no', 'Быть «удобной», а не любимой'),
        ]
    },
}
```

### CSS for new visual types (add to chapter `<style>` block in `build_chapter_html()`):

```css
/* Red flags */
.red-flags { margin: 24px 0; }
.rf-title { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #ff8080; font-weight: 700; margin-bottom: 12px; }
.rf-list { display: grid; gap: 8px; }
.rf-item { display: flex; gap: 12px; align-items: flex-start; padding: 12px 16px; border-radius: 10px; background: rgba(255,80,80,.06); border: 1px solid rgba(255,80,80,.2); }
.rf-num { width: 24px; height: 24px; border-radius: 50%; background: #ff5c5c; color: #fff; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rf-item p { margin: 0; font-size: .92rem; line-height: 1.5; color: #ffd0d0; }

/* Checklist */
.checklist { margin: 24px 0; }
.cl-title { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--acc2); font-weight: 700; margin-bottom: 12px; }
.cl-item { display: flex; gap: 12px; align-items: flex-start; padding: 10px 14px; border-radius: 10px; margin-bottom: 6px; }
.cl-item.yes { background: rgba(135,239,201,.07); border: 1px solid rgba(135,239,201,.25); }
.cl-item.no  { background: rgba(255,80,80,.05); border: 1px solid rgba(255,80,80,.18); }
.cl-item span { font-size: 1rem; font-weight: 800; flex-shrink: 0; width: 20px; }
.cl-item.yes span { color: var(--acc2); }
.cl-item.no  span { color: #ff8080; }
.cl-item p { margin: 0; font-size: .92rem; line-height: 1.5; }

/* Timeline */
.vis-timeline { display: flex; align-items: flex-start; gap: 0; margin: 24px 0; flex-wrap: wrap; }
.tl-step { flex: 1; min-width: 120px; padding: 14px; text-align: center; background: rgba(114,216,255,.06); border: 1px solid var(--line); border-radius: 10px; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--acc); margin: 0 auto 8px; }
.tl-step:last-child .tl-dot { background: var(--acc2); }
.tl-step p { font-size: .82rem; color: var(--muted); margin: 0; line-height: 1.4; }
.tl-step strong { display: block; font-size: .88rem; color: var(--fg); margin-bottom: 4px; }
.tl-arrow { display: flex; align-items: center; padding: 0 6px; color: var(--line); font-size: 1.2rem; margin-top: 10px; }

/* Status badge */
.status-badge { margin: 24px 0; padding: 24px; text-align: center; border-radius: 16px; border: 1px solid var(--line); background: rgba(11,22,45,.6); }
.sb-icon { font-size: 2.4rem; margin-bottom: 10px; }
.sb-label { font-size: 1.3rem; font-weight: 800; letter-spacing: .06em; color: var(--acc); margin-bottom: 8px; }
.sb-sub { font-size: .9rem; color: var(--muted); line-height: 1.5; }

/* Truth scale */
.truth-scale { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }
.ts-col { padding: 18px 20px; border-radius: 14px; }
.ts-col.myth { border: 1px solid rgba(255,120,120,.3); background: rgba(255,80,80,.04); position: relative; }
.ts-col.myth::after { content: '✗'; position: absolute; top: 12px; right: 14px; color: #ff8080; font-size: 1rem; font-weight: 800; }
.ts-col.reality { border: 1px solid rgba(135,239,201,.3); background: rgba(135,239,201,.05); position: relative; }
.ts-col.reality::after { content: '✓'; position: absolute; top: 12px; right: 14px; color: var(--acc2); font-size: 1rem; font-weight: 800; }
.ts-head { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; margin-bottom: 10px; }
.ts-col.myth .ts-head { color: #ff8080; }
.ts-col.reality .ts-head { color: var(--acc2); }
.ts-col strong { display: block; font-size: .95rem; color: var(--fg); margin-bottom: 8px; line-height: 1.4; }
.ts-col p { margin: 0; font-size: .85rem; color: var(--muted); line-height: 1.5; }
@media (max-width: 600px) { .truth-scale, .compare-grid { grid-template-columns: 1fr; } }
```

### Updated `build_infographic()` function logic:
Replace the existing function with one that dispatches on `visual['type']`:

```python
def build_infographic(idx: int) -> str:
    data = CHAPTER_STATS.get(idx, {})
    if not data:
        return ''
    parts = []

    # Stats row (always shown)
    stats = data.get('stats', [])
    if stats:
        stat_items = ''.join(
            f'<div class="stat"><div class="stat-num">{escape_html(v)}</div>'
            f'<div class="stat-label">{escape_html(l)}</div></div>'
            for v, l in stats
        )
        parts.append(f'<div class="stats">{stat_items}</div>')

    # Callout (always shown)
    callout = data.get('callout', '')
    if callout:
        parts.append(
            f'<div class="callout"><div class="callout-icon">!</div>'
            f'<p>{escape_html(callout)}</p></div>'
        )

    # Chapter-specific visual block (dispatched by type)
    vis = CHAPTER_VISUALS.get(idx)
    if vis:
        parts.append(build_visual_block(vis))

    return '\n'.join(parts)
```

### New `build_visual_block(vis)` function:
Dispatches by `vis['type']` to render the appropriate HTML block.

---

## Execution order

1. Edit `skills/html-book-bundler/templates/default.html`:
   - Add `height: 100vh; overflow: hidden;` to `.side` CSS rule

2. Edit `scripts/convert_book.py`:
   - Add `CHAPTER_VISUALS` dict after `CHAPTER_INSIGHTS`
   - Add `build_visual_block(vis)` function before `build_infographic()`
   - Update `build_infographic()` to dispatch to `build_visual_block(vis)` instead of always compare-grid
   - Add all new CSS to the `<style>` block in `build_chapter_html()`
   - Remove old `compare` key logic from `build_infographic()` (replaced by CHAPTER_VISUALS)

3. Run: `python scripts/convert_book.py`
4. Run: `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_nravites --output nravites-book.html`
5. Also rebuild: `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_ne_uslozhnyay --output ne-uslozhnyay-ULTIMATE-v6.html`
