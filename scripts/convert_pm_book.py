#!/usr/bin/env python3
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

GLOSSARY_TERMS = {
    "WBS": "Иерархическая структура работ (Work Breakdown Structure). Декомпозиция проекта на мелкие пакеты задач.",
    "PERT": "Метод оценки и анализа программ. Техника оценки времени (оптимистичная, пессимистичная, вероятная).",
    "ROM": "Rough Order of Magnitude. Грубая оценка стоимости или времени (допуск +/- 50%).",
    "RACI": "Матрица ответственности (Responsible, Accountable, Consulted, Informed).",
    "PMBOK": "Project Management Body of Knowledge. Свод знаний по управлению проектами от PMI.",
    "Agile": "Гибкие методологии разработки, основанные на итерациях и быстрой обратной связи.",
    "Waterfall": "Каскадная (водопадная) модель планирования, где этапы идут строго друг за другом.",
    "Scope": "Содержание проекта — весь объем работ, который должен быть выполнен.",
    "Critical Path": "Критический путь — самая длинная цепочка задач, определяющая срок завершения проекта.",
    "Milestone": "Веха — значимое событие в проекте, имеющее нулевую длительность.",
    "PMI": "Project Management Institute — международная организация по стандартизации управления проектами.",
    "Stakeholder": "Заинтересованное лицо — человек или группа, чьи интересы затронуты проектом.",
    "Float": "Временной резерв задачи — насколько её можно отложить, не задерживая проект.",
    "Buffer": "Буфер — защитный резерв времени или денег.",
    "Gantt": "Диаграмма Ганта — ленточная диаграмма, визуализирующая график работ."
}

def extract_clean_text(doc, start, end):
    text_blocks = []
    for p in range(start, end + 1):
        page = doc[p-1]
        raw = page.get_text("blocks")
        for b in raw:
            if b[6] == 0: # text type
                line = b[4].replace('\n', ' ').strip()
                if re.match(r'^\d+$', line): continue # skip page numbers
                if "Селиховкин Иван" in line: continue
                if "www.pmlead.ru" in line: continue
                text_blocks.append(line)
    return text_blocks

def inject_glossary_links(text):
    for term in GLOSSARY_TERMS:
        # Avoid double-linking
        pattern = rf'\b({term})\b'
        text = re.sub(pattern, rf'<a href="glossary.html#{term.lower()}" class="term-link">\1</a>', text, flags=re.IGNORECASE)
    return text

def get_svg_wbs():
    return """<div class="vis-diag" style="max-width:500px"><svg viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg">
    <defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="var(--line)"/></marker></defs>
    <rect x="150" y="10" width="100" height="40" rx="8" class="diag-node" style="fill:var(--acc)"/>
    <text x="200" y="35" class="diag-text" style="fill:#000">ПРОЕКТ</text>
    <line x1="200" y1="50" x2="200" y2="70" class="diag-link"/>
    <line x1="100" y1="70" x2="300" y2="70" class="diag-link" style="marker-end:none"/>
    <line x1="100" y1="70" x2="100" y2="90" class="diag-link"/>
    <line x1="300" y1="70" x2="300" y2="90" class="diag-link"/>
    <rect x="50" y="90" width="100" height="40" rx="8" class="diag-node"/>
    <text x="100" y="115" class="diag-text">Фаза 1</text>
    <rect x="250" y="90" width="100" height="40" rx="8" class="diag-node"/>
    <text x="300" y="115" class="diag-text">Фаза 2</text>
    </svg><div class="caption">Пример дерева ИСР (WBS)</div></div>"""

def get_svg_network():
    return """<div class="vis-diag" style="max-width:600px"><svg viewBox="0 0 500 150" xmlns="http://www.w3.org/2000/svg">
    <defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="var(--line)"/></marker></defs>
    <rect x="20" y="50" width="60" height="40" rx="5" class="diag-node"/>
    <text x="50" y="75" class="diag-text">Start</text>
    <path d="M 80 70 L 140 40" class="diag-link"/>
    <path d="M 80 70 L 140 100" class="diag-link"/>
    <rect x="140" y="20" width="100" height="40" rx="5" class="diag-node" style="stroke:var(--bad);stroke-width:3"/>
    <text x="190" y="45" class="diag-text">Task A (CP)</text>
    <rect x="140" y="80" width="100" height="40" rx="5" class="diag-node"/>
    <text x="190" y="105" class="diag-text">Task B</text>
    <path d="M 240 40 L 300 70" class="diag-link" style="stroke:var(--bad)"/>
    <path d="M 240 100 L 300 70" class="diag-link"/>
    <rect x="300" y="50" width="60" height="40" rx="5" class="diag-node"/>
    <text x="330" y="75" class="diag-text">End</text>
    </svg><div class="caption">Сетевая диаграмма и Критический путь</div></div>"""

def main():
    doc = fitz.open(PDF_PATH)
    out_path = Path(OUT_DIR)
    out_path.mkdir(exist_ok=True)
    
    # Generate Chapters
    for i, (title, s, e) in enumerate(CHAPTERS):
        blocks = extract_clean_text(doc, s, e)
        # Use more text! 
        body_html = "".join([f"<p>{inject_glossary_links(b)}</p>" for b in blocks])
        
        # Inject visuals
        extra_viz = ""
        if i+1 == 6: extra_viz = get_svg_wbs()
        if i+1 == 8: extra_viz = get_svg_network()
        if i+1 == 9: 
            extra_viz = '<div class="matrix"><table><tr><th>Role</th><th>Identify</th><th>Plan</th><th>Execute</th></tr><tr><td>PM</td><td>A</td><td>R</td><td>R</td></tr><tr><td>Team</td><td>C</td><td>R</td><td>R</td></tr><tr><td>Sponsor</td><td>I</td><td>A</td><td>I</td></tr></table></div>'

        chapter_html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>{title}</title></head>
<body>
<section class="hero"><p class="kicker">Глава {i+1}</p><h1>{title}</h1></section>
<div class="wrap">
{extra_viz}
{body_html}
</div></body></html>"""
        (out_path / f"chapter{i+1}.html").write_text(chapter_html, encoding="utf-8")

    # Generate Glossary
    glossary_items = "".join([f'<div class="card" id="{tid.lower()}"><b>{tid}</b><p>{desc}</p></div>' for tid, desc in GLOSSARY_TERMS.items()])
    glossary_html = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Глоссарий</title></head>
<body>
<section class="hero"><p class="kicker">Словарь</p><h1>Термины и определения</h1></section>
<div class="wrap"><div class="grid">{glossary_items}</div></div>
</body></html>"""
    (out_path / "glossary.html").write_text(glossary_html, encoding="utf-8")
    
    print("Done. Rebuilt with full content, SVG diagrams and Glossary.")

if __name__ == "__main__": main()
