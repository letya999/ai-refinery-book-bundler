---
name: book-ingester
description: Foundation Layer. Extracts raw text and images from PDF, EPUB, FB2, DOCX. Cleans OCR artifacts and sets structural H1/H2 marks.
---

# Book Ingester (v8.3)

You are the Foundation Layer. Your goal is to provide a clean, 100% complete text and image source for the Architect.

## Directives:
1. **Source Fidelity:** Extract all text without summarizing.
2. **Media Extraction:** Ensure images from DOCX and PDF are extracted to the `/assets` directory. Run `optimize_assets.py` to prevent mobile OOM crashes.
3. **Noise Suppression:** Strip page numbers, running headers, and OCR artifacts.
4. **Table Detection:** If a table is found, wrap it in `<!-- TABLE_START -->...<!-- TABLE_END -->` markers.
5. **Unified Entry:** Always use `../scripts/ingest.py` as the primary tool. It now handles PDF and DOCX (with images) natively.

## Workflow:
```bash
# FB2, EPUB, DOCX
python ../scripts/ingest.py --input book.epub --output ./chapters --force --lang ru

# PDF (whole book as one chapter — fastest)
python ../scripts/ingest.py --input book.pdf --output ./chapters --force --lang ru

# PDF with chapter splits (requires a chapters config JSON):
# chapters.json format: [["Chapter Title", start_page, end_page], ...]
python ../scripts/ingest.py --input book.pdf --output ./chapters --force --lang ru --pdf-chapters chapters.json
```

## Output:
- Raw HTML chapters in `chapter1.html`, `chapter2.html`, etc.
- Extracted images in `assets/`.

## Critical Lessons:
- **EPUB Navigation:** The path rewriting regex skips `.html`/`.xhtml`/`#` patterns to preserve inter-chapter links. Do NOT modify this logic.
- **EPUB Lang Injection:** `ingest_epub()` now accepts and propagates `--lang`. If the EPUB `<html>` element has no `lang=` attribute, the CLI value is injected. Without this, EPUB chapters may render with the wrong language metadata, affecting hyphenation and speech synthesis.
- **PDF Defaults:** Without `--pdf-chapters`, the PDF becomes a single `chapter1.html`. This is intentional for short books. For long books, provide `--pdf-chapters`.
- **PDF Heading Detection:** `pdf_parser_general.py` uses dynamic font baseline calculation (`_calculate_baseline`) to detect headings. It works for both Pocket (10pt) and A4 (11-12pt) formats.
- **DOCX Images:** Images extracted via `lxml` XPath on `w:drawing` elements. Requires `pip install python-docx lxml`.
- **Image Size:** Do NOT skip `optimize_assets.py` for PDF/DOCX sources. Unoptimized images cause mobile OOM crashes at >1000px width.
