# Plan: Enrich "Вы просто ему не нравитесь" book chapters with infographics

## Root cause analysis

### Problem 1: One OCR page = one giant paragraph
`pages_text()` joins OCR pages with `\n\n`. `paragraphs_to_html()` splits on `\n{2,}`.
Result: each "paragraph" is an entire scanned page (avg 2516 chars, max 3882 chars).
Within a page, text only has single `\n` (OCR line-wrap), never double-newlines.
Fix: add sentence-boundary splitting inside paragraphs longer than 600 chars.

### Problem 2: OCR soft hyphens never joined
Scanned books break words at line ends: "нару-\nшать" stays as is.
Fix: in `clean_text()`, join `word-\n` patterns into a single word.

### Problem 3: No infographics — chapters are walls of text
`convert_book.py` only produces `<p>`, `.letter-q`, `.letter-a` etc.
No stats blocks, no comparison grids, no key-quote callouts.
The `ne_uslozhnyay` chapters are rich because they were hand-written.
Fix: generate chapter-specific infographic sections in `build_chapter_html()`.

---

## File to modify: `scripts/convert_book.py`

### Change 1 — Fix soft-hyphen joining in `clean_text()`
Add after existing header removal:
```python
# Join OCR soft hyphens at end of line: "нару-\nшать" -> "нарушать"
text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
```

### Change 2 — Sentence-boundary paragraph splitting in `paragraphs_to_html()`
Before the existing `for para in paras` loop, add a helper:
```python
def split_long_para(text: str, max_len: int = 600) -> list[str]:
    """Split a paragraph at sentence boundaries if it exceeds max_len."""
    if len(text) <= max_len:
        return [text]
    # Split on '. ' or '! ' or '? ' followed by capital Cyrillic or Latin
    sentences = re.split(r'(?<=[.!?])\s+(?=[А-ЯЁA-Z])', text)
    chunks, current = [], ''
    for s in sentences:
        if current and len(current) + len(s) > max_len:
            chunks.append(current.strip())
            current = s
        else:
            current = (current + ' ' + s).strip() if current else s
    if current:
        chunks.append(current.strip())
    return chunks if chunks else [text]
```

Then replace `for para in paras:` with:
```python
expanded = []
for para in paras:
    expanded.extend(split_long_para(para))

for para in expanded:
```

