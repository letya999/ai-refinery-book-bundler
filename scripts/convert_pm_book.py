#!/usr/bin/env python3
"""
Converter: Управление ИТ-проектами по-простому (Селиховкин Иван, 2010)
PDF → structured chapter HTML files for html-book-bundler with enriched visuals.
"""

import fitz
import re
import os
import html as html_lib
from pathlib import Path

PDF_PATH  = "pm_book_ru.pdf"
OUT_DIR   = "chapters_pm_book"

CHAPTERS = [
    ("Введение. Об авторе",                                  5,  5),
    ("Глава I. О чём эта книга?",                            6,  7),
    ("Глава II. Предлагают должность — соглашаться?",        8, 10),
    ("Глава III. Как определиться с подходом?",             11, 14),
    ("Глава IV. Инициация проекта",                         15, 18),
    ("Глава V. Приступаем к планированию",                  19, 23),
    ("Глава VI. Планируем содержание",                      24, 30),
    ("Глава VII. Команда и подрядчики",                     31, 33),
    ("Глава VIII. Планируем время и стоимость",             34, 45),
    ("Глава IX. Ответственность, коммуникации, качество",   46, 50),
    ("Глава X. Планируем и работаем с рисками",             51, 57),
    ("Глава XI. Другие планы",                              58, 61),
    ("Глава XII. Выполнение и контроль работ",              62, 67),
    ("Глава XIII. Закрытие проекта",                        68, 70),
    ("Глава XIV. Что дальше? Рекомендованная литература",   71, 74),
]

# Visual definitions for chapters to enrich content
CHAPTER_VISUALS = {
    3: { # Глава II
        "type": "translator",
        "title": "Решение о вступлении в проект",
        "left_head": "РИСКИ",
        "left_items": ["Ответственность без власти", "Размытые цели", "Чужая команда"],
        "right_head": "ВОЗМОЖНОСТИ",
        "right_items": ["Новый опыт", "Влияние на продукт", "Профессиональный рост"]
    },
    5: { # Глава IV
        "type": "stats",
        "items": [
            ("ВХОД", "Бизнес-кейс / Идея"),
            ("ИНСТРУМЕНТ", "Устав проекта"),
            ("ВЫХОД", "Легитимный статус РМ")
        ]
    },
    9: { # Глава VIII
        "type": "timeline",
        "steps": [
            "Определение перечня работ (WBS)",
            "Оценка длительности и ресурсов",
            "Выявление зависимостей",
            "Построение критического пути",
            "Оптимизация и резервы"
        ]
    },
    11: { # Глава X
        "type": "grid",
        "cards": [
            ("ИДЕНТИФИКАЦИЯ", "Что может пойти не так?"),
            ("ОЦЕНКА", "Вероятность и влияние."),
            ("РЕАГИРОВАНИЕ", "План А и План Б.")
        ]
    }
}

RUNNING_HEADER_RE = re.compile(r'^Селиховкин\s+Иван.*$', re.IGNORECASE)
PAGE_NUMBER_RE    = re.compile(r'^\d{1,3}$')
SITE_RE           = re.compile(r'www\.pmlead\.ru', re.IGNORECASE)

def extract_page_blocks(doc: fitz.Document, page_num: int) -> list[dict]:
    page = doc[page_num - 1]
    raw = page.get_text("dict")
    blocks = []
    for b in raw.get("blocks", []):
        if b.get("type") != 0: continue
        lines_text = []
        max_size = 0
        is_bold = False
        for line in b.get("lines", []):
            line_parts = []
            for span in line.get("spans", []):
                t = span["text"]
                if not t.strip(): continue
                size = span["size"]
                flags = span["flags"]
                bold = bool(flags & (1 << 4))
                max_size = max(max_size, size)
                if bold: is_bold = True
                line_parts.append((t, bold, size))
            if line_parts: lines_text.append(line_parts)
        if not lines_text: continue
        plain = " ".join(part[0] for line in lines_text for part in line).strip()
        if (RUNNING_HEADER_RE.match(plain) or PAGE_NUMBER_RE.match(plain) or SITE_RE.match(plain)) and len(plain) < 100:
            continue
        blocks.append({"lines": lines_text, "plain": plain, "size": max_size, "bold": is_bold})
    return blocks

