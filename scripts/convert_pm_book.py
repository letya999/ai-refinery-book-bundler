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

RUNNING_HEADER_RE = re.compile(r'^Селиховкин\s+Иван.*$', re.IGNORECASE)
PAGE_NUMBER_RE    = re.compile(r'^\d{1,3}$')
SITE_RE           = re.compile(r'www\.pmlead\.ru', re.IGNORECASE)

def extract_page_text(doc: fitz.Document, page_num: int) -> str:
    page = doc[page_num - 1]
    text = page.get_text("text")
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if RUNNING_HEADER_RE.match(line) or PAGE_NUMBER_RE.match(line) or SITE_RE.match(line):
            continue
        lines.append(line)
    return " ".join(lines)

def main():
    doc = fitz.open(PDF_PATH)
    out_path = Path(OUT_DIR)
    out_path.mkdir(exist_ok=True)
    for i, (title, first_page, last_page) in enumerate(CHAPTERS):
        all_text = []
        for p in range(first_page, last_page + 1):
            if p <= len(doc): 
                all_text.append(extract_page_text(doc, p))
        
        # Simple HTML wrapper for the semantic processor to read
        raw_body = "\n\n".join(all_text)
        chapter_html = f"<html><head><title>{title}</title></head><body>{raw_body}</body></html>"
        (out_path / f"chapter{i+1}.html").write_text(chapter_html, encoding="utf-8")
    print(f"Extracted {len(CHAPTERS)} raw chapters.")

if __name__ == "__main__": main()
