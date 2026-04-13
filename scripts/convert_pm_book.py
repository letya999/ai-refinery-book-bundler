#!/usr/bin/env python3
"""
Converter: Управление ИТ-проектами по-простому (Селиховкин Иван, 2010)
PDF → structured chapter HTML files for html-book-bundler

Usage:
  python scripts/convert_pm_book.py

Output: chapters_pm_book/chapter1.html ... chapter15.html
"""

import fitz
import re
import os
import html as html_lib
from pathlib import Path

PDF_PATH  = "pm_book_ru.pdf"
OUT_DIR   = "chapters_pm_book"

# TOC-based chapter map: (title, first_page, last_page)  — 1-indexed PDF pages
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

# Running header/footer patterns to strip
RUNNING_HEADER_RE = re.compile(r'^Селиховкин\s+Иван.*$', re.IGNORECASE)
PAGE_NUMBER_RE    = re.compile(r'^\d{1,3}$')
SITE_RE           = re.compile(r'www\.pmlead\.ru', re.IGNORECASE)


def extract_page_blocks(doc: fitz.Document, page_num: int) -> list[dict]:
    """Extract text blocks with font size/bold info from a page."""
    page = doc[page_num - 1]  # 0-indexed
    raw = page.get_text("dict")
    blocks = []

    for b in raw.get("blocks", []):
        if b.get("type") != 0:  # skip images
            continue
        lines_text = []
        max_size = 0
        is_bold = False

        for line in b.get("lines", []):
            line_parts = []
            for span in line.get("spans", []):
                t = span["text"]
                if not t.strip():
                    continue
                size = span["size"]
                flags = span["flags"]
                bold = bool(flags & (1 << 4))
                max_size = max(max_size, size)
                if bold:
                    is_bold = True
                line_parts.append((t, bold, size))
            if line_parts:
                lines_text.append(line_parts)

        if not lines_text:
            continue

        # Flatten to plain text for running-header detection
        plain = " ".join(part[0] for line in lines_text for part in line).strip()
        
        # IMPROVED: Only ignore if the block IS ONLY a header/footer/page number
        is_header = RUNNING_HEADER_RE.match(plain)
        is_page_num = PAGE_NUMBER_RE.match(plain)
        is_site = SITE_RE.match(plain)
        
        if is_header or is_page_num or is_site:
            # Check if there is other content in the block (shouldn't be, but just in case)
            if len(plain) < 100: 
                continue

        blocks.append({
            "lines": lines_text,
            "plain": plain,
            "size":  max_size,
            "bold":  is_bold,
        })

    return blocks


NUMBERED_ITEM_RE = re.compile(r'^(\d+)\.\s*(.+)', re.DOTALL)

def blocks_to_html(blocks: list[dict]) -> str:
    """Convert extracted blocks to structured HTML paragraphs/headings."""
    parts = []
    i = 0
    in_numbered_list = False

    while i < len(blocks):
        b = blocks[i]
        size = b["size"]
        plain = b["plain"]
        lines = b["lines"]

        # Determine heading level by font size
        if size >= 20:
            tag = "h1"
        elif size >= 14:
            tag = "h2"
        elif size >= 12.5 or (b["bold"] and size >= 11.5 and len(plain) < 120):
            tag = "h3"
        else:
            tag = "p"

        # Build rich inline HTML preserving bold spans
        inline_parts = []
        for line in lines:
            for text, bold, _ in line:
                escaped = html_lib.escape(text)
                if bold and tag == "p":
                    inline_parts.append(f"<b>{escaped}</b>")
                else:
                    inline_parts.append(escaped)
            inline_parts.append(" ")

        content = "".join(inline_parts).strip()
        if not content:
            i += 1
            continue

        # Detect numbered list items: "1.Text" or "1. Text"
        num_match = NUMBERED_ITEM_RE.match(content) if tag == "p" else None
        if num_match:
            if not in_numbered_list:
                parts.append("<ol>")
                in_numbered_list = True
            parts.append(f"<li>{html_lib.escape(num_match.group(2).strip())}</li>")
        else:
            if in_numbered_list:
                parts.append("</ol>")
                in_numbered_list = False

            # Split h3 block that accidentally merged heading + first sentence
            # (block > 200 chars classified as h3 is likely a mis-detection)
            if tag == "h3" and len(plain) > 200:
                # Take only up to first sentence end as heading
                m = re.match(r'^(.{20,120}[.!?])\s+(.+)$', content, re.DOTALL)
                if m:
                    parts.append(f"<h3>{m.group(1)}</h3>")
                    parts.append(f"<p>{m.group(2)}</p>")
                else:
                    parts.append(f"<p>{content}</p>")
            else:
                parts.append(f"<{tag}>{content}</{tag}>")

        i += 1

    if in_numbered_list:
        parts.append("</ol>")

    return "\n".join(parts)


def detect_step_list(html_content: str) -> str:
    """
    Detect numbered step patterns like "Шаг первый/первый:" or "Шаг 1."
    and wrap them in a styled steps section.
    """
    # Replace step headings with a class
    html_content = re.sub(
        r'<h3>(Шаг [^<]{1,60})</h3>',
        r'<h3 class="step-head">\1</h3>',
        html_content
    )
    return html_content


def detect_checklist(html_content: str) -> str:
    """
    Detect sequences of short bold items that look like a checklist or key points list.
    """
    return html_content


