# Plan: Visual Rewrite — нравится chapters text density fix

## Problem diagnosis
- Chapter 7: 30 `<p>` tags, 15,225 chars of OCR text, page height 5355px
- Most `<p>` are walls of raw OCR narrative text with no visual breaks
- The Q&A styled blocks (letter-q, letter-a) ARE good, but buried under text
- The hero infographic (stats + callout + compare-grid) is good — need same energy throughout

## Goal
Transform each chapter from "OCR dump with some styled boxes" to:
1. Hero section (already good: stats + callout + compare-grid)
2. "Сигнал главы" — a simple visual signal-strength meter (CSS only, 5 bars)
3. "Темы главы" — the excuse headings as visual cards/chips shown upfront
4. Intro text collapsed: show first 2 paragraphs, rest hidden behind "Читать вступление ▼" toggle
5. Q&A section fully visible and prominent — letters/responses are the core visual content
6. Long raw `<p>` paragraphs (>500 chars) auto-collapsed with "Показать ещё..." toggle
7. Auto-extracted insight pullquotes: 1-2 short impactful sentences per chapter displayed as large styled blockquotes

## Files to modify: `scripts/convert_book.py`

### Change 1: CHAPTER_META — add signal strength per chapter (1-5)
Add to CHAPTER_STATS each entry a `'signal': N` key (1=mild, 5=critical):
- ch1 (Предисловие): signal=1
- ch2 (Не звонит): signal=4
- ch3 (Не признаёт): signal=3
- ch4 (Изменяет): signal=5
- ch5 (Только пьяным): signal=5
- ch6 (Не женится): signal=3
- ch7 (Расстаться): signal=5
- ch8 (Исчез): signal=5
- ch9 (Женат): signal=5
- ch10 (Придурок): signal=4
- ch11 (Заключение): signal=1

### Change 2: CHAPTER_INSIGHTS — add 2 key insight quotes per chapter
Add a separate dict CHAPTER_INSIGHTS = { 1: ['quote1', 'quote2'], 2: [...], ... }
These are short impactful sentences (max 160 chars) that will appear as pullquotes.
Example ch2: ['Если он не звонит — он не думает о вас. Это единственное объяснение.', 'Мужчина, который хочет позвонить, — позвонит. Даже если он занят, устал или болен.']

Add insights for all 11 chapters.

### Change 3: build_signal_meter(signal: int) -> str
CSS-only signal meter: 5 vertical bars, filled=red, empty=dark.
```html
<div class="signal-meter">
  <div class="signal-label">Сигнал тревоги</div>
  <div class="signal-bars">
    <div class="bar filled"></div>   <!-- repeat signal times -->
    <div class="bar empty"></div>    <!-- repeat (5-signal) times -->
  </div>
</div>
```

### Change 4: build_insights_html(idx: int) -> str  
Returns 1-2 `<blockquote class="insight">` elements from CHAPTER_INSIGHTS[idx].
```html
<blockquote class="insight">
  <p>Мужчина, который хочет позвонить, — позвонит.</p>
</blockquote>
```

### Change 5: Rewrite paragraphs_to_html() output structure
Track state while iterating:
- `intro_paras`: collect `<p>` before first excuse-title or letter-q
- `qa_paras`: collect everything from first excuse/letter onwards

Build output:
```
1. [intro block] — first 2 paras shown, rest in collapsible:
   <div class="intro-text">
     {first_2_paras}
     <details class="more-text">
       <summary>Читать вступление ▼</summary>
       {remaining_intro_paras}
     </details>
   </div>

2. [insights] — 1st insight pullquote

3. [qa block] — all excuse-titles, letters, responses, success-stories, summary-boxes, workbooks
   BUT: long raw <p> tags (>500 chars) inside the qa section become:
   <details class="long-para">
     <summary>{first 120 chars}...</summary>
     <p>{full text}</p>
   </details>

4. [2nd insight] — placed before summary-box if one exists
```

### Change 6: Update CSS in build_chapter_html()
Add to the `<style>` block:

