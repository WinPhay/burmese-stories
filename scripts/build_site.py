#!/usr/bin/env python3
"""
Static Web Reader Generator for Burmese Stories
Compiles markdown stories and assets into a responsive, mobile-first PWA-ready web reader.
"""

import os
import re
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"
ASSETS_DIR = REPO_ROOT / "assets"
DIST_SITE = REPO_ROOT / "dist" / "site"

CATEGORY_NAMES = {
    "children": "ကလေးပုံပြင်များ",
    "folklore": "ရိုးရာနှင့် ဒဏ္ဍာရီများ",
    "contemporary": "ခေတ်ပေါ်ပုံပြင်များ",
}

CATEGORY_COLORS = {
    "children": "#e67e22",
    "folklore": "#27ae60",
    "contemporary": "#2980b9",
}

def parse_frontmatter(content):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    raw_meta, body = match.groups()
    meta = {}
    for line in raw_meta.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                val = [item.strip().strip('"').strip("'") for item in val[1:-1].split(",") if item.strip()]
            meta[key] = val
    return meta, body

def get_stories():
    stories = []
    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
            continue
        content = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        if not meta.get("id"):
            continue
        
        # Extract slug
        slug = md_file.stem
        # Extract illustration
        img_match = re.search(r"!\[.*?\]\((.*?)\)", body)
        img_src = img_match.group(1) if img_match else None
        if img_src:
            img_filename = Path(img_src).name
            img_web_path = f"assets/illustrations/{img_filename}"
        else:
            img_web_path = ""
            
        stories.append({
            "meta": meta,
            "body": body,
            "slug": slug,
            "category": meta.get("category", "children"),
            "img_web_path": img_web_path,
            "file_path": md_file
        })
    return stories

def render_markdown_to_html(body):
    # Remove image tag from body since it will be rendered in the header
    clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    
    # Strip any explicit structural beat headers (e.g., ## ၁။ အစပျိုးခြင်း, ## ၂။ ဖြစ်စဉ်ပျိုးခြင်း)
    clean_body = re.sub(r"^##\s*[၀-၉\d]+[။\.\)]\s*.*$", "", clean_body, flags=re.MULTILINE)
    clean_body = re.sub(r"^---\s*$", "", clean_body, flags=re.MULTILINE)
    
    # Remove top title # Title
    clean_body = re.sub(r"^#\s+(.+)$", r"<!-- title -->", clean_body, flags=re.MULTILINE)
    
    # Render moral section
    def moral_sub(m):
        return f'<div class="moral-box"><div class="moral-label">သင်ခန်းစာ</div><div class="moral-content">{m.group(1).strip()}</div></div>'
    
    clean_body = re.sub(r'^##\s+သင်ခန်းစာ\s*\n*(.*?)(?=\n##|$)', moral_sub, clean_body, flags=re.DOTALL | re.MULTILINE)
    
    # Render any other legitimate h2 headers
    clean_body = re.sub(r"^##\s+(.+)$", r'<h2 class="section-title">\1</h2>', clean_body, flags=re.MULTILINE)
    
    # Split paragraphs
    paragraphs = []
    for block in clean_body.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("<!--"):
            continue
        if block.startswith("<h2") or block.startswith("<div"):
            paragraphs.append(block)
        else:
            # Inline bold / quotes
            block = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", block)
            paragraphs.append(f"<p>{block}</p>")
            
    return "\n".join(paragraphs)

