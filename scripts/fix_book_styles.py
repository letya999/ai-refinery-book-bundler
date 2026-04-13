import base64
import re
import json

def decode_b64(data):
    return base64.b64decode(data).decode('utf-8')

def encode_b64(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

# ФИНАЛЬНЫЙ ЭТАЛОННЫЙ CSS (на основе анализа preview-book)
ULTIMATE_CSS = """
:root {
  --bg: #070d19; --bg-grad: radial-gradient(circle at 15% -20%, #1c3d6d 0, #0d1a31 45%, #070d19 85%);
  --panel: rgba(15, 31, 56, 0.7); --line: rgba(57, 95, 157, 0.4);
  --txt: #f0f7ff; --muted: #94a9c9; --acc: #72d8ff; --acc2: #87efc9;
}
* { box-sizing: border-box; -webkit-font-smoothing: antialiased; }
body { 
  margin: 0; background: var(--bg-grad); color: var(--txt); 
  font: 400 17px/1.65 "Segoe UI Variable Text", system-ui, sans-serif; 
}
.wrap { max-width: 1000px; margin: 0 auto; padding: 40px 20px 100px; }

/* HERO SECTION */
.hero { 
  position: relative; padding: 48px; border: 1px solid var(--line); border-radius: 28px; 
  background: linear-gradient(135deg, rgba(20,40,75,0.4), rgba(10,20,40,0.6));
  backdrop-filter: blur(20px); overflow: hidden; margin-bottom: 48px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.3);
}
.hero::before {
  content: ""; position: absolute; inset: 0; 
  background: linear-gradient(-45deg, transparent, rgba(114,216,255,0.05), transparent);
  animation: shine 8s infinite linear;
}
@keyframes shine { 0% { transform: translateX(-100%) } 100% { transform: translateX(100%) } }

.kicker { font-size: 12px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--acc); margin-bottom: 12px; }
h1 { margin: 0 0 16px; font-size: clamp(34px, 6vw, 60px); font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; color: #fff; }
.lead { font-size: 20px; line-height: 1.5; color: var(--muted); max-width: 800px; }

/* CONTENT ELEMENTS */
.sec { margin-top: 56px; padding: 40px; border: 1px solid var(--line); border-radius: 32px; background: var(--panel); backdrop-filter: blur(12px); }
.sec h2 { margin: 0 0 24px; font-size: 32px; font-weight: 700; letter-spacing: -0.02em; color: var(--acc); }

.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin-top: 32px; }
.card { 
  padding: 32px; background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 24px; transition: 0.4s; 
}
.card:hover { transform: translateY(-8px); background: rgba(255,255,255,0.06); border-color: var(--acc); }
.card b { display: block; margin-bottom: 8px; font-size: 13px; color: var(--acc2); text-transform: uppercase; letter-spacing: 0.1em; }
.card h3 { margin: 0 0 12px; font-size: 22px; color: #fff; }

blockquote { 
  margin: 48px 0; padding: 10px 0 10px 32px; border-left: 5px solid var(--acc); 
  font-size: 22px; line-height: 1.4; font-style: italic; color: #d1e3ff; 
}
"""

def fix_chapter(html, idx):
    # Удаляем старые стили и заменяем на новые
    html = re.sub(r'<style>.*?</style>', f'<style>{ULTIMATE_CSS}</style>', html, flags=re.DOTALL)
    
    # Исправляем структуру body
    body_match = re.search(r'<body>(.*?)</body>', html, re.DOTALL)
    if not body_match: return html
    body = body_match.group(1)
    
    # Если это "пустая" глава без Hero (4-5), оборачиваем
    if 'class="hero"' not in body:
        h1 = re.search(r'<h1>(.*?)</h1>', body)
        lead = re.search(r'<(p|div) class="lead">(.*?)</\1>', body)
        
        title = h1.group(1) if h1 else f"Глава {idx+1}"
        desc = lead.group(2) if lead else ""
        
        content = body
        if h1: content = content.replace(h1.group(0), "")
        if lead: content = content.replace(lead.group(0), "")
        
        new_body = f'''
<main class="wrap">
  <section class="hero">
    <div class="kicker">P3.express • Глава {idx+1}</div>
    <h1>{title}</h1>
    <p class="lead">{desc}</p>
  </section>
  <div class="content-body">{content}</div>
</main>
'''
        html = html.replace(body, new_body)
    elif 'class="wrap"' not in body:
        html = html.replace(body, f'<main class="wrap">{body}</main>')
        
    return html

def update_book(path):
    with open(path, 'r', encoding='utf-8') as f:
        full_html = f.read()

    # Поиск массива данных (безопасный паттерн)
    match = re.search(r'(LOCAL_B64|B64)\s*=\s*\[(.*?)\]\s*;', full_html, re.DOTALL)
    if not match:
        print("Data array not found!")
        return

    var_name = match.group(1)
    data_str = match.group(2)
    
    # Извлечение элементов (поддержка одинарных и двойных кавычек)
    items = re.findall(r'["\'](.*?)["\']', data_str)
    
    fixed_items = []
    for i, item in enumerate(items):
        print(f"Fixing Chapter {i+1}...")
        decoded = decode_b64(item)
        fixed = fix_chapter(decoded, i)
        fixed_items.append(f'"{encode_b64(fixed)}"')
    
    # СБОРКА ОБРАТНО: ВАЖНО! Не добавляем лишних const
    # Ищем все вхождение объявления чтобы заменить его целиком
    new_array = f"{var_name} = [" + ",".join(fixed_items) + "];"
    
    # Заменяем только само присваивание, сохраняя контекст (let/const перед ним если есть)
    new_html = full_html.replace(match.group(0), new_array)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("Success!")

if __name__ == "__main__":
    update_book('C:/Users/User/a_projects/no_complex_book/ne-uslozhnyay-ULTIMATE-v6.html')
