#!/usr/bin/env python3
import argparse
import base64
import json
import pathlib
import re
import sys

class BookLinter:
    def __init__(self, file_path: str, max_size_mb: float = 30.0):
        self.file_path = pathlib.Path(file_path)
        self.max_size_mb = max_size_mb
        self.errors = []
        self.warnings = []
        self.stats = {}

    def run(self):
        if not self.file_path.exists():
            self.errors.append(f"Файл не найден: {self.file_path}")
            return False

        content = self.file_path.read_text(encoding="utf-8", errors="replace")
        self.stats['size_mb'] = self.file_path.stat().st_size / (1024 * 1024)

        if self.stats['size_mb'] > self.max_size_mb:
            self.warnings.append(f"Размер файла ({self.stats['size_mb']:.1f} MB) превышает норму.")

        if "Content-Security-Policy" not in content:
            self.errors.append("Оболочка: Отсутствует CSP мета-тег!")
        
        if "sandbox" not in content.lower():
            self.errors.append("Оболочка: <iframe> не имеет атрибута 'sandbox'!")

        ext_refs = re.findall(r'(src|href|url)\s*=\s*[\'"](http[s]?://[^\'"]+)[\'"]', content, re.I)
        for _, url in ext_refs:
            self.errors.append(f"Оболочка: Найдена внешняя ссылка (не бандлится): {url}")

        b64_match = re.search(r'const\s+LOCAL_B64\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not b64_match:
            self.errors.append("Данные: Не найден массив LOCAL_B64_CHAPTERS.")
            return False

        try:
            chapters = json.loads(b64_match.group(1))
            self.stats['chapters'] = len(chapters)
            for i, b64_str in enumerate(chapters):
                html = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                self._audit_chapter(i + 1, html)
        except Exception as e:
            self.errors.append(f"Данные: Ошибка парсинга глав ({e})")

        return len(self.errors) == 0

    def _audit_chapter(self, idx: int, html: str):
        p = f"Глава {idx}"
        
        unsafe_js = re.search(r'(window|top|parent|opener)\s*(\.|\[|\]|\s+)+(\.|\s+)*(parent|top|opener|location|cookie)', html, re.I)
        if unsafe_js and "postMessage" not in html:
             self.errors.append(f"{p}: Подозрительный JS (попытка побега из песочницы): {unsafe_js.group(0)}")

        links = re.findall(r'(src|href|srcset)\s*=\s*[\'"]([^\'"]+)[\'"]', html, re.I)
        for _, url in links:
            if url.startswith('http'):
                self.errors.append(f"{p}: Внешняя ссылка (должна быть внутри): {url}")
            elif not (url.startswith('data:') or url.startswith('#') or url.startswith('blob:')):
                if url.endswith('.html') or '.html#' in url: continue
                self.errors.append(f"{p}: Непривязанный локальный путь: {url}")

    def report(self):
        print(f"\n{'='*60}\nАУДИТ КНИГИ: {self.file_path.name}\n{'='*60}")
        print(f"Размер: {self.stats.get('size_mb',0):.2f} MB | Глав в томе: {self.stats.get('chapters',0)}")
        
        for e in self.errors: print(f"  [X] ОШИБКА: {e}")
        for w in self.warnings: print(f"  [!] ПРЕДУПРЕЖДЕНИЕ: {w}")
        
        if not self.errors:
            print("\nСТАТУС: PASS - 100% Оффлайн и Безопасно.")
        else:
            print("\nСТАТУС: FAIL - Найдены критические уязвимости.")
        print("="*60 + "\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--max-size", type=float, default=30.0)
    args = p.parse_args()
    linter = BookLinter(args.file, args.max_size)
    sys.exit(0 if linter.run() and not linter.report() else 1)