BASE_CSS = """
:root {
  --bg-primary: #fdfbf7;
  --bg-card: #ffffff;
  --text-main: #2c3e50;
  --text-muted: #64748b;
  --accent-color: #d35400;
  --border-color: #e2e8f0;
  --header-bg: rgba(253, 251, 247, 0.95);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.04);
  --shadow-md: 0 8px 24px rgba(0,0,0,0.07);
}

[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-card: #1e293b;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --accent-color: #f97316;
  --border-color: #334155;
  --header-bg: rgba(15, 23, 42, 0.95);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
  --shadow-md: 0 8px 24px rgba(0,0,0,0.4);
}

[data-theme="sepia"] {
  --bg-primary: #f4ecd8;
  --bg-card: #fdf6e2;
  --text-main: #433422;
  --text-muted: #79664f;
  --accent-color: #b35900;
  --border-color: #e6dac2;
  --header-bg: rgba(244, 236, 216, 0.95);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Noto Sans Myanmar", "Pyidaungsu", -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
  line-height: 1.8;
  transition: background-color 0.3s, color 0.3s;
}

header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-link {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--accent-color);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.telegram-pill {
  background: #0088cc;
  color: white;
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: transform 0.2s;
}
.telegram-pill:hover { transform: scale(1.04); }

.theme-toggles {
  display: flex;
  gap: 8px;
  align-items: center;
}

.theme-btn, .font-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}

.container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 20px 80px 20px;
}

.hero {
  text-align: center;
  padding: 32px 0 40px;
}
.hero h1 {
  font-size: 2.2rem;
  color: var(--accent-color);
  margin-bottom: 8px;
}
.hero p {
  color: var(--text-muted);
  font-size: 1.1rem;
}

.filter-bar {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 36px;
  flex-wrap: wrap;
}
.filter-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 8px 18px;
  border-radius: 24px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.2s;
}
.filter-btn.active, .filter-btn:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 28px;
}

.story-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}
.story-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.card-img-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 */
  background: #eee;
  overflow: hidden;
}
.card-img-wrapper img {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.story-card:hover .card-img-wrapper img {
  transform: scale(1.03);
}

.card-badge {
  position: absolute;
  top: 12px; left: 12px;
  color: white;
  font-size: 0.75rem;
  font-weight: bold;
  padding: 4px 10px;
  border-radius: 12px;
  backdrop-filter: blur(4px);
}

.card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-body h3 {
  font-size: 1.25rem;
  margin-bottom: 8px;
  line-height: 1.5;
}

.card-meta {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.card-lesson-preview {
  font-size: 0.95rem;
  color: var(--text-muted);
  line-height: 1.6;
  flex: 1;
  margin-bottom: 20px;
}

.card-actions {
  display: flex;
  gap: 10px;
}
.btn-read {
  flex: 1;
  background: var(--accent-color);
  color: white;
  text-decoration: none;
  padding: 10px;
  border-radius: 8px;
  text-align: center;
  font-weight: bold;
}
.btn-pdf {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Reader Page Specific */
.reader-container {
  max-width: 780px;
  margin: 0 auto;
  padding: 32px 20px 80px;
}

.reader-header {
  margin-bottom: 24px;
}

.reader-cover {
  width: 100%;
  border-radius: 16px;
  box-shadow: var(--shadow-md);
  margin-bottom: 32px;
  max-height: 480px;
  object-fit: cover;
}

.reader-content p {
  font-size: var(--font-size, 1.15rem);
  line-height: 2.1;
  margin-bottom: 24px;
  text-align: justify;
}

.section-title {
  font-size: 1.35rem;
  color: var(--accent-color);
  margin: 36px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px dashed var(--border-color);
}

.moral-box {
  background: rgba(211, 84, 0, 0.08);
  border-left: 5px solid var(--accent-color);
  padding: 24px;
  border-radius: 12px;
  margin: 40px 0;
}
.moral-label {
  font-weight: bold;
  color: var(--accent-color);
  font-size: 1.1rem;
  margin-bottom: 8px;
}
.moral-content {
  font-size: 1.15rem;
  line-height: 1.9;
}

.reader-footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
"""

READER_JS = """
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('burmese_stories_theme', theme);
}

function filterCategory(cat, btn) {
  if (btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  document.querySelectorAll('.story-card').forEach(card => {
    if (cat === 'all' || card.getAttribute('data-category') === cat) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

function adjustFontSize(delta) {
  let size = parseFloat(localStorage.getItem('burmese_stories_fontsize') || 1.15);
  size = Math.min(Math.max(size + delta, 0.9), 1.6);
  document.documentElement.style.setProperty('--font-size', size + 'rem');
  localStorage.setItem('burmese_stories_fontsize', size);
}

document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('burmese_stories_theme') || 'light';
  setTheme(savedTheme);
  const savedSize = localStorage.getItem('burmese_stories_fontsize');
  if (savedSize) {
    document.documentElement.style.setProperty('--font-size', savedSize + 'rem');
  }
  // Ensure all story cards are visible on initial load
  document.querySelectorAll('.story-card').forEach(c => c.style.display = 'flex');
});
"""

def generate_catalog_html(stories):
    cards_html = []
    for s in stories:
        meta = s["meta"]
        cat_key = s["category"]
        cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
        cat_color = CATEGORY_COLORS.get(cat_key, "#333")
        
        pdf_filename = f"{s['slug']}.pdf" if s['slug'].startswith(meta.get('id', '')) else f"{meta.get('id')}-{s['slug']}.pdf"
        cards_html.append(f"""
        <div class="story-card" data-category="{cat_key}">
          <div class="card-img-wrapper">
            <span class="card-badge" style="background: {cat_color}">{cat_name}</span>
            <img src="{s['img_web_path']}" alt="{meta.get('title_my', '')}" loading="lazy" />
          </div>
          <div class="card-body">
            <h3>{meta.get('title_my', '')}</h3>
            <div class="card-meta">{meta.get('title_en', '')} • {meta.get('target_audience', 'All Ages')}</div>
            <div class="card-lesson-preview">{meta.get('lesson', '')}</div>
            <div class="card-actions">
              <a href="stories/{s['slug']}.html" class="btn-read">ဖတ်ရှုရန်</a>
              <a href="pdf/{pdf_filename}" class="btn-pdf" download title="Download PDF">📄 PDF</a>
            </div>
          </div>
        </div>
        """)
        
    return f"""<!DOCTYPE html>
<html lang="my">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>မြန်မာပုံပြင်များ — Burmese Stories Collection</title>
  <meta name="description" content="ကလေးလူငယ်များနှင့် မိဘဆရာများအတွက် အသိပညာပေး မူရင်းမြန်မာပုံပြင်များ">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&display=swap" rel="stylesheet">
  <style>{BASE_CSS}</style>
</head>
<body>
  <header>
    <a href="./" class="brand-link">📖 မြန်မာပုံပြင်များ</a>
    <div style="display: flex; gap: 12px; align-items: center;">
      <a href="https://t.me/stellarpub_official" target="_blank" class="telegram-pill">
        <span>📢 @stellarpub_official</span>
      </a>
      <div class="theme-toggles">
        <button class="theme-btn" onclick="setTheme('light')">☀️</button>
        <button class="theme-btn" onclick="setTheme('sepia')">📜</button>
        <button class="theme-btn" onclick="setTheme('dark')">🌙</button>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="hero">
      <h1>မြန်မာပုံပြင်များ စုစည်းမှု</h1>
      <p>ဘဝအတွက် အဖိုးတန်သော အတွေးအမြင်နှင့် သင်ခန်းစာများ ပေးစွမ်းနိုင်မည့် ပုံပြင်များ</p>
    </div>

    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterCategory('all', this)">အားလုံး ({len(stories)})</button>
      <button class="filter-btn" onclick="filterCategory('children', this)">ကလေးပုံပြင်များ</button>
      <button class="filter-btn" onclick="filterCategory('folklore', this)">ရိုးရာနှင့် ဒဏ္ဍာရီများ</button>
      <button class="filter-btn" onclick="filterCategory('contemporary', this)">ခေတ်ပေါ်ပုံပြင်များ</button>
    </div>

    <div class="story-grid">
      {''.join(cards_html)}
    </div>
  </div>

  <script>{READER_JS}</script>
</body>
</html>
"""