```css
/* Signal meter */
.signal-meter { margin: 20px 0 28px; }
.signal-label { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 8px; }
.signal-bars { display: flex; gap: 4px; align-items: flex-end; height: 28px; }
.signal-bars .bar { width: 14px; border-radius: 3px 3px 0 0; transition: opacity .2s; }
.signal-bars .bar.filled { background: #ff5c5c; }
.signal-bars .bar.empty  { background: rgba(255,92,92,.18); }
.signal-bars .bar:nth-child(1) { height: 30%; }
.signal-bars .bar:nth-child(2) { height: 50%; }
.signal-bars .bar:nth-child(3) { height: 65%; }
.signal-bars .bar:nth-child(4) { height: 80%; }
.signal-bars .bar:nth-child(5) { height: 100%; }

/* Insight pullquote */
blockquote.insight {
  margin: 28px 0; padding: 20px 24px;
  border-left: 4px solid var(--acc);
  background: rgba(114,216,255,.06);
  border-radius: 0 14px 14px 0;
}
blockquote.insight p {
  margin: 0; font-size: 1.15rem; font-style: italic;
  line-height: 1.6; color: var(--fg);
}

/* Intro text collapsible */
.intro-text { margin-bottom: 24px; }
details.more-text summary, details.long-para summary {
  cursor: pointer; color: var(--acc); font-size: .9rem;
  padding: 6px 0; list-style: none; user-select: none;
}
details.more-text summary::-webkit-details-marker,
details.long-para summary::-webkit-details-marker { display: none; }
details.more-text[open] summary { color: var(--muted); }
details.long-para {
  margin-bottom: 14px;
  border-left: 2px solid var(--line);
  padding-left: 14px;
}
details.long-para summary {
  color: var(--muted); font-size: .88rem; line-height: 1.5;
}
details.long-para[open] summary { display: none; }
```

### Change 7: Update build_chapter_html() to include signal meter + insights
After `infographic_html = build_infographic(idx)`, add:
```python
signal = CHAPTER_STATS.get(idx, {}).get('signal', 3)
signal_html = build_signal_meter(signal)
insights_html = build_insights_html(idx)
```

Place in template:
```
hero section
infographic_html   (stats + callout + compare-grid)
signal_html        (signal meter)
insights[0]        (first pullquote)
content-body       (restructured: intro-collapsed + qa blocks)
insights[1]        (second pullquote, before summary-box)
```

Actually, simpler: put both insights inside content-body via the restructured paragraphs_to_html, or pass insights to it. Easiest: pass `insights` list to a new `structured_body_html(text, insights)` function that replaces `paragraphs_to_html`.

## Revised function signature
```python
def structured_body_html(text: str, insights: list[str]) -> str:
    # replaces paragraphs_to_html
    # returns full content-body innerHTML with intro-collapse + insights intercalated
```

## Execution order
1. Edit `scripts/convert_book.py`:
   - Add `signal` key to each entry in CHAPTER_STATS
   - Add CHAPTER_INSIGHTS dict (all 11 chapters)
   - Add build_signal_meter(signal) function
   - Add build_insights_html(idx) function  
   - Rewrite paragraphs_to_html into structured_body_html(text, insights)
   - Update build_chapter_html() to use new functions
   - Add all new CSS to the chapter <style> block
2. Run: `C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe scripts/convert_book.py`
3. Run: `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_nravites --output nravites-book.html`
4. Verify output visually

## CHAPTER_INSIGHTS data

```python
CHAPTER_INSIGHTS = {
    1: [
        'Мужчина, который хочет оказаться рядом, — оказывается рядом. Без исключений.',
        'Мы написали эту книгу, потому что вы заслуживаете знать правду: оправданий не существует.',
    ],
    2: [
        'Если он не звонит — он не думает о вас. Это единственное объяснение.',
        'Мужчина, который хочет позвонить, позвонит. Даже если он занят, устал или болен.',
    ],
    3: [
        'Если он не называет вас своей девушкой — вы ею не являетесь.',
        '«Мы просто общаемся» — это не стадия. Это его ответ.',
    ],
    4: [
        'Измена — это не ошибка. Это решение, которое принимается осознанно.',
        'Хороший человек не причиняет такой боли. Это не жестоко — это правда.',
    ],
    5: [
        'Трезвый — настоящий. Пьяный — удобный. Разница принципиальная.',
        'Если он звонит только после полуночи — ты ему не нравишься. Ты ему удобна.',
    ],
    6: [
        'Мужчина, который хочет жениться, женится. Не через год, не «когда всё наладится».',
        'Ожидание предложения — это не романтика. Это потеря времени.',
    ],
    7: [
        'Расставание — это не начало переговоров. Это конец.',
        'Уважать себя — значит принять его решение с первого раза.',
    ],
    8: [
        'Исчезновение — это ответ. Самый трусливый, но вполне однозначный.',
        'Человек, которому важно, — не исчезает. Он объясняется.',
    ],
    9: [
        'Женатый мужчина недоступен. Не «немного», не «почти» — полностью.',
        'Он несчастлив в браке? Недостаточно, чтобы уйти. Достаточно, чтобы изменять.',
    ],
    10: [
        'Хорошие качества не отменяют плохого поведения. Никогда.',
        'Судить человека надо по его поступкам, а не по его потенциалу.',
    ],
    11: [
        'Вы заслуживаете мужчину, который без ума от вас. Не «терпит», не «ценит» — без ума.',
        'Стандарты — это не высокомерие. Это знание своей ценности.',
    ],
}
```
