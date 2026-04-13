#!/usr/bin/env python3
"""
Universal Book Ingester for HTML Book Bundler v3.0
Supports: FB2, EPUB
Converts books to standard HTML chapters in a target directory.
Zero external dependencies (uses standard library).
"""
import argparse
import zipfile
import tempfile
import shutil
import os
import base64
import xml.etree.ElementTree as ET
from pathlib import Path

def strip_ns(tag):
    return tag.split('}')[-1]

def ingest_fb2(input_path, out_dir):
    print(f"📚 Разбор FB2: {input_path}")
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Извлечение картинок
    binaries = {}
    for binary in root.findall('.//{*}binary'):
        b_id = binary.attrib.get('id')
        if b_id and binary.text:
            out_file = assets_dir / b_id
            try:
                out_file.write_bytes(base64.b64decode(binary.text))
                binaries[b_id] = f"assets/{b_id}"
            except Exception as e:
                print(f"  [Ошибка] Не удалось декодировать {b_id}: {e}")

    # Извлечение глав
    body = root.find('.//{*}body')
    if body is None:
        print("  [Ошибка] Не найден <body> в FB2.")
        return

    chapter_idx = 1
    for section in body.findall('./{*}section'):
        title_el = section.find('./{*}title')
        title_text = f"Глава {chapter_idx}"
        if title_el is not None:
            title_text = "".join(title_el.itertext()).strip()
            
        html = [f"<!DOCTYPE html>\n<html>\n<head>\n<meta charset='utf-8'>\n<title>{title_text}</title>\n</head>\n<body>"]
        if title_el is not None:
            html.append(f"<h1>{title_text}</h1>")
            
        for child in section:
            tag = strip_ns(child.tag)
            if tag == 'title': continue
            if tag == 'p':
                text = "".join(child.itertext()).strip()
                if text: html.append(f"<p>{text}</p>")
            elif tag == 'image':
                href = child.attrib.get('{http://www.w3.org/1999/xlink}href', '')
                if href.startswith('#') and href[1:] in binaries:
                    html.append(f'<img src="{binaries[href[1:]]}">')
            elif tag == 'subtitle':
                text = "".join(child.itertext()).strip()
                html.append(f"<h3>{text}</h3>")
            elif tag == 'empty-line':
                html.append("<br>")
                
        html.append("</body>\n</html>")
        out_file = out_dir / f"{chapter_idx:03d}.html"
        out_file.write_text("\n".join(html), encoding='utf-8')
        chapter_idx += 1
        
    print(f"✅ Успешно извлечено глав: {chapter_idx-1}")

def ingest_epub(input_path, out_dir):
    print(f"📚 Разбор EPUB: {input_path}")
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(input_path, 'r') as z:
        # Находим .opf
        try:
            container = z.read('META-INF/container.xml')
            root = ET.fromstring(container)
            opf_path = root.find('.//{*}rootfile').attrib['full-path']
            base_path = os.path.dirname(opf_path)
        except Exception:
            print("  [Ошибка] Некорректный EPUB (не найден container.xml или OPF)")
            return
            
        opf_tree = ET.fromstring(z.read(opf_path))
        manifest = {}
        for item in opf_tree.findall('.//{*}item'):
            manifest[item.attrib['id']] = item.attrib['href']
            
        spine = [item.attrib['idref'] for item in opf_tree.findall('.//{*}itemref')]
        
        # Извлекаем все медиафайлы
        for m_id, m_href in manifest.items():
            if m_href.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.css')):
                try:
                    full_path = f"{base_path}/{m_href}" if base_path else m_href
                    data = z.read(full_path)
                    # Выравниваем структуру папок
                    safe_name = m_href.replace('/', '_')
                    (assets_dir / safe_name).write_bytes(data)
                except Exception:
                    pass

        # Обрабатываем главы
        chapter_idx = 1
        for s_id in spine:
            if s_id not in manifest: continue
            m_href = manifest[s_id]
            full_path = f"{base_path}/{m_href}" if base_path else m_href
            try:
                html_data = z.read(full_path).decode('utf-8', errors='ignore')
                # Простая чистка путей для ассетов
                html_data = html_data.replace('src="../images/', 'src="assets/images_')
                html_data = html_data.replace('src="images/', 'src="assets/images_')
                html_data = html_data.replace('href="../css/', 'href="assets/css_')
                html_data = html_data.replace('href="css/', 'href="assets/css_')
                
                out_file = out_dir / f"{chapter_idx:03d}.html"
                out_file.write_text(html_data, encoding='utf-8')
                chapter_idx += 1
            except Exception as e:
                print(f"  [Предупреждение] Пропуск главы {m_href}: {e}")
                
    print(f"✅ Успешно извлечено глав: {chapter_idx-1}")

def main():
    p = argparse.ArgumentParser(description="Ingest e-books into HTML chapters.")
    p.add_argument("--input", required=True, help="Path to .fb2 or .epub file")
    p.add_argument("--output", required=True, help="Output directory (e.g. ./chapters)")
    args = p.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.output)
    
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    if in_path.suffix.lower() == '.fb2':
        ingest_fb2(in_path, out_dir)
    elif in_path.suffix.lower() == '.epub':
        ingest_epub(in_path, out_dir)
    else:
        print("❌ Формат не поддерживается. Только .fb2 или .epub")

if __name__ == "__main__":
    main()