def generate_story_html(story):
    meta = story["meta"]
    body_html = render_markdown_to_html(story["body"])
    cat_key = story["category"]
    cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
    cat_color = CATEGORY_COLORS.get(cat_key, "#333")
    pdf_filename = f"{story['slug']}.pdf" if story['slug'].startswith(meta.get('id', '')) else f"{meta.get('id')}-{story['slug']}.pdf"

    return f"""<!DOCTYPE html>
<html lang="my">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{meta.get('title_my', '')} — မြန်မာပုံပြင်များ</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&display=swap" rel="stylesheet">
  <style>{BASE_CSS}</style>
</head>
<body>
  <header>
    <a href="../" class="brand-link">← ပုံပြင်များသို့ ပြန်သွားရန်</a>
    <div style="display: flex; gap: 8px; align-items: center;">
      <button class="font-btn" onclick="adjustFontSize(-0.1)">A-</button>
      <button class="font-btn" onclick="adjustFontSize(0.1)">A+</button>
      <div class="theme-toggles">
        <button class="theme-btn" onclick="setTheme('light')">☀️</button>
        <button class="theme-btn" onclick="setTheme('sepia')">📜</button>
        <button class="theme-btn" onclick="setTheme('dark')">🌙</button>
      </div>
    </div>
  </header>

  <div class="reader-container">
    <div class="reader-header">
      <span style="background: {cat_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
        {cat_name}
      </span>
      <h1 style="font-size: 2.2rem; color: var(--accent-color); margin: 16px 0 8px;">{meta.get('title_my', '')}</h1>
      <div style="color: var(--text-muted); font-size: 1rem; margin-bottom: 24px;">
        {meta.get('title_en', '')} • {meta.get('target_audience', 'All Ages')}
      </div>
    </div>

    <img src="../{story['img_web_path']}" alt="{meta.get('title_my', '')}" class="reader-cover" />

    <div class="reader-content">
      {body_html}
    </div>

    <div class="reader-footer">
      <a href="../" class="btn-pdf">← ပုံပြင်အားလုံး ကြည့်ရှုရန်</a>
      <div style="display: flex; gap: 10px;">
        <a href="../pdf/{pdf_filename}" class="btn-pdf" download>📄 A4 Print PDF ဒေါင်းလုဒ်</a>
        <a href="https://t.me/stellarpub_official" target="_blank" class="telegram-pill">📢 @stellarpub_official</a>
      </div>
    </div>
  </div>

  <script>{READER_JS}</script>
</body>
</html>
"""

def main():
    print("Building Web Reader...")
    # Prepare dist directory
    if DIST_SITE.exists():
        shutil.rmtree(DIST_SITE)
    DIST_SITE.mkdir(parents=True, exist_ok=True)
    (DIST_SITE / "stories").mkdir(parents=True, exist_ok=True)
    (DIST_SITE / "pdf").mkdir(parents=True, exist_ok=True)
    
    # Copy assets
    shutil.copytree(ASSETS_DIR, DIST_SITE / "assets")
    
    stories = get_stories()
    print(f"Loaded {len(stories)} stories.")
    
    # Build index.html
    index_html = generate_catalog_html(stories)
    (DIST_SITE / "index.html").write_text(index_html, encoding="utf-8")
    
    # Build story pages
    for s in stories:
        story_html = generate_story_html(s)
        (DIST_SITE / "stories" / f"{s['slug']}.html").write_text(story_html, encoding="utf-8")
        
    print(f"Web reader successfully generated at {DIST_SITE}")

if __name__ == "__main__":
    main()
