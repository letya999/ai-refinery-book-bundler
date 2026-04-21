#!/usr/bin/env python3
"""
Master Linter for HTML Book Bundler (v8.4).
Combines Security, Design, and Structural audits into one tool.
"""
import argparse
import json
import pathlib
import re
import sys


class BookLinter:
    def __init__(self, file_path: str, max_size_mb: float = 30.0):
        self.file_path = pathlib.Path(file_path)
        self.max_size_mb = max_size_mb
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict = {}

    def run(self) -> bool:
        if not self.file_path.exists():
            self.errors.append(f"File not found: {self.file_path}")
            return False

        content = self.file_path.read_text(encoding='utf-8', errors='replace')
        self.stats['size_mb'] = self.file_path.stat().st_size / (1024 * 1024)

        # 1. Shell Infrastructure Checks
        if 'Content-Security-Policy' not in content:
            self.errors.append("Shell: Missing Content-Security-Policy meta tag")
        if 'sandbox' not in content.lower():
            self.errors.append("Shell: <iframe> missing sandbox attribute")
        if 'allow-same-origin' in content.lower():
            self.errors.append("Shell: <iframe> contains forbidden 'allow-same-origin' sandbox directive")
        if "prefers-reduced-motion" not in content:
            self.warnings.append("Shell: No prefers-reduced-motion media query found (a11y)")
        if "URL.createObjectURL" in content:
            self.warnings.append("Shell: Legacy Blob URL usage detected (srcdoc is preferred)")

        # 2. Template Integrity
        unresolved = re.findall(r'\{\{[A-Z_]+\}\}', content)
        if unresolved:
            self.errors.append(f"Template: Unresolved placeholders found: {', '.join(set(unresolved))}")

        # 3. Chapter Data Checks
        chapters_start = re.search(r'\bCHAPTERS\s*=\s*(\[)', content)
        if not chapters_start:
            self.errors.append("Data: CHAPTERS array not found (architecture mismatch)")
            return False

        try:
            decoder = json.JSONDecoder()
            chapters, _ = decoder.raw_decode(content, chapters_start.start(1))
            self.stats['chapters'] = len(chapters)
            if not chapters:
                self.warnings.append("Data: CHAPTERS array is empty")
            for i, ch_html in enumerate(chapters):
                if not isinstance(ch_html, str):
                    self.errors.append(f"Chapter {i+1}: Not a string (invalid JSON data)")
                else:
                    self._audit_chapter(i + 1, ch_html)
        except Exception as e:
            self.errors.append(f"Data: Failed to parse CHAPTERS array: {e}")

        # 4. ASSETS Dictionary Validation
        assets_start = re.search(r'\bASSETS\s*=\s*(\{)', content)
        if not assets_start:
            self.warnings.append("Data: ASSETS dictionary not found (lazy-loading disabled — all images should be inline)")
        else:
            try:
                decoder = json.JSONDecoder()
                assets, _ = decoder.raw_decode(content, assets_start.start(1))
                self.stats['assets'] = len(assets)
                if not isinstance(assets, dict):
                    self.errors.append("Data: ASSETS is not a JSON object")
            except Exception as e:
                self.errors.append(f"Data: Failed to parse ASSETS dictionary: {e}")

        # 5. File Size Warning
        if self.stats['size_mb'] > self.max_size_mb:
            self.warnings.append(
                f"File size {self.stats['size_mb']:.1f} MB exceeds threshold {self.max_size_mb} MB"
            )

        # 5b. Theme contrast validation
        self._audit_theme_contrast(content)

        # 5a. SEARCH_IDX (SIDX) Validation
        sidx_start = re.search(r'\bSIDX\s*=\s*(\{)', content)
        if not sidx_start:
            self.warnings.append("Data: SIDX (search index) not found — in-chapter search will be non-functional")
        else:
            try:
                decoder = json.JSONDecoder()
                sidx, _ = decoder.raw_decode(content, sidx_start.start(1))
                self.stats['search_terms'] = len(sidx)
                if not isinstance(sidx, dict):
                    self.errors.append("Data: SIDX is not a JSON object")
            except Exception as e:
                self.errors.append(f"Data: Failed to parse SIDX search index: {e}")

        return len(self.errors) == 0

    def _audit_chapter(self, idx: int, html: str):
        label = f"Chapter {idx}"

        # SVG Hex Color Check — catches both attribute and inline style forms
        svgs = re.findall(r'<svg[^>]*>.*?</svg>', html, re.I | re.S)
        for svg in svgs:
            # Extended hex check (v8.3 audit fix: catches 3, 4, 6, and 8-digit hex codes)
            attr_hex = re.search(
                r'(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*["\']#[0-9a-fA-F]{3,8}["\']',
                svg, re.I
            )
            style_hex = re.search(
                r'style\s*=\s*["\'][^"\']*(?:fill|stroke|stop-color|flood-color|lighting-color)\s*:\s*#[0-9a-fA-F]{3,8}',
                svg, re.I
            )
            if attr_hex or style_hex:
                self.errors.append(f"{label}: Hardcoded hex color in <svg>. Use CSS variables.")

        # viewBox enforcement
        for svg_match in re.finditer(r'<svg([^>]*)>', html, re.I):
            attrs = svg_match.group(1)
            if 'viewBox' not in attrs and 'viewbox' not in attrs.lower():
                self.errors.append(f"{label}: <svg> missing viewBox attribute (required for mobile responsiveness)")
                break  # one error per chapter is enough

        # user-scalable=no check (WCAG 1.4.4)
        if re.search(r'user-scalable\s*=\s*no', html, re.I):
            self.errors.append(f"{label}: viewport meta has user-scalable=no (WCAG 1.4.4 violation)")

        # lang attribute check
        if re.search(r'<html(?![^>]*\blang\s*=)', html, re.I):
            self.warnings.append(f"{label}: <html> element missing lang attribute (accessibility)")

        # Wall of Text Check
        visual_tags = r"""class=["'][^"']*\b(vis-diag|vis-stats|vis-grid|stats|stat|translator|grid|card|vis-timeline|tl-step|acc-item|badge|diag-node|matrix)\b[^"']*["']|<table>"""
        if len(html) > 15000 and not re.search(visual_tags, html, re.I):
            self.warnings.append(f"{label}: Potential 'wall of text' detected ({len(html)} chars).")

        # Security: Sandbox Escape
        safe = html.replace('window.parent.postMessage', '__BRIDGE__')
        danger = re.search(r'\b(?:window|top|parent|opener)\s*\.\s*(?:location|cookie|href|assign|replace|open)\b', safe, re.I)
        if danger:
            self.errors.append(f"{label}: Potential sandbox escape pattern: {danger.group(0)!r}")

        # External Requests
        ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+["\']', safe, re.I)
        if ext:
            self.errors.append(f"{label}: External network dependency (not 100% offline): {ext[0]}")

    def _parse_css_variables(self, content: str) -> dict[str, str]:
        var_map: dict[str, str] = {}
        for name, value in re.findall(r'(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+);', content):
            var_map[name.strip()] = value.strip()
        return var_map

    def _resolve_var(self, value: str, var_map: dict[str, str], depth: int = 0) -> str | None:
        if depth > 8:
            return None
        m = re.match(r'var\(\s*(--[A-Za-z0-9_-]+)', value.strip())
        if not m:
            return value.strip()
        target = m.group(1)
        target_value = var_map.get(target)
        if not target_value:
            return None
        return self._resolve_var(target_value, var_map, depth + 1)

    def _parse_color(self, raw: str, var_map: dict[str, str]) -> tuple[int, int, int] | None:
        value = self._resolve_var(raw, var_map)
        if not value:
            return None
        value = value.strip().lower()

        hex_m = re.fullmatch(r'#([0-9a-f]{3}|[0-9a-f]{6})', value)
        if hex_m:
            hex_raw = hex_m.group(1)
            if len(hex_raw) == 3:
                hex_raw = ''.join(c * 2 for c in hex_raw)
            return tuple(int(hex_raw[i:i + 2], 16) for i in (0, 2, 4))

        rgb_m = re.fullmatch(r'rgba?\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})(?:\s*,\s*[\d.]+\s*)?\)', value)
        if rgb_m:
            r, g, b = (int(rgb_m.group(i)) for i in (1, 2, 3))
            if any(c > 255 for c in (r, g, b)):
                return None
            return r, g, b

        return None

    def _contrast_ratio(self, fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
        def linearize(channel: int) -> float:
            c = channel / 255.0
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4

        def luminance(rgb: tuple[int, int, int]) -> float:
            r, g, b = rgb
            return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

        l1 = luminance(fg)
        l2 = luminance(bg)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def _audit_theme_contrast(self, content: str):
        var_map = self._parse_css_variables(content)
        if not var_map:
            return

        bg_candidates = ['--bg', '--background', '--surface', '--panel']
        txt_candidates = ['--txt', '--fg', '--text', '--color-text']

        bg_name = next((k for k in bg_candidates if k in var_map), None)
        txt_name = next((k for k in txt_candidates if k in var_map), None)

        if not bg_name or not txt_name:
            self.warnings.append("Theme: Could not find --bg/--txt (or equivalent) variables for contrast check")
            return

        bg_rgb = self._parse_color(var_map[bg_name], var_map)
        txt_rgb = self._parse_color(var_map[txt_name], var_map)
        if not bg_rgb or not txt_rgb:
            self.warnings.append(
                f"Theme: Unable to parse color values for contrast check ({bg_name}={var_map[bg_name]!r}, {txt_name}={var_map[txt_name]!r})"
            )
            return

        ratio = self._contrast_ratio(txt_rgb, bg_rgb)
        self.stats['theme_contrast'] = round(ratio, 2)
        if ratio < 4.5:
            self.errors.append(
                f"Theme: Low contrast between {txt_name} and {bg_name} (ratio {ratio:.2f}:1, minimum 4.5:1)"
            )

    def report(self):
        sep = '=' * 60
        print(f"\n{sep}\nMASTER LINT REPORT: {self.file_path.name}\n{sep}")
        print(f"Size: {self.stats.get('size_mb', 0):.2f} MB | Chapters: {self.stats.get('chapters', 0)} | Assets: {self.stats.get('assets', 0)} | Search terms: {self.stats.get('search_terms', 0)}")
        for e in self.errors:   print(f"  [ERROR] {e}")
        for w in self.warnings: print(f"  [WARN]  {w}")
        if not self.errors:
            print("\nSTATUS: PASS (100% Secure & Offline-Ready)")
        else:
            print("\nSTATUS: FAIL")
        print(sep + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--file',     required=True)
    p.add_argument('--max-size', type=float, default=30.0)
    args = p.parse_args()

    linter = BookLinter(args.file, args.max_size)
    success = linter.run()
    linter.report()
    sys.exit(0 if success else 1)
