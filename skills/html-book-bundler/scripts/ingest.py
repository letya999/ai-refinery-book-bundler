#!/usr/bin/env python3
"""
Universal Book Ingester for HTML Book Bundler v8.3
Supports: FB2, EPUB, FB2.ZIP
Outputs chapter1.html, chapter2.html, ... (compatible with bundle.cjs navScript)
Zero stdlib-only dependencies for FB2/EPUB (python-docx needed for DOCX).
"""
import argparse
import base64
import os
import posixpath
import re
import shutil
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Try to import PDFParser for PDF support
try:
    from pdf_parser_general import PDFParser
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


def strip_ns(tag: str) -> str:
    return tag.split('}')[-1]


def escape_html(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def el_to_html(el) -> str:
    """Recursively convert FB2 element to HTML, preserving inline markup."""
    tag = strip_ns(el.tag)
    text = el.text or ''
    children_html = ''.join(el_to_html(c) for c in el)
    tail = el.tail or ''

    etail = escape_html(tail)
    if tag == 'strong':    return f'<b>{escape_html(text)}{children_html}</b>{etail}'
    if tag == 'emphasis':  return f'<em>{escape_html(text)}{children_html}</em>{etail}'
    if tag == 'strikethrough': return f'<s>{escape_html(text)}{children_html}</s>{etail}'
    if tag == 'code':      return f'<code>{escape_html(text)}{children_html}</code>{etail}'
    if tag == 'p':         return f'<p>{escape_html(text)}{children_html}</p>{etail}'
    if tag == 'v':         return f'{escape_html(text)}{children_html}<br>{etail}'
    if tag in ('subtitle',): return f'<h3>{escape_html(text)}{children_html}</h3>{etail}'
    if tag == 'empty-line': return f'<br>{etail}'
    if tag == 'image':
        href = el.attrib.get('{http://www.w3.org/1999/xlink}href', '')
        return f'<img src="{href[1:] if href.startswith("#") else href}" alt="">{etail}'
    # Unknown tags: just render content
    return f'{escape_html(text)}{children_html}{etail}'


def section_to_html(section, depth: int = 0) -> tuple[str, str]:
    """Convert FB2 section to (title_text, body_html)."""
    title_el = section.find('./{*}title')
    title = ''
    if title_el is not None:
        title = ''.join(title_el.itertext()).strip()

    html_parts = []
    if title:
        htag = f'h{min(depth + 1, 3)}'
        html_parts.append(f'<{htag}>{escape_html(title)}</{htag}>')

    for child in section:
        tag = strip_ns(child.tag)
        if tag == 'title':
            continue
        elif tag == 'section':
            # Nested section — recurse
            _, sub_html = section_to_html(child, depth + 1)
            html_parts.append(sub_html)
        elif tag == 'p':
            html_parts.append(el_to_html(child))
        elif tag in ('epigraph', 'annotation'):
            inner = ''.join(el_to_html(c) for c in child)
            html_parts.append(f'<blockquote class="epigraph">{inner}</blockquote>')
        elif tag in ('poem',):
            stanzas = ''.join(
                '<p>' + ''.join(el_to_html(v) for v in stanza.findall('./{*}v')) + '</p>'
                for stanza in child.findall('./{*}stanza')
            )
            html_parts.append(f'<blockquote class="poem">{stanzas}</blockquote>')
        elif tag == 'subtitle':
            html_parts.append(f'<h3>{escape_html("".join(child.itertext()))}</h3>')
        elif tag == 'empty-line':
            html_parts.append('<br>')
        elif tag == 'image':
            href = child.attrib.get('{http://www.w3.org/1999/xlink}href', '')
            html_parts.append(f'<img src="{href[1:] if href.startswith("#") else href}" alt="">')
        elif tag == 'cite':
            inner = ''.join(el_to_html(c) for c in child)
            html_parts.append(f'<blockquote>{inner}</blockquote>')
        elif tag == 'table':
            html_parts.append(el_to_html(child))

    return title, '\n'.join(html_parts)


def ingest_fb2(input_path: Path, out_dir: Path, lang: str = 'ru'):
    print(f"Parsing FB2: {input_path}")

    raw = input_path.read_bytes()
    # Handle .fb2.zip
    if input_path.suffix.lower() == '.zip':
        import io
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            fb2_names = [n for n in zf.namelist() if n.lower().endswith('.fb2')]
            if not fb2_names:
                print("Error: no .fb2 file inside zip")
                return
            raw = zf.read(fb2_names[0])

    root = ET.fromstring(raw)

    assets_dir = out_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    # Extract embedded images
    binaries: dict[str, str] = {}
    for binary in root.findall('.//{*}binary'):
        b_id = binary.attrib.get('id', '')
        if b_id and binary.text:
            try:
                data = base64.b64decode(binary.text.strip())
                safe_name = b_id.replace('/', '_')
                (assets_dir / safe_name).write_bytes(data)
                binaries[b_id] = f'assets/{safe_name}'
            except Exception as e:
                print(f"  Warning: could not decode image {b_id}: {e}")

    body = root.find('.//{*}body')
    if body is None:
        print("Error: no <body> in FB2")
        return

    chapter_idx = 1
    for section in body.findall('./{*}section'):
        title_text, body_html = section_to_html(section, depth=0)
        chapter_title = title_text or f'Chapter {chapter_idx}'

        # Fix image src references
        for b_id, path_str in binaries.items():
            body_html = body_html.replace(f'src="{b_id}"', f'src="{path_str}"')

        html = (
            f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<title>{escape_html(chapter_title)}</title>\n</head>\n<body>\n'
            f'{body_html}\n</body>\n</html>'
        )
        out_file = out_dir / f'chapter{chapter_idx}.html'
        out_file.write_text(html, encoding='utf-8')
        chapter_idx += 1

    print(f"Done. Extracted {chapter_idx - 1} chapters to {out_dir}")


def inline_epub_css(html: str, assets_dir: Path) -> str:
    """Inline linked CSS <link> tags as <style> blocks. Attribute-order independent."""
    def replace_link(m):
        tag = m.group(0)
        rel_m = re.search(r'rel=["\']([^"\']+)["\']', tag, re.I)
        href_m = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if not rel_m or 'stylesheet' not in rel_m.group(1).lower():
            return tag
        if not href_m:
            return tag
        href = href_m.group(1)
        if href.startswith('assets/'):
            css_path = assets_dir / href[len('assets/'):]
            if css_path.exists():
                try:
                    css_content = css_path.read_text(encoding='utf-8', errors='replace')
                    return f'<style>{css_content}</style>'
                except Exception:
                    pass
        return tag
    return re.sub(r'<link[^>]*/?>',  replace_link, html, flags=re.I)


def ingest_epub(input_path: Path, out_dir: Path, lang: str = 'ru'):
    print(f"Parsing EPUB: {input_path}")
    assets_dir = out_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(input_path, 'r') as zf:
        # Find OPF file
        try:
            container = ET.fromstring(zf.read('META-INF/container.xml'))
            opf_path = container.find('.//{*}rootfile').attrib['full-path']
            base_path = posixpath.dirname(opf_path)
        except Exception:
            print("Error: invalid EPUB (cannot find container.xml or OPF)")
            return

        opf = ET.fromstring(zf.read(opf_path))
        manifest: dict[str, dict] = {}
        for item in opf.findall('.//{*}item'):
            manifest[item.attrib['id']] = {
                'href': item.attrib.get('href', ''),
                'type': item.attrib.get('media-type', ''),
                'props': item.attrib.get('properties', ''),
            }

        spine = [item.attrib['idref'] for item in opf.findall('.//{*}itemref')]

        # Extract all assets (images, fonts, css)
        for m in manifest.values():
            href = m['href']
            ext = posixpath.splitext(href)[1].lower()
            if ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.css', '.woff', '.woff2'):
                try:
                    full = posixpath.join(base_path, href) if base_path else href
                    data = zf.read(full)
                    # Use double underscore to avoid collisions
                    safe = href.replace('/', '__').replace('..', '')
                    (assets_dir / safe).write_bytes(data)
                except Exception:
                    pass

        def fix_asset_path(src: str, chapter_href: str) -> str:
            """Rewrite relative asset src to assets/ flat directory."""
            if src.startswith('http') or src.startswith('data:') or src.startswith('#'):
                return src
            chapter_dir = posixpath.dirname(chapter_href)
            resolved = posixpath.normpath(posixpath.join(chapter_dir, src))
            safe = resolved.replace('/', '__').replace('..', '')
            return f'assets/{safe}'

        # Process spine chapters
        chapter_idx = 1
        # NCX navigation document (EPUB 2), SMIL media overlays (EPUB 3), and DTBook
        # are non-content spine items that must be skipped.
        skip_types = {
            'application/x-dtbncx+xml',
            'application/smil+xml',
            'application/x-dtbook+xml',
            'application/oebps-package+xml',
        }
        for s_id in spine:
            if s_id not in manifest:
                continue
            m = manifest[s_id]
            if m['type'] in skip_types or 'nav' in m['props']:
                continue

            href = m['href']
            full = posixpath.join(base_path, href) if base_path else href
            try:
                raw_bytes = zf.read(full)
                try:
                    html_data = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    html_data = raw_bytes.decode('latin-1')

                # Rewrite asset paths to use assets/ flat directory
                def replace_asset(mo):
                    attr = mo.group(1)
                    src = mo.group(2)
                    # Preserve inter-chapter navigation links
                    if src.startswith('#') or src.split('#')[0].lower().endswith(('.html', '.xhtml', '.htm')):
                        return mo.group(0)
                    return f'{attr}="{fix_asset_path(src, href)}"'

                html_data = re.sub(
                    r'(src|href)=["\']([^"\']+)["\']',
                    replace_asset,
                    html_data
                )

                # Inline CSS assets
                html_data = inline_epub_css(html_data, assets_dir)

                # Inject lang attribute if missing (EPUB source may not set it, or may use wrong lang)
                if not re.search(r'<html[^>]+\blang\s*=', html_data[:500], re.I):
                    html_data = re.sub(r'<html([^>]*)>', f'<html\\1 lang="{lang}">', html_data,
                                       count=1, flags=re.I)

                out_file = out_dir / f'chapter{chapter_idx}.html'
                out_file.write_text(html_data, encoding='utf-8')
                chapter_idx += 1
            except Exception as e:
                print(f"  Warning: skipping {href}: {e}")

    print(f"Done. Extracted {chapter_idx - 1} chapters to {out_dir}")


def ingest_docx(input_path: Path, out_dir: Path, lang: str = 'ru'):
    """Requires: pip install python-docx lxml"""
    try:
        from docx import Document
        from lxml import etree  # noqa: F401 - needed for run._r.xpath()
    except ImportError as e:
        print(f"Error: {e}. Run: pip install python-docx lxml")
        return

    print(f"Parsing DOCX: {input_path}")
    doc = Document(str(input_path))
    assets_dir = out_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)

    HEADING_STYLES = {'Heading 1', 'Heading 2', 'Heading 3', 'Заголовок 1', 'Заголовок 2'}

    def _is_heading(para):
        """Detect headings by named style OR outline level (for custom-styled DOCX files)."""
        style_name = para.style.name if para.style else ''
        if style_name in HEADING_STYLES:
            return True
        # python-docx exposes outline level via paragraph format
        try:
            if para.paragraph_format.outline_level is not None and para.paragraph_format.outline_level < 3:
                return True
        except AttributeError:
            pass
        return False

    chapters: list[tuple[str, list[str]]] = []  # [(title, [html_parts])]
    current_title = 'Chapter 1'
    current_parts: list[str] = []

    # Map for deduplicating images
    img_map: dict[str, str] = {} # rId -> path

    for para in doc.paragraphs:
        style_name = para.style.name if para.style else ''
        text = para.text.strip()

        if _is_heading(para):
            if current_parts:
                chapters.append((current_title, current_parts))
            current_title = text or current_title
            current_parts = [f'<h1>{escape_html(text)}</h1>']
        else:
            # Build paragraph with inline formatting
            html_parts = []
            
            # Extract images from this paragraph
            for run in para.runs:
                # 1. Process Text
                t = escape_html(run.text)
                if run.bold:   t = f'<b>{t}</b>'
                if run.italic: t = f'<em>{t}</em>'
                if run.underline: t = f'<u>{t}</u>'
                html_parts.append(t)

                # 2. Process Images in Run
                # Check for drawing elements in the run's XML
                r_el = run._r
                drawings = r_el.xpath('.//w:drawing', namespaces=r_el.nsmap)
                for drawing in drawings:
                    blips = drawing.xpath('.//a:blip', namespaces=drawing.nsmap)
                    for blip in blips:
                        rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        if rId and rId not in img_map:
                            image_part = doc.part.related_parts[rId]
                            img_ext = Path(image_part.partname).suffix or '.png'
                            img_name = f"docx_{rId}{img_ext}"
                            (assets_dir / img_name).write_bytes(image_part.blob)
                            img_map[rId] = f"assets/{img_name}"
                        
                        if rId in img_map:
                            html_parts.append(f'<img src="{img_map[rId]}" alt="DOCX Image">')

            para_html = "".join(html_parts).strip()
            if para_html:
                current_parts.append(f'<p>{para_html}</p>')

    if current_parts:
        chapters.append((current_title, current_parts))
    
    print(f"  Extracted {len(img_map)} images from DOCX.")

    for i, (title, parts) in enumerate(chapters, 1):
        html = (
            f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<title>{escape_html(title)}</title>\n</head>\n<body>\n'
            f'{"".join(parts)}\n</body>\n</html>'
        )
        (out_dir / f'chapter{i}.html').write_text(html, encoding='utf-8')

    print(f"Done. Extracted {len(chapters)} chapters to {out_dir}")