NUMBERED_ITEM_RE = re.compile(r'^(\d+)\.\s*(.+)', re.DOTALL)

def blocks_to_html(blocks: list[dict]) -> str:
    parts = []
    in_numbered_list = False
    for b in blocks:
        size, plain, lines = b["size"], b["plain"], b["lines"]
        if size >= 20: tag = "h1"
        elif size >= 14: tag = "h2"
        elif size >= 12.5 or (b["bold"] and size >= 11.5 and len(plain) < 120): tag = "h3"
        else: tag = "p"
        
        inline_parts = []
        for line in lines:
            for text, bold, _ in line:
                escaped = html_lib.escape(text)
                inline_parts.append(f"<b>{escaped}</b>" if bold and tag == "p" else escaped)
            inline_parts.append(" ")
        content = "".join(inline_parts).strip()
        if not content: continue

        num_match = NUMBERED_ITEM_RE.match(content) if tag == "p" else None
        if num_match:
            if not in_numbered_list: parts.append("<ol>"); in_numbered_list = True
            parts.append(f"<li>{html_lib.escape(num_match.group(2).strip())}</li>")
        else:
            if in_numbered_list: parts.append("</ol>"); in_numbered_list = False
            if tag == "h3" and len(plain) > 200:
                m = re.match(r'^(.{20,120}[.!?])\s+(.+)$', content, re.DOTALL)
                if m: parts.append(f"<h3>{m.group(1)}</h3>"); parts.append(f"<p>{m.group(2)}</p>")
                else: parts.append(f"<p>{content}</p>")
            else: parts.append(f"<{tag}>{content}</{tag}>")
    if in_numbered_list: parts.append("</ol>")
    return "\n".join(parts)

def get_visual_html(config: dict) -> str:
    vtype = config.get("type")
    if vtype == "stats":
        items = "".join([f'<div class="stat"><b class="stat-num">{label}</b><span class="stat-label">{val}</span></div>' for label, val in config["items"]])
        return f'<div class="stats">{items}</div>'
    if vtype == "translator":
        l_items = "".join([f"<li>{i}</li>" for i in config["left_items"]])
        r_items = "".join([f"<li>{i}</li>" for i in config["right_items"]])
        return f'<div class="translator"><div class="tr-col bad"><div class="tr-head bad">{config["left_head"]}</div><ul>{l_items}</ul></div><div class="tr-col good"><div class="tr-head good">{config["right_head"]}</div><ul>{r_items}</ul></div></div>'
    if vtype == "grid":
        cards = "".join([f'<div class="card"><b>{title}</b><p>{text}</p></div>' for title, text in config["cards"]])
        return f'<div class="grid">{cards}</div>'
    if vtype == "timeline":
        steps = "".join([f'<div class="tl-step"><div class="tl-num">{i+1}</div><div class="tl-content">{s}</div></div>' for i, s in enumerate(config["steps"])])
        return f'<div class="vis-timeline">{steps}</div>'
    return ""