def build_chapter_html(chapter_idx: int, title: str, body_html: str) -> str:
    """Wrap body HTML in a full chapter HTML document."""

    # Extract a short kicker from chapter number
    kicker_match = re.match(r'^(Глава\s+[IVXa-zА-Яа-я]+\.?)', title)
    kicker = kicker_match.group(1) if kicker_match else "Введение"
    subtitle = title[len(kicker):].strip().lstrip('.')  .strip() or title

    # Minimal styles for chapter rendering - the rest comes from theme.css via bundler
    css = """
body { margin: 0; padding: 0; font-family: system-ui, sans-serif; }
.hero { padding: 3rem 2rem 2.5rem; border-bottom: 2px solid var(--acc, #72d8ff); background: var(--panel, #0f1f38); }
.kicker { font-size: .75rem; font-weight: 700; text-transform: uppercase; color: var(--acc); margin-bottom: .6rem; }
.hero h1 { font-size: 2.4rem; font-weight: 800; color: var(--txt); margin: 0; }
.wrap { max-width: 860px; margin: 0 auto; padding: 2rem 1.5rem; }
blockquote.insight { border-left: 3px solid var(--acc); margin: 1.5rem 0; padding: .75rem 1.25rem; background: rgba(114,216,255,.07); font-style: italic; }
"""

    # AI-curated insights: one key takeaway per chapter, placed after hero
    CHAPTER_INSIGHTS = {
        1:  "Управление проектом — это не должность, это набор обязанностей, которые кто-то должен взять на себя.",
        2:  "Принять приглашение на роль менеджера проекта без понимания своих полномочий — значит согласиться на ответственность без возможности на неё влиять.",
        3:  "Методология — это инструмент, а не цель. Нет «единственно верного» подхода; есть подход, который подходит вашей организации прямо сейчас.",
        4:  "Устав проекта — единственный документ, который легитимизирует ваши полномочия. Без него вы управляете проектом на чужой территории.",
        5:  "Планы не читают, когда они написаны для галочки. Планы читают, когда они отвечают на вопросы, которые волнуют читателя.",
        6:  "Управление содержанием — это управление тем, что НЕ входит в проект, не меньше, чем тем, что входит.",
        7:  "Подрядчик, которого вы не можете заменить, — это не ресурс, а зависимость.",
        8:  "Расписание без оценки рисков — это оптимистический сценарий, а не план.",
        9:  "Матрица ответственности превращает устные договорённости в письменные обязательства. Разница между ними — это разница между намерением и результатом.",
        10: "Риск, который вы не записали, не перестаёт существовать — он просто становится неожиданностью.",
        11: "Каждый «другой план» существует потому, что кто-то когда-то столкнулся с проблемой, которую этот план должен был предотвратить.",
        12: "Контроль — это не надзор. Контроль — это своевременное обнаружение отклонений и принятие решений, пока у вас ещё есть варианты.",
        13: "Проект не закрыт, пока не задокументированы уроки. Иначе следующий менеджер снова изобретёт те же грабли.",
        14: "PMP — это не диплом об образовании. Это сигнал рынку о том, что вы воспринимаете управление проектами как профессию.",
        15: "Лучшая рекомендованная литература — та, которую вы откроете снова, когда столкнётесь с реальной проблемой.",
    }

    insight = CHAPTER_INSIGHTS.get(chapter_idx + 1, "")
    insight_html = ""
    if insight:
        insight_html = f'\n<blockquote class="insight"><p>{html_lib.escape(insight)}</p></blockquote>\n'

    hero_html = f"""<div class="hero">
  <p class="kicker">{html_lib.escape(kicker)}</p>
  <h1>{html_lib.escape(subtitle)}</h1>
</div>
{insight_html}"""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{html_lib.escape(title)}</title>
<style>{css}</style>
</head>
<body>
{hero_html}
<div class="wrap">
{body_html}
</div>
</body>
</html>"""


BULLET_RE = re.compile(r'<p>[-–•▪]\s+([^<]+)</p>')

def post_process(html_content: str, chapter_idx: int, title: str) -> str:
    """Apply chapter-specific post-processing and add semantic visuals."""

    # Convert <p>- Text</p> bullet lines into <ul><li> lists
    # Find runs of consecutive bullet <p> tags and wrap in <ul>
    def replace_bullet_run(m):
        items = BULLET_RE.findall(m.group(0))
        return "<ul>\n" + "\n".join(f"<li>{item.strip()}</li>" for item in items) + "\n</ul>"

    # Replace consecutive bullet paragraphs as a group
    html_content = re.sub(
        r'(?:<p>[-–•▪]\s+[^<]+</p>\s*)+',
        replace_bullet_run,
        html_content
    )

    # Chapter-specific enhancements
    chapter_num = chapter_idx + 1  # 1-based

    if chapter_num == 9:  # Глава VIII: Планируем время и стоимость (steps 1-7)
        html_content = detect_step_list(html_content)

    return html_content


def main():
    doc = fitz.open(PDF_PATH)
    out_path = Path(OUT_DIR)
    out_path.mkdir(exist_ok=True)

    for i, (title, first_page, last_page) in enumerate(CHAPTERS):
        print(f"Processing chapter {i+1}: {title} (pages {first_page}-{last_page})")

        all_blocks = []
        for page_num in range(first_page, last_page + 1):
            if page_num <= len(doc):
                blocks = extract_page_blocks(doc, page_num)
                all_blocks.extend(blocks)

        if not all_blocks:
            print(f"  WARNING: no text extracted for chapter {i+1}")
            continue

        body_html = blocks_to_html(all_blocks)
        body_html = post_process(body_html, i, title)

        chapter_html = build_chapter_html(i, title, body_html)

        out_file = out_path / f"chapter{i+1}.html"
        out_file.write_text(chapter_html, encoding="utf-8")
        print(f"  -> {out_file} ({len(chapter_html)} chars)")

    print(f"\nDone. {len(CHAPTERS)} chapters written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
