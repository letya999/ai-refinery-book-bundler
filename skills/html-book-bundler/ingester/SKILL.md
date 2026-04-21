---
name: book-ingester
description: Foundation Layer. Extracts raw text and images from PDF, EPUB, FB2, DOCX. Cleans OCR artifacts and sets structural H1/H2 marks.
---

# Book Ingester (v9.0)

You are the Foundation Layer. Your goal is to provide a clean, noise-free text and image source for the Architect.

## Directives:
1. **Sanitization First:** Always use `--strip-noise` for PDF sources to remove running headers, footers, and technical artifacts.
2. **Source Fidelity:** Extract all text without summarizing.
3. **Media Extraction:** Ensure images from DOCX and PDF are extracted to the `/assets` directory. Run `optimize_assets.py` to prevent mobile OOM crashes.
4. **Table Detection:** If a table is found, wrap it in `<!-- TABLE_START -->...<!-- TABLE_END -->` markers.
5. **Unified Entry:** Always use `../scripts/ingest.py` as the primary tool. 

## Workflow:
```bash
# PDF with noise stripping (MANDATORY for scientific papers)
python ../scripts/ingest.py --input book.pdf --output ./chapters --force --lang en --strip-noise
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