def build_chapter_html(chapter_idx: int, title: str, body_html: str) -> str:
    kicker_match = re.match(r'^(Глава\s+[IVXa-zА-Яа-я]+\.?)', title)
    kicker = kicker_match.group(1) if kicker_match else "Введение"
    subtitle = title[len(kicker):].strip().lstrip('.').strip() or title
    
    css = """
body { margin: 0; padding: 0; font-family: system-ui, sans-serif; }
.hero { padding: 3rem 2rem 2.5rem; border-bottom: 2px solid var(--acc, #72d8ff); background: var(--panel, #0f1f38); }
.kicker { font-size: .75rem; font-weight: 700; text-transform: uppercase; color: var(--acc); margin-bottom: .6rem; }
.hero h1 { font-size: 2.4rem; font-weight: 800; color: var(--txt); margin: 0; }
.wrap { max-width: 860px; margin: 0 auto; padding: 2rem 1.5rem; }
blockquote.insight { border-left: 3px solid var(--acc); margin: 1.5rem 0; padding: .75rem 1.25rem; background: rgba(114,216,255,.07); font-style: italic; }
.vis-timeline { margin: 2rem 0; border-left: 2px solid var(--line); padding-left: 1.5rem; }
.tl-step { position: relative; margin-bottom: 1.5rem; }
.tl-num { position: absolute; left: -2.1rem; top: 0; width: 1.2rem; height: 1.2rem; background: var(--acc); color: #000; border-radius: 50%; font-size: 0.7rem; font-weight: 800; display: flex; align-items: center; justify-content: center; }
"""
    
    CHAPTER_INSIGHTS = {1: "Управление проектом — это не должность, это набор обязанностей.", 2: "Принять приглашение без понимания полномочий — согласиться на ответственность без влияния.", 3: "Методология — инструмент, а не цель. Нет «единственно верного» подхода.", 4: "Устав проекта легитимизирует ваши полномочия.", 5: "Планы читают, когда они отвечают на вопросы читателя.", 6: "Управление содержанием — это и управление тем, что НЕ входит в проект.", 7: "Незаменимый подрядчик — это не ресурс, а зависимость.", 8: "Расписание без оценки рисков — это оптимистический сценарий.", 9: "Матрица ответственности превращает слова в обязательства.", 10: "Риск, который вы не записали, станет неприятной неожиданностью.", 11: "Планы нужны, чтобы предотвратить уже случавшиеся когда-то проблемы.", 12: "Контроль — это обнаружение отклонений, пока есть варианты решений.", 13: "Проект не закрыт без извлеченных уроков.", 14: "PMP — это сигнал о профессиональном отношении к делу.", 15: "Лучшая книга — та, которую откроете в момент реальной проблемы."}
    
    insight = CHAPTER_INSIGHTS.get(chapter_idx + 1, "")
    insight_html = f'\n<blockquote class="insight"><p>{html_lib.escape(insight)}</p></blockquote>\n' if insight else ""
    
    visual_html = ""
    if (chapter_idx + 1) in CHAPTER_VISUALS:
        visual_html = get_visual_html(CHAPTER_VISUALS[chapter_idx + 1])

    # Inject visual after the first few paragraphs
    if visual_html:
        paras = body_html.split('</p>')
        if len(paras) > 2:
            paras.insert(2, f'\n{visual_html}\n')
            body_html = '</p>'.join(paras)
        else:
            body_html = visual_html + body_html

    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>{html_lib.escape(title)}</title><style>{css}</style></head>
<body>
<div class="hero"><p class="kicker">{html_lib.escape(kicker)}</p><h1>{html_lib.escape(subtitle)}</h1></div>
{insight_html}
<div class="wrap">{body_html}</div>
</body></html>"""

def main():
    doc = fitz.open(PDF_PATH)
    out_path = Path(OUT_DIR)
    out_path.mkdir(exist_ok=True)
    for i, (title, first_page, last_page) in enumerate(CHAPTERS):
        all_blocks = []
        for p in range(first_page, last_page + 1):
            if p <= len(doc): all_blocks.extend(extract_page_blocks(doc, p))
        body_html = blocks_to_html(all_blocks)
        chapter_html = build_chapter_html(i, title, body_html)
        (out_path / f"chapter{i+1}.html").write_text(chapter_html, encoding="utf-8")
    print(f"\nDone. {len(CHAPTERS)} chapters written to {OUT_DIR}/")

if __name__ == "__main__": main()
