#!/usr/bin/env python3
"""
Converts OCR'd pages JSON into structured HTML chapters for the html-book-bundler skill.
Book: "Вы просто ему не нравитесь" (He's Just Not That Into You) - Behrendt & Tuccillo
"""
import json, re, os, sys, textwrap

sys.stdout.reconfigure(encoding='utf-8')

PAGES_JSON  = r"C:\Users\User\a_projects\no_complex_book\scripts\book_text_raw.json"
OUT_DIR     = r"C:\Users\User\a_projects\no_complex_book\chapters_nravites"

# ---------------------------------------------------------------------------
# Chapter definitions: (title, first_page, last_page, subtitle)
# ---------------------------------------------------------------------------
CHAPTERS = [
    ("Предисловие",
     1, 8,
     "Зачем была написана эта книга и как ею пользоваться"),
    ("Он вам не звонит",
     9, 20,
     "Если он не звонит — он о вас не думает"),
    ("Он не признаёт, что вы встречаетесь",
     21, 26,
     "Туман «мы просто общаемся» — сигнал тревоги"),
    ("Он изменяет или не хочет близости",
     27, 37,
     "Измене нет оправдания. Повторяем: измене нет оправдания"),
    ("Он видит вас только пьяным",
     38, 42,
     "Если трезвым он вам не звонит — вы ему не нужны"),
    ("Он не хочет на вас жениться",
     43, 49,
     "Хороший мужчина найдёт деньги, время и смелость"),
    ("Он хочет расстаться",
     50, 55,
     "Расставание — решение окончательное и не обсуждается"),
    ("Он просто исчез",
     56, 60,
     "Исчезновение — ответ. Достаточно ясный"),
    ("Он женат",
     61, 66,
     "Если он не целиком ваш — он целиком чей-то другой"),
    ("Он ведёт себя как эгоист или придурок",
     67, 76,
     "Положительные качества не отменяют плохое поведение"),
    ("Заключение: вы этого заслуживаете",
     77, 85,
     "Вы достойны мужчины, который без ума от вас"),
]

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

# Signal strength per chapter (1=mild, 5=critical)
_SIGNAL = {1:1, 2:4, 3:3, 4:5, 5:5, 6:3, 7:5, 8:5, 9:5, 10:4, 11:1}
for _k, _v in _SIGNAL.items():
    CHAPTER_STATS.setdefault(_k, {})['signal'] = _v

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

CHAPTER_VISUALS = {
    1: None,
    2: {
        'type': 'red_flags', 'title': 'Красные флаги',
        'items': [
            'Прошло больше 7 дней — он не позвонил',
            'Пишет только поздно ночью или в выходные',
            'Всегда «очень занят», но в соцсетях активен',
            'Предлагает встречу, но никогда не назначает конкретное время',
        ],
    },
    3: {
        'type': 'checklist', 'title': 'Признаки настоящих отношений',
        'items': [
            ('yes', 'Он называет вас своей девушкой'),
            ('yes', 'Знакомит с друзьями и семьёй'),
            ('yes', 'Строит с вами планы на будущее'),
            ('no',  '«Мы просто общаемся» или «не торопи события»'),
            ('no',  'Избегает слова «отношения»'),
        ],
    },
    4: {
        'type': 'truth_scale',
        'myth': ('«Он больше не повторит»', 'Раскаялся, это была ошибка, всё изменится'),
        'reality': ('Измена — это выбор', 'Паттерн не меняется без серьёзной работы над собой'),
    },
    5: {
        'type': 'timeline',
        'steps': [
            ('Пьяный звонок', 'Поздно ночью'),
            ('Трезвое молчание', 'Днём — тишина'),
            ('Снова пьяный', 'История повторяется'),
            ('Вывод', 'Трезвый — настоящий'),
        ],
    },
    6: {
        'type': 'red_flags', 'title': 'Признаки что он не женится',
        'items': [
            'Вместе больше 2 лет, тема брака «не поднималась»',
            'Говорит «когда-нибудь» или «не сейчас»',
            'Против официальных отношений, но живёт вместе',
            'При разговоре о браке — уходит от темы',
        ],
    },
    7: {
        'type': 'compare_grid',
        'excuse': ('«Он вернётся, если я постараюсь»', 'Надо дать ему время, он просто запутался'),
        'truth': ('Он уже принял решение', 'Расставание — не переговоры. Первое «нет» — окончательное'),
    },
    8: {
        'type': 'status_badge', 'icon': '👻',
        'label': 'ИСЧЕЗ = ОТВЕТИЛ',
        'sub': 'Самый трусливый ответ, но вполне однозначный',
    },
    9: {
        'type': 'status_badge', 'icon': '🔒',
        'label': 'ЖЕНАТ = НЕДОСТУПЕН',
        'sub': 'Не «немного», не «почти» — целиком принадлежит другой',
    },
    10: {
        'type': 'truth_scale',
        'myth': ('«Он хороший человек»', 'Добрый, умный — просто иногда ведёт себя плохо'),
        'reality': ('Поступки важнее потенциала', 'Хорошие качества не отменяют плохого поведения'),
    },
    11: {
        'type': 'checklist', 'title': 'Вы заслуживаете',
        'items': [
            ('yes', 'Мужчину, который без ума от вас'),
            ('yes', 'Отношения без гаданий и оправданий'),
            ('yes', 'Человека, который сам звонит и предлагает встречу'),
            ('no',  'Ждать, гадать, оправдывать'),
            ('no',  'Быть «удобной», а не любимой'),
        ],
    },
}