### Change 3 — Chapter-specific infographic header in `build_chapter_html()`
Before the `body_html = paragraphs_to_html(body_text)` line, build a chapter-specific
stats/visual block based on `idx`. Each chapter gets:
- A `.stats` row with 2-3 relevant numbers or key facts (from `CHAPTER_STATS` dict)
- A `.callout` key-principle box (the chapter's single core message)
- For chapters 2-10: a `.compare-grid` with 2 columns: "Оправдание" vs "Правда"

#### `CHAPTER_STATS` dict (add near top of file, after CHAPTERS):
```python
CHAPTER_STATS = {
    1: {
        'stats': [
            ('100%', 'мужчин способны позвонить, если захотят'),
            ('0', 'оправданий, которые имеют смысл'),
            ('1', 'правило: если он хочет — он найдёт способ'),
        ],
        'callout': 'Мужчина, который хочет быть рядом — будет рядом. Всегда.',
        'compare': None,
    },
    2: {
        'stats': [
            ('7 дней', 'максимум, после которых ждать бессмысленно'),
            ('5 минут', 'сколько нужно, чтобы набрать номер'),
            ('0', 'уважительных причин не позвонить'),
        ],
        'callout': 'Если он не звонит — он не думает о тебе. Это и есть ответ.',
        'compare': ('«Он очень занят»', 'Он нашёл время поесть, поспать и посмотреть футбол'),
    },
    3: {
        'stats': [
            ('«просто дружим»', 'самая опасная фраза'),
            ('100%', 'ясности требуют нормальные отношения'),
            ('0', 'смысла в «неопределённости»'),
        ],
        'callout': 'Если он не называет вас парой — вы не пара. Это не туман, это ответ.',
        'compare': ('«Он боится слова «отношения»»', 'Он не боится — ему просто не нужны отношения с тобой'),
    },
    4: {
        'stats': [
            ('0', 'оправданий измене — ни одного'),
            ('1', 'раз — уже достаточно, чтобы уйти'),
            ('100%', 'ответственности лежит на том, кто изменил'),
        ],
        'callout': 'Измена — это выбор, а не ошибка. Хороший человек этот выбор не делает.',
        'compare': ('«Он больше не повторит»', 'Паттерн поведения не меняется без реальной работы над собой'),
    },
    5: {
        'stats': [
            ('трезвый', 'настоящий он — тот, кто не звонит'),
            ('пьяный', 'это не признание — это удобство'),
            ('0', 'шансов на нормальные отношения «только по пятницам»'),
        ],
        'callout': 'Пьяный звонок в 2 ночи — не романтика. Это сигнал: трезвым ты ему не нужна.',
        'compare': ('«Он раскрепощается после выпитого»', 'Трезвым он тебя вообще не вспоминает'),
    },
    6: {
        'stats': [
            ('5 лет', 'средний срок ожидания предложения «вот-вот»'),
            ('1', 'разговор решает — «женись или расстаёмся»'),
            ('100%', 'мужчин знают, хотят ли они жениться'),
        ],
        'callout': 'Мужчина, который хочет жениться — женится. Не «когда-нибудь», а сейчас.',
        'compare': ('«Он просто не готов»', 'Он готов — просто не с тобой'),
    },
    7: {
        'stats': [
            ('1', 'раз сказал «расстаёмся» — уже достаточно'),
            ('0', 'смысла в «последнем шансе» для него'),
            ('100%', 'уважения к себе требует принять его решение'),
        ],
        'callout': 'Расставание — это не переговоры. Услышала «нет» — поверь.',
        'compare': ('«Он вернётся, если я постараюсь»', 'Он уже принял решение. Ты просто ещё нет'),
    },
    8: {
        'stats': [
            ('0', 'сообщений = понятный ответ'),
            ('исчез', 'это тоже ответ, просто трусливый'),
            ('100%', 'твоего времени стоит тот, кто остаётся'),
        ],
        'callout': 'Исчезновение — это ответ. Самый жестокий, но самый честный.',
        'compare': ('«Может, с ним что-то случилось»', 'Instagram он обновляет. Просто не пишет тебе'),
    },
    9: {
        'stats': [
            ('женат', '= недоступен полностью'),
            ('0', 'времени на ожидание, пока он «разберётся»'),
            ('50%', 'себя ты отдаёшь тому, кто принадлежит другой'),
        ],
        'callout': 'Если он не целиком твой — он целиком чей-то другого. Середины нет.',
        'compare': ('«Он несчастлив в браке»', 'Недостаточно несчастлив, чтобы уйти'),
    },
    10: {
        'stats': [
            ('хорошие черты', 'не отменяют плохое поведение'),
            ('0', 'причин терпеть эгоизм ради «потенциала»'),
            ('сейчас', 'важнее, чем «каким он мог бы быть»'),
        ],
        'callout': 'Судить надо по поступкам, а не по потенциалу. Он уже показывает, кто он есть.',
        'compare': ('«Он просто такой человек»', 'Значит, тебе нужен другой человек'),
    },
    11: {
        'stats': [
            ('ты', 'заслуживаешь мужчину, который без ума от тебя'),
            ('100%', 'усилий должен вкладывать он, а не только ты'),
            ('сейчас', 'лучшее время отпустить то, что не работает'),
        ],
        'callout': 'Стандарты — это не каприз. Это уважение к себе.',
        'compare': None,
    },
}
```

#### Infographic HTML block (generated per chapter):
```python
def build_infographic(idx: int) -> str:
    data = CHAPTER_STATS.get(idx, {})
    if not data:
        return ''
    parts = []

    # Stats row
    stats = data.get('stats', [])
    if stats:
        stat_items = ''.join(
            f'<div class="stat"><div class="stat-num">{escape_html(v)}</div>'
            f'<div class="stat-label">{escape_html(l)}</div></div>'
            for v, l in stats
        )
        parts.append(f'<div class="stats">{stat_items}</div>')

    # Core callout
    callout = data.get('callout', '')
    if callout:
        parts.append(
            f'<div class="callout">'
            f'<div class="callout-icon">!</div>'
            f'<p>{escape_html(callout)}</p>'
            f'</div>'
        )

    # Compare grid
    compare = data.get('compare')
    if compare:
        excuse, truth = compare
        parts.append(
            f'<div class="compare-grid">'
            f'<div class="cg-col excuse"><div class="cg-head">Оправдание</div>'
            f'<p>{escape_html(excuse)}</p></div>'
            f'<div class="cg-col truth"><div class="cg-head">Правда</div>'
            f'<p>{escape_html(truth)}</p></div>'
            f'</div>'
        )

    return '\n'.join(parts)
```

Then in `build_chapter_html()`, insert `build_infographic(idx)` between the hero section and the `content-body` div:
```python
infographic_html = build_infographic(idx)
return f'''...
  </section>

  {infographic_html}

  <div class="content-body">
{body_html}
  </div>
...'''
```

### Change 4 — Add infographic CSS to chapter `<style>` block
Add to the per-chapter style in `build_chapter_html()`:
```css
.callout {
  display: flex; gap: 16px; align-items: flex-start;
  margin: 24px 0; padding: 18px 20px;
  border-radius: 14px; border: 1px solid var(--acc);
  background: rgba(114,216,255,.07);
}
.callout-icon {
  font-size: 1.4rem; font-weight: 900; color: var(--acc);
  line-height: 1; flex-shrink: 0; margin-top: 2px;
}
.callout p { margin: 0; font-size: 1.05rem; line-height: 1.55; }
.compare-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin: 24px 0;
}
.cg-col {
  padding: 18px 20px; border-radius: 14px;
}
.cg-col.excuse {
  border: 1px solid rgba(255,120,120,.35);
  background: rgba(255,80,80,.05);
}
.cg-col.truth {
  border: 1px solid rgba(135,239,201,.35);
  background: rgba(135,239,201,.05);
}
.cg-head {
  font-size: 11px; text-transform: uppercase; letter-spacing: .1em;
  font-weight: 700; margin-bottom: 10px;
}
.cg-col.excuse .cg-head { color: #ff8080; }
.cg-col.truth  .cg-head { color: var(--acc2); }
.cg-col p { margin: 0; font-size: .95rem; line-height: 1.5; }
@media (max-width: 600px) {
  .compare-grid { grid-template-columns: 1fr; }
}
```

---

## Execution order

1. Edit `scripts/convert_book.py`:
   - Add `CHAPTER_STATS` dict after `CHAPTERS`
   - Add `split_long_para()` helper before `paragraphs_to_html()`
   - Add soft-hyphen join to `clean_text()`
   - Add `build_infographic()` function before `build_chapter_html()`
   - Update `paragraphs_to_html()` to use `split_long_para()`
   - Update `build_chapter_html()` to call `build_infographic()` and include new CSS
2. Run: `python scripts/convert_book.py`
3. Run: `node skills/html-book-bundler/scripts/bundle.cjs --input chapters_nravites --output nravites-book.html`
4. Verify output at `http://localhost:7789/nravites-book.html`