def ingest_pdf(input_path: Path, out_dir: Path, lang: str = 'ru', chapters_config: list | None = None):
    if not HAS_PDF:
        print("Error: fitz (PyMuPDF) not found. PDF support disabled.")
        print("Install it with: pip install pymupdf")
        return
    print(f"Parsing PDF: {input_path}")
    config: dict = {"lang": lang}
    if chapters_config:
        config["chapters"] = chapters_config
    processor = PDFParser(str(input_path), config)
    processor.run(str(out_dir))


def main():
    p = argparse.ArgumentParser(
        description='Ingest books (FB2, EPUB, DOCX, PDF) into chapter HTML files.'
    )
    p.add_argument('--input',          required=True, help='Path to source file (.fb2, .epub, .docx, .pdf, .fb2.zip)')
    p.add_argument('--output',         required=True, help='Output directory for chapter HTML files')
    p.add_argument('--force',          action='store_true', help='Overwrite output directory if it exists')
    p.add_argument('--lang',           default='ru', help='Language code for generated HTML (default: ru)')
    p.add_argument('--pdf-chapters',   default=None,
                   help='PDF only: JSON file defining chapter splits. '
                        'Format: [["Title", start_page, end_page], ...]. '
                        'Without this flag, the whole PDF becomes one chapter.')
    args = p.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.output)
    lang    = args.lang

    if not in_path.exists():
        print(f"Error: input file not found: {in_path}")
        raise SystemExit(1)

    if out_dir.exists():
        if args.force:
            shutil.rmtree(out_dir)
        else:
            print(f"Error: output directory exists: {out_dir}. Use --force to overwrite.")
            raise SystemExit(1)
    out_dir.mkdir(parents=True)

    suffix = in_path.suffix.lower()
    name   = in_path.name.lower()

    if suffix == '.fb2' or name.endswith('.fb2.zip'):
        ingest_fb2(in_path, out_dir, lang)
    elif suffix == '.epub':
        ingest_epub(in_path, out_dir, lang)
    elif suffix == '.docx':
        ingest_docx(in_path, out_dir, lang)
    elif suffix == '.pdf':
        chapters_config = None
        if args.pdf_chapters:
            import json
            try:
                with open(args.pdf_chapters, encoding='utf-8') as f:
                    chapters_config = json.load(f)
            except Exception as e:
                print(f"Error: could not read --pdf-chapters file: {e}")
                raise SystemExit(1)
        ingest_pdf(in_path, out_dir, lang, chapters_config)
    elif suffix == '.doc':
        print("Error: .doc (Word 97 binary) is not supported. Please save as .docx and retry.")
        raise SystemExit(1)
    else:
        print(f"Error: unsupported format '{suffix}'. Supported: .fb2, .fb2.zip, .epub, .docx, .pdf")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