def build_visual_block(vis: dict) -> str:
    t = vis.get('type', '')
    if t == 'red_flags':
        items_html = ''.join(
            f'<div class="rf-item"><span class="rf-num">{i+1}</span>'
            f'<p>{escape_html(item)}</p></div>'
            for i, item in enumerate(vis.get('items', []))
        )
        return (f'<div class="red-flags">'
                f'<div class="rf-title">{escape_html(vis.get("title","Красные флаги"))}</div>'
                f'<div class="rf-list">{items_html}</div></div>')

    if t == 'checklist':
        items_html = ''.join(
            f'<div class="cl-item {kind}"><span>{"✓" if kind=="yes" else "✗"}</span>'
            f'<p>{escape_html(text)}</p></div>'
            for kind, text in vis.get('items', [])
        )
        return (f'<div class="checklist">'
                f'<div class="cl-title">{escape_html(vis.get("title",""))}</div>'
                f'{items_html}</div>')

    if t == 'timeline':
        steps = vis.get('steps', [])
        parts = []
        for i, (name, desc) in enumerate(steps):
            parts.append(
                f'<div class="tl-step"><div class="tl-dot"></div>'
                f'<strong>{escape_html(name)}</strong>'
                f'<p>{escape_html(desc)}</p></div>'
            )
            if i < len(steps) - 1:
                parts.append('<div class="tl-arrow">→</div>')
        return f'<div class="vis-timeline">{"".join(parts)}</div>'

    if t == 'status_badge':
        return (f'<div class="status-badge">'
                f'<div class="sb-icon">{vis.get("icon","")}</div>'
                f'<div class="sb-label">{escape_html(vis.get("label",""))}</div>'
                f'<div class="sb-sub">{escape_html(vis.get("sub",""))}</div>'
                f'</div>')

    if t == 'truth_scale':
        myth_title, myth_text = vis.get('myth', ('', ''))
        real_title, real_text = vis.get('reality', ('', ''))
        return (f'<div class="truth-scale">'
                f'<div class="ts-col myth"><div class="ts-head">Миф</div>'
                f'<strong>{escape_html(myth_title)}</strong><p>{escape_html(myth_text)}</p></div>'
                f'<div class="ts-col reality"><div class="ts-head">Реальность</div>'
                f'<strong>{escape_html(real_title)}</strong><p>{escape_html(real_text)}</p></div>'
                f'</div>')

    if t == 'compare_grid':
        exc_title, exc_text = vis.get('excuse', ('', ''))
        tru_title, tru_text = vis.get('truth', ('', ''))
        return (f'<div class="compare-grid">'
                f'<div class="cg-col excuse"><div class="cg-head">Оправдание</div>'
                f'<p><strong>{escape_html(exc_title)}</strong><br>{escape_html(exc_text)}</p></div>'
                f'<div class="cg-col truth"><div class="cg-head">Правда</div>'
                f'<p><strong>{escape_html(tru_title)}</strong><br>{escape_html(tru_text)}</p></div>'
                f'</div>')
    return ''


# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------
HEADER_RE = re.compile(
    r'^(Вы\s+просто|ВЫ\s+ПРОСТО|Вы\s+ПРОСТО|НЕ\s+ТАК\s+УЖ).{0,60}НРАВИТЕСЬ\s*',
    re.MULTILINE | re.IGNORECASE
)

