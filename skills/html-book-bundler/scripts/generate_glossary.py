#!/usr/bin/env python3
"""
Generate glossary.html from terms.json
"""
import argparse
import json
import pathlib
import sys

def generate_glossary(input_path: str, output_path: str):
    inp = pathlib.Path(input_path)
    out = pathlib.Path(output_path)
    
    if not inp.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)
        
    try:
        data = json.loads(inp.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
        
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="en">')
    html_parts.append('<head>')
    html_parts.append('<meta charset="utf-8">')
    html_parts.append('<title>Glossary</title>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append('<div class="wrap">')
    html_parts.append('<section class="hero">')
    html_parts.append('  <div class="kicker">Reference</div>')
    html_parts.append('  <h1>Glossary</h1>')
    html_parts.append('</section>')
    html_parts.append('<div class="content-body">')
    html_parts.append('<dl class="glossary-list">')
    
    # Handle dict or list format for terms.json
    terms = []
    if isinstance(data, dict):
        terms = sorted(data.items(), key=lambda x: x[0].lower())
    elif isinstance(data, list):
        terms = sorted(data, key=lambda x: x.get('term', '').lower())
        terms = [(t.get('term', ''), t.get('definition', '')) for t in terms]
    else:
        print("Invalid format in terms.json")
        sys.exit(1)
        
    for term, definition in terms:
        html_parts.append(f'  <dt id="term-{term.lower().replace(" ", "-")}">{term}</dt>')
        html_parts.append(f'  <dd>{definition}</dd>')
        
    html_parts.append('</dl>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    out.write_text('\n'.join(html_parts), encoding='utf-8')
    print(f"Generated {output_path} with {len(terms)} terms.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate glossary.html from terms.json")
    parser.add_argument('--input', default='terms.json')
    parser.add_argument('--output', default='glossary.html')
    args = parser.parse_args()
    generate_glossary(args.input, args.output)
