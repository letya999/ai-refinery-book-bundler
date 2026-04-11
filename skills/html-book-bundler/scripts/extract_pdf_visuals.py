#!/usr/bin/env python3
"""Extract visual assets from PDF for interactive HTML books.

Usage:
  python skills/html-book-bundler/scripts/extract_pdf_visuals.py \
    --pdf ./book.pdf --out ./extracted --pages 1-5,12 --dpi 180

Outputs:
  - pages/page_XXX.png    (full-page render)
  - images/pXXX_iYY.png   (embedded raster images found on page)
  - manifest.json         (summary of exported assets)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import fitz  # PyMuPDF


def parse_pages(spec: str, max_pages: int) -> list[int]:
    items = set()
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            start, end = int(a), int(b)
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                if 1 <= p <= max_pages:
                    items.add(p)
        else:
            p = int(part)
            if 1 <= p <= max_pages:
                items.add(p)
    return sorted(items)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True, help='Path to PDF file')
    ap.add_argument('--out', required=True, help='Output directory')
    ap.add_argument('--pages', default='', help='Pages like 1-3,8,10-12 (1-based)')
    ap.add_argument('--dpi', type=int, default=180, help='Render DPI for full pages')
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    out = Path(args.out)
    pages_dir = out / 'pages'
    imgs_dir = out / 'images'
    out.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    imgs_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = doc.page_count
    pages = parse_pages(args.pages, total) if args.pages else list(range(1, total + 1))

    manifest: dict = {
        'pdf': str(pdf_path),
        'total_pages': total,
        'exported_pages': pages,
        'page_renders': [],
        'embedded_images': [],
    }

    zoom = args.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for p in pages:
        page = doc.load_page(p - 1)

        # full page render
        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_file = pages_dir / f'page_{p:03d}.png'
        pix.save(page_file)
        manifest['page_renders'].append({'page': p, 'file': str(page_file)})

        # embedded images (raster XObjects)
        img_list = page.get_images(full=True)
        for i, img in enumerate(img_list, start=1):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
            except Exception:
                continue
            ext = base.get('ext', 'png')
            img_bytes = base.get('image')
            if not img_bytes:
                continue
            out_file = imgs_dir / f'p{p:03d}_i{i:02d}.{ext}'
            out_file.write_bytes(img_bytes)
            manifest['embedded_images'].append(
                {
                    'page': p,
                    'index': i,
                    'xref': xref,
                    'width': base.get('width'),
                    'height': base.get('height'),
                    'colorspace': base.get('colorspace'),
                    'file': str(out_file),
                }
            )

    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Export complete: {out}')
    print(f'Pages rendered: {len(manifest["page_renders"])}')
    print(f'Embedded images: {len(manifest["embedded_images"])}')


if __name__ == '__main__':
    main()