def clean_text(raw: str) -> str:
    """Remove OCR artefacts and running headers from a page."""
    text = raw
    # Remove running book-title header
    text = re.sub(
        r'(?m)^(Вы\s+просто\s+ему\s+не\s+нравитесь|'
        r'Вы\s+ПРОСТО\s+ЕМУ\s+НЕ\s+НРАВИТЕСЬ|'
        r'ВЫ\s+просто\s+ЕМУ\s+не\s+НРАВИТЕСЬ|'
        r'Вы\s+ПЮСТО\s+ЕМУ\s+НЕ\s+НРАВИТЕСЬ|'
        r'Вы\s+пОсго\s+ЕМУ\s+НЕ\s+НРАВИТЕСЬ|'
        r'Вы\s+пюсто\s+ЕМУ\s+НЕ\s+НРАВИТЕСЬ)'
        r'\s*', '', text)
    # Remove bare page numbers (a line that is just digits)
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    # Join OCR soft hyphens at end of line: "нару-\nшать" -> "нарушать"
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def pages_text(pages: list, start: int, end: int) -> str:
    """Concatenate cleaned text for pages start..end (1-indexed)."""
    parts = []
    for p in pages:
        if start <= p['page'] <= end:
            parts.append(clean_text(p['text']))
    return '\n\n'.join(parts)


def escape_html(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def build_signal_meter(signal: int) -> str:
    bars = ''.join(
        f'<div class="bar filled" style="height:{int(30+14*i)}%"></div>'
        if i < signal else
        f'<div class="bar empty" style="height:{int(30+14*i)}%"></div>'
        for i in range(5)
    )
    return (
        f'<div class="signal-meter">'
        f'<div class="signal-label">Сигнал тревоги</div>'
        f'<div class="signal-bars">{bars}</div>'
        f'</div>'
    )


def build_insights_html(idx: int) -> list[str]:
    quotes = CHAPTER_INSIGHTS.get(idx, [])
    return [
        f'<blockquote class="insight"><p>{escape_html(q)}</p></blockquote>'
        for q in quotes
    ]


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


def _classify_para(para: str) -> str:
    """Return HTML for a single classified paragraph (no side-effects)."""
    # Excuse+letter merged: split first
    excuse_match = re.search(r'[Оо]правдание\s+типа', para)
    letter_match = re.search(r'[Дд]орого[йи]\s+[Гг]рег', para)
    if excuse_match and letter_match and excuse_match.start() < letter_match.start():
        head = para[:letter_match.start()].strip()
        tail = para[letter_match.start():].strip()
        return '\n'.join(filter(None, [
            _classify_para(head) if head else '',
            _classify_para(tail) if tail else '',
        ]))

    para_esc = escape_html(para)

    if re.search(r'ЧТО\s+ВЫ\s+ДОЛ', para, re.IGNORECASE):
        lines = [l.strip() for l in para.split('\n') if l.strip()]
        items = '<br>'.join(escape_html(l) for l in lines[1:])
        return (f'<div class="summary-box"><div class="summary-title">'
                f'Что вы должны были усвоить из этой главы</div>'
                f'<p>{items}</p></div>')

    if re.search(r'[Оо]правдание\s+типа', para):
        return f'<h3 class="excuse-title">{para_esc}</h3>'

    if re.search(r'[Дд]орого[йи]\s+[Гг]рег', para):
        return (f'<div class="letter-q"><div class="letter-label">Письмо Грегу</div>'
                f'<p>{para_esc}</p></div>')

    if re.search(r'[Ии]з\s+архивов\s+[Гг]рега|[Дд]орогая\s+.*[,!]', para):
        return (f'<div class="letter-a"><div class="letter-label">Грег отвечает</div>'
                f'<p>{para_esc}</p></div>')

    if re.search(r'ГРЕГ,\s+У\s+МЕНЯ\s+ПОЛУЧИЛОСЬ', para, re.IGNORECASE):
        body = '<br>'.join(escape_html(l) for l in para.split('\n'))
        return (f'<div class="success-story"><div class="success-label">'
                f'Грег, у меня получилось!</div><p>{body}</p></div>')

    if re.search(r'рабоч|тетрадь', para, re.IGNORECASE):
        return (f'<div class="workbook"><div class="workbook-label">Рабочая тетрадь</div>'
                f'<p>{para_esc}</p></div>')

    cleaned = para.replace('\n', ' ')
    if (20 < len(cleaned) < 160 and cleaned == cleaned.upper()
            and re.search(r'[А-ЯЁ]{4,}', cleaned)):
        return f'<h2 class="chapter-subhead">{escape_html(cleaned)}</h2>'

    # Normal paragraph — collapse if long
    para_single = re.sub(r'\s*\n\s*', ' ', para_esc)
    if len(para_single) > 500:
        preview = para_single[:130].rsplit(' ', 1)[0] + '…'
        return (f'<details class="long-para">'
                f'<summary>{preview}</summary>'
                f'<p>{para_single}</p></details>')
    return f'<p>{para_single}</p>'


def _is_qa_para(para: str) -> bool:
    """True if para is a Q&A structured element (excuse, letter, response, story, etc.)."""
    return bool(re.search(
        r'[Оо]правдание\s+типа|[Дд]орого[йи]\s+[Гг]рег|'
        r'[Ии]з\s+архивов\s+[Гг]рега|ГРЕГ,\s+У\s+МЕНЯ|'
        r'ЧТО\s+ВЫ\s+ДОЛ|рабоч|тетрадь',
        para, re.IGNORECASE
    ))


def structured_body_html(text: str, insights: list) -> str:
    """Build content-body HTML: collapsed intro + insights intercalated + Q&A section."""
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    expanded = []
    for para in paras:
        expanded.extend(split_long_para(para))

    # Split into intro (pure narrative) and qa sections
    intro, qa = [], []
    in_qa = False
    for para in expanded:
        if not in_qa and _is_qa_para(para):
            in_qa = True
        if in_qa:
            qa.append(para)
        else:
            intro.append(para)

    # Build intro block: first 2 shown, rest in <details>
    intro_html_parts = [_classify_para(p) for p in intro]
    if len(intro_html_parts) <= 3:
        intro_block = '\n'.join(intro_html_parts)
    else:
        visible = '\n'.join(intro_html_parts[:2])
        hidden = '\n'.join(intro_html_parts[2:])
        intro_block = (
            f'{visible}\n'
            f'<details class="more-text">'
            f'<summary>Читать вступление ▼</summary>'
            f'{hidden}'
            f'</details>'
        )

    # Build Q&A block
    qa_html_parts = [_classify_para(p) for p in qa]
    qa_block = '\n'.join(qa_html_parts)

    # Intercalate insights
    ins = insights or []
    ins0 = ins[0] if len(ins) > 0 else ''
    ins1 = ins[1] if len(ins) > 1 else ''

    return f'{intro_block}\n{ins0}\n{qa_block}\n{ins1}'


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

    # Chapter-specific visual block (dispatched by type)
    vis = CHAPTER_VISUALS.get(idx)
    if vis:
        parts.append(build_visual_block(vis))

    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Build one chapter HTML
# ---------------------------------------------------------------------------
def build_chapter_html(idx: int, title: str, subtitle: str, body_text: str) -> str:
    insights = build_insights_html(idx)
    body_html = structured_body_html(body_text, insights)
    infographic_html = build_infographic(idx)
    signal = CHAPTER_STATS.get(idx, {}).get('signal', 3)
    signal_html = build_signal_meter(signal)

    # Extract a key quote for the hero if possible
    quote = ""
    for para in body_text.split('\n\n'):
        s = para.strip()
        if 30 < len(s) < 200 and not re.search(r'[Дд]орог|рабоч|УСВОИТЬ', s):
            quote = s.split('\n')[0][:180]
            break

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{idx}. {title}</title>
<style>
/* Chapter-specific extras on top of shared theme */
.letter-q, .letter-a {{
  margin: 20px 0;
  padding: 18px 20px;
  border-radius: 14px;
  border-left: 4px solid var(--acc);
  background: rgba(114,216,255,.06);
}}
.letter-a {{
  border-left-color: var(--acc2);
  background: rgba(135,239,201,.06);
}}
.letter-label, .success-label, .workbook-label, .summary-title {{
  font-size: 11px; text-transform: uppercase; letter-spacing: .12em;
  font-weight: 700; margin-bottom: 10px;
}}
.letter-label      {{ color: var(--acc);  }}
.letter-a .letter-label {{ color: var(--acc2); }}
.success-label     {{ color: var(--warn); }}
.workbook-label    {{ color: var(--muted);}}
.summary-title     {{ color: var(--acc2); font-size: 13px; margin-bottom: 14px; }}
.success-story {{
  margin: 20px 0; padding: 18px 20px;
  border-radius: 14px; border: 1px solid var(--warn);
  background: rgba(255,209,138,.06);
}}
.workbook {{
  margin: 20px 0; padding: 16px 20px;
  border-radius: 14px; border: 1px dashed #3f66a6;
  background: rgba(15,31,56,.6);
}}
.summary-box {{
  margin: 28px 0; padding: 22px 24px;
  border-radius: 16px; border: 1px solid var(--acc2);
  background: rgba(135,239,201,.08);
}}
.excuse-title {{
  margin: 28px 0 12px;
  color: var(--warn);
  font-size: 1.1rem;
  border-left: 3px solid var(--warn);
  padding-left: 14px;
}}
.chapter-subhead {{
  font-size: 1.3rem;
  color: var(--acc);
  margin: 36px 0 18px;
  line-height: 1.25;
}}
.hero-quote {{
  margin-top: 16px;
  font-style: italic;
  color: var(--muted);
  font-size: .95rem;
  border-left: 3px solid var(--line);
  padding-left: 14px;
  line-height: 1.5;
}}
.callout {{
  display: flex; gap: 16px; align-items: flex-start;
  margin: 24px 0; padding: 18px 20px;
  border-radius: 14px; border: 1px solid var(--acc);
  background: rgba(114,216,255,.07);
}}
.callout-icon {{
  font-size: 1.4rem; font-weight: 900; color: var(--acc);
  line-height: 1; flex-shrink: 0; margin-top: 2px;
}}
.callout p {{ margin: 0; font-size: 1.05rem; line-height: 1.55; }}
.compare-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin: 24px 0;
}}
.cg-col {{
  padding: 18px 20px; border-radius: 14px;
}}
.cg-col.excuse {{
  border: 1px solid rgba(255,120,120,.35);
  background: rgba(255,80,80,.05);
}}
.cg-col.truth {{
  border: 1px solid rgba(135,239,201,.35);
  background: rgba(135,239,201,.05);
}}
.cg-head {{
  font-size: 11px; text-transform: uppercase; letter-spacing: .1em;
  font-weight: 700; margin-bottom: 10px;
}}
.cg-col.excuse .cg-head {{ color: #ff8080; }}
.cg-col.truth  .cg-head {{ color: var(--acc2); }}
.cg-col p {{ margin: 0; font-size: .95rem; line-height: 1.5; }}
@media (max-width: 600px) {{
  .compare-grid {{ grid-template-columns: 1fr; }}
}}
.content-body p {{ margin-bottom: 14px; line-height: 1.7; }}
.content-body h2 {{ margin-top: 36px; }}
.content-body h3 {{ margin-top: 24px; }}
/* Signal meter */
.signal-meter {{ margin: 20px 0 28px; display:flex; align-items:center; gap:16px; }}
.signal-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); }}
.signal-bars {{ display: flex; gap: 4px; align-items: flex-end; height: 28px; }}
.signal-bars .bar {{ width: 14px; border-radius: 3px 3px 0 0; }}
.signal-bars .bar.filled {{ background: #ff5c5c; }}
.signal-bars .bar.empty  {{ background: rgba(255,92,92,.18); }}
/* Insight pullquotes */
blockquote.insight {{
  margin: 24px 0; padding: 18px 22px;
  border-left: 4px solid var(--acc);
  background: rgba(114,216,255,.06);
  border-radius: 0 14px 14px 0;
}}
blockquote.insight p {{
  margin: 0; font-size: 1.1rem; font-style: italic;
  line-height: 1.65; color: var(--fg);
}}
/* Collapsibles */
details.more-text summary, details.long-para summary {{
  cursor: pointer; color: var(--acc); font-size: .88rem;
  padding: 6px 0; list-style: none; user-select: none;
  outline: none;
}}
details.more-text summary::marker,
details.long-para summary::marker {{ display: none; content: ''; }}
details.long-para {{
  margin-bottom: 14px;
  border-left: 2px solid var(--line);
  padding-left: 14px;
}}
details.long-para[open] summary {{ display: none; }}
/* Red flags */
.red-flags {{ margin: 24px 0; }}
.rf-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: #ff8080; font-weight: 700; margin-bottom: 12px; }}
.rf-list {{ display: grid; gap: 8px; }}
.rf-item {{ display: flex; gap: 12px; align-items: flex-start; padding: 12px 16px; border-radius: 10px; background: rgba(255,80,80,.06); border: 1px solid rgba(255,80,80,.2); }}
.rf-num {{ width: 24px; height: 24px; border-radius: 50%; background: #ff5c5c; color: #fff; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.rf-item p {{ margin: 0; font-size: .92rem; line-height: 1.5; color: #ffd0d0; }}
/* Checklist */
.checklist {{ margin: 24px 0; }}
.cl-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--acc2); font-weight: 700; margin-bottom: 12px; }}
.cl-item {{ display: flex; gap: 12px; align-items: flex-start; padding: 10px 14px; border-radius: 10px; margin-bottom: 6px; }}
.cl-item.yes {{ background: rgba(135,239,201,.07); border: 1px solid rgba(135,239,201,.25); }}
.cl-item.no  {{ background: rgba(255,80,80,.05); border: 1px solid rgba(255,80,80,.18); }}
.cl-item span {{ font-size: 1rem; font-weight: 800; flex-shrink: 0; width: 20px; }}
.cl-item.yes span {{ color: var(--acc2); }}
.cl-item.no  span {{ color: #ff8080; }}
.cl-item p {{ margin: 0; font-size: .92rem; line-height: 1.5; }}
/* Timeline */
.vis-timeline {{ display: flex; align-items: flex-start; gap: 0; margin: 24px 0; flex-wrap: wrap; }}
.tl-step {{ flex: 1; min-width: 110px; padding: 14px; text-align: center; background: rgba(114,216,255,.06); border: 1px solid var(--line); border-radius: 10px; }}
.tl-dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--acc); margin: 0 auto 8px; }}
.tl-step:last-child .tl-dot {{ background: var(--acc2); }}
.tl-step strong {{ display: block; font-size: .88rem; color: var(--fg,#eef5ff); margin-bottom: 4px; }}
.tl-step p {{ font-size: .82rem; color: var(--muted); margin: 0; line-height: 1.4; }}
.tl-arrow {{ display: flex; align-items: center; padding: 0 6px; color: var(--line); font-size: 1.2rem; margin-top: 10px; }}
/* Status badge */
.status-badge {{ margin: 24px 0; padding: 24px; text-align: center; border-radius: 16px; border: 1px solid var(--line); background: rgba(11,22,45,.6); }}
.sb-icon {{ font-size: 2.4rem; margin-bottom: 10px; }}
.sb-label {{ font-size: 1.3rem; font-weight: 800; letter-spacing: .06em; color: var(--acc); margin-bottom: 8px; }}
.sb-sub {{ font-size: .9rem; color: var(--muted); line-height: 1.5; }}
/* Truth scale */
.truth-scale {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }}
.ts-col {{ padding: 18px 20px; border-radius: 14px; position: relative; }}
.ts-col.myth {{ border: 1px solid rgba(255,120,120,.3); background: rgba(255,80,80,.04); }}
.ts-col.myth::after {{ content: '✗'; position: absolute; top: 12px; right: 14px; color: #ff8080; font-size: 1rem; font-weight: 800; }}
.ts-col.reality {{ border: 1px solid rgba(135,239,201,.3); background: rgba(135,239,201,.05); }}
.ts-col.reality::after {{ content: '✓'; position: absolute; top: 12px; right: 14px; color: var(--acc2); font-size: 1rem; font-weight: 800; }}
.ts-head {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; margin-bottom: 10px; }}
.ts-col.myth .ts-head {{ color: #ff8080; }}
.ts-col.reality .ts-head {{ color: var(--acc2); }}
.ts-col strong {{ display: block; font-size: .95rem; color: var(--fg,#eef5ff); margin-bottom: 8px; line-height: 1.4; }}
.ts-col p {{ margin: 0; font-size: .85rem; color: var(--muted); line-height: 1.5; }}
@media (max-width: 600px) {{ .truth-scale {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<main class="wrap">
  <section class="hero">
    <div class="kicker">«Вы просто ему не нравитесь» • Глава {idx}</div>
    <h1>{escape_html(title)}</h1>
    <p class="lead">{escape_html(subtitle)}</p>
    {f'<p class="hero-quote">{escape_html(quote)}</p>' if quote else ''}
  </section>

  {infographic_html}
  {signal_html}

  <div class="content-body">
{body_html}
  </div>
</main>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    with open(PAGES_JSON, encoding='utf-8') as f:
        pages = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)

    for idx, (title, p_start, p_end, subtitle) in enumerate(CHAPTERS, 1):
        text = pages_text(pages, p_start, p_end)
        html = build_chapter_html(idx, title, subtitle, text)
        out_path = os.path.join(OUT_DIR, f'chapter{idx}.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ch{idx} ({p_start}-{p_end}): {title} → {len(html):,} bytes")

    print(f"\nDone. {len(CHAPTERS)} chapters written to {OUT_DIR}")


if __name__ == '__main__':
    main()
