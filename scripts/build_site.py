#!/usr/bin/env python3
"""
Static Web Reader Generator for Burmese Stories
Compiles markdown stories and assets into a responsive, mobile-first PWA-ready web reader.
"""

import os
import re
import json
import shutil
from html import escape as html_escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

try:
    from PIL import Image
except ImportError:
    Image = None

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
    "children": "#b45309",
    "folklore": "#15803d",
    "contemporary": "#1d4ed8",
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
  --accent-color: #c2410c;
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
img { max-width: 100%; height: auto; }
body {
  font-family: "Noto Sans Myanmar", "Pyidaungsu", -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-main);
  line-height: 1.8;
  transition: background-color 0.3s, color 0.3s;
  -webkit-text-size-adjust: 100%;
}

header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-color);
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.brand-link {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--accent-color);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
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
  white-space: nowrap;
  touch-action: manipulation;
}
.telegram-pill:hover { transform: scale(1.04); }

.theme-toggles {
  display: flex;
  gap: 6px;
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
  min-height: 36px;
  min-width: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
}

.container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px 16px 80px 16px;
}

.hero {
  text-align: center;
  padding: 24px 0 32px;
}
.hero h1 {
  font-size: clamp(1.6rem, 4vw, 2.3rem);
  color: var(--accent-color);
  margin-bottom: 8px;
  line-height: 1.35;
}
.hero p {
  color: var(--text-muted);
  font-size: clamp(0.95rem, 2vw, 1.1rem);
  max-width: 640px;
  margin: 0 auto;
  line-height: 1.6;
}

.filter-bar {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.filter-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: 24px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  touch-action: manipulation;
  white-space: nowrap;
}
.filter-btn.active, .filter-btn:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 24px;
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
  -webkit-backdrop-filter: blur(4px);
}

.btn-card-bookmark {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #ffffff;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 2;
  touch-action: manipulation;
}
.btn-card-bookmark:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}
.btn-card-bookmark.bookmarked {
  color: #f59e0b;
  background: rgba(15, 23, 42, 0.85);
  border-color: #f59e0b;
}

.card-read-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(4, 120, 87, 0.95);
  color: white;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 10px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}

.card-aigc-badge {
  position: absolute;
  bottom: 10px;
  left: 12px;
  background: rgba(15, 23, 42, 0.8);
  color: #fef3c7;
  border: 1px solid rgba(251, 191, 36, 0.55);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 10px;
  letter-spacing: 0.04em;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.reader-aigc-badge {
  display: inline-block;
  background: #1e293b;
  color: #fef3c7;
  border: 1px solid #f59e0b;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-left: 8px;
  vertical-align: middle;
}

.bookmark-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 600;
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  touch-action: manipulation;
  transition: all 0.2s;
}
.bookmark-btn:hover {
  border-color: var(--accent-color);
}
.bookmark-btn.bookmarked {
  color: #d97706;
  background: rgba(245, 158, 11, 0.12);
  border-color: #f59e0b;
}
[data-theme="dark"] .bookmark-btn.bookmarked {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.2);
}

.card-body {
  padding: 18px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-body h3 {
  font-size: 1.2rem;
  margin-bottom: 8px;
  line-height: 1.5;
  word-break: break-word;
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
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
}
.btn-pdf {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  touch-action: manipulation;
}

/* Reader Page Specific */
.reader-container {
  max-width: 780px;
  margin: 0 auto;
  padding: 24px 16px 80px 16px;
}

.reader-header {
  margin-bottom: 20px;
}

.reader-title {
  font-size: clamp(1.5rem, 4vw, 2.2rem);
  color: var(--accent-color);
  margin: 14px 0 8px;
  line-height: 1.35;
  word-break: break-word;
}

.reader-meta {
  color: var(--text-muted);
  font-size: clamp(0.85rem, 2vw, 1rem);
  margin-bottom: 20px;
}

.reader-cover {
  width: 100%;
  height: auto;
  border-radius: 16px;
  box-shadow: var(--shadow-md);
  margin-bottom: 28px;
  max-height: 480px;
  object-fit: cover;
}

.audio-player-box {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 12px 16px;
  margin-bottom: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}
.audio-player-label {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--accent-color);
}
.audio-player-box audio {
  flex: 1;
  min-width: 220px;
  height: 36px;
}

.reader-content p {
  font-size: var(--font-size, 1.15rem);
  line-height: 2.05;
  margin-bottom: 22px;
  text-align: left;
  word-break: break-word;
  overflow-wrap: break-word;
}

.section-title {
  font-size: clamp(1.2rem, 3vw, 1.35rem);
  color: var(--accent-color);
  margin: 32px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px dashed var(--border-color);
}

.moral-box {
  background: rgba(211, 84, 0, 0.08);
  border-left: 5px solid var(--accent-color);
  padding: 20px;
  border-radius: 12px;
  margin: 32px 0;
}
.moral-label {
  font-weight: bold;
  color: var(--accent-color);
  font-size: 1.1rem;
  margin-bottom: 8px;
}
.moral-content {
  font-size: var(--font-size, 1.15rem);
  line-height: 1.95;
  text-align: left;
  word-break: break-word;
}

.reader-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}

.reader-footer-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.watermark {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  font-size: clamp(2rem, 7vw, 4.5rem);
  font-weight: 800;
  color: var(--text-main);
  opacity: 0.035;
  pointer-events: none;
  user-select: none;
  white-space: nowrap;
  z-index: 0;
  letter-spacing: 4px;
}

.copyright-box {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 18px 20px;
  margin-top: 36px;
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.6;
  text-align: center;
}
.copyright-box strong {
  color: var(--text-main);
}
.copyright-box a {
  color: var(--accent-color);
  text-decoration: none;
}

.site-footer {
  text-align: center;
  padding: 32px 16px 40px;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.88rem;
  line-height: 1.7;
  margin-top: 48px;
}
.site-footer a {
  color: var(--accent-color);
  text-decoration: none;
}

/* Mobile Breakpoints & Responsive Adaptations */
@media (max-width: 680px) {
  header {
    padding: 10px 14px;
    gap: 8px;
  }
  .brand-link {
    font-size: 1.05rem;
  }
  .header-actions {
    gap: 6px;
  }
  .telegram-pill span {
    display: none;
  }
  .telegram-pill::after {
    content: "📢 Channel";
  }
  .telegram-pill {
    padding: 5px 10px;
    font-size: 0.8rem;
  }
  .theme-btn, .font-btn {
    padding: 4px 8px;
    min-width: 40px;
    min-height: 40px;
    font-size: 0.85rem;
  }
  .bookmark-btn .bookmark-text {
    display: none;
  }
  .bookmark-btn {
    padding: 4px 8px;
    min-width: 40px;
    min-height: 40px;
    font-size: 0.85rem;
  }
  .story-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .card-actions {
    flex-direction: column;
    gap: 8px;
  }
  .btn-read, .btn-pdf {
    width: 100%;
    text-align: center;
  }
  .reader-footer {
    flex-direction: column;
    align-items: stretch;
  }
  .reader-footer .btn-pdf {
    width: 100%;
    text-align: center;
  }
  .reader-footer-actions {
    flex-direction: column;
    width: 100%;
  }
  .reader-footer-actions .btn-pdf,
  .reader-footer-actions .telegram-pill {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 440px) {
  .brand-link {
    font-size: 0.95rem;
  }
  .telegram-pill::after {
    content: "📢";
  }
  .theme-toggles {
    gap: 4px;
  }
  .filter-btn {
    padding: 5px 10px;
    font-size: 0.82rem;
  }
  .moral-box {
    padding: 16px;
  }
}
"""

READER_JS = """
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('burmese_stories_theme', theme);
}

function adjustFontSize(delta) {
  let size = parseFloat(localStorage.getItem('burmese_stories_fontsize') || 1.15);
  size = Math.min(Math.max(size + delta, 0.9), 1.6);
  size = Math.round(size * 100) / 100;
  document.documentElement.style.setProperty('--font-size', size + 'rem');
  localStorage.setItem('burmese_stories_fontsize', size);
}

function getStoredArray(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || [];
  } catch (e) {
    return [];
  }
}

function setStoredArray(key, arr) {
  localStorage.setItem(key, JSON.stringify(arr));
}

function toggleBookmark(storyId, event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  let bookmarks = getStoredArray('bs_bookmarks');
  const idx = bookmarks.indexOf(storyId);
  if (idx >= 0) {
    bookmarks.splice(idx, 1);
  } else {
    bookmarks.push(storyId);
  }
  setStoredArray('bs_bookmarks', bookmarks);
  syncUI();

  const activeBtn = document.querySelector('.filter-btn.active');
  if (activeBtn && activeBtn.id === 'filter-btn-bookmarks') {
    filterStories('bookmarks', activeBtn);
  }
}

function markAsRead(storyId) {
  let readList = getStoredArray('bs_read');
  if (!readList.includes(storyId)) {
    readList.push(storyId);
    setStoredArray('bs_read', readList);
  }
}

function filterStories(filterType, btn) {
  if (btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  const bookmarks = getStoredArray('bs_bookmarks');
  const readList = getStoredArray('bs_read');
  let visibleCount = 0;

  document.querySelectorAll('.story-card').forEach(card => {
    const cat = card.getAttribute('data-category');
    const id = card.getAttribute('data-id');
    let show = false;

    if (filterType === 'all') {
      show = true;
    } else if (filterType === 'bookmarks') {
      show = bookmarks.includes(id);
    } else if (filterType === 'unread') {
      show = !readList.includes(id);
    } else if (filterType === 'read') {
      show = readList.includes(id);
    } else if (cat === filterType) {
      show = true;
    }

    if (show) {
      card.style.display = 'flex';
      visibleCount++;
    } else {
      card.style.display = 'none';
    }
  });

  const emptyMsg = document.getElementById('empty-filter-msg');
  if (emptyMsg) {
    emptyMsg.style.display = visibleCount === 0 ? 'block' : 'none';
  }
}

function filterCategory(cat, btn) {
  filterStories(cat, btn);
}

function syncUI() {
  const bookmarks = getStoredArray('bs_bookmarks');
  const readList = getStoredArray('bs_read');

  document.querySelectorAll('.story-card').forEach(card => {
    const id = card.getAttribute('data-id');
    const bmBtn = card.querySelector('.btn-card-bookmark');
    if (bmBtn) {
      if (bookmarks.includes(id)) {
        bmBtn.classList.add('bookmarked');
        bmBtn.innerHTML = '★';
        bmBtn.setAttribute('title', 'မှတ်သားထားပြီး (ဖယ်ရှားရန် နှိပ်ပါ)');
      } else {
        bmBtn.classList.remove('bookmarked');
        bmBtn.innerHTML = '☆';
        bmBtn.setAttribute('title', 'မှတ်သားထားမည်');
      }
    }
    const readBadge = card.querySelector('.card-read-badge');
    if (readBadge) {
      readBadge.style.display = readList.includes(id) ? 'inline-block' : 'none';
    }
  });

  const countSpan = document.getElementById('bookmark-count');
  if (countSpan) {
    countSpan.textContent = bookmarks.length;
  }

  const readerBtn = document.getElementById('reader-bookmark-btn');
  if (readerBtn) {
    const storyId = readerBtn.getAttribute('data-id');
    const icon = document.getElementById('reader-star-icon');
    const text = readerBtn.querySelector('.bookmark-text');
    if (bookmarks.includes(storyId)) {
      readerBtn.classList.add('bookmarked');
      if (icon) icon.textContent = '★';
      if (text) text.textContent = 'မှတ်သားပြီး';
    } else {
      readerBtn.classList.remove('bookmarked');
      if (icon) icon.textContent = '☆';
      if (text) text.textContent = 'မှတ်သားမည်';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('burmese_stories_theme') || 'light';
  setTheme(savedTheme);
  const savedSize = localStorage.getItem('burmese_stories_fontsize');
  if (savedSize) {
    document.documentElement.style.setProperty('--font-size', savedSize + 'rem');
  }
  syncUI();
});
"""

FONT_LINKS_HTML = """  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&display=swap" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&display=swap" rel="stylesheet"></noscript>"""


def optimize_illustrations(dist_illustrations_dir):
    """Build 640w card and full-size WebP variants in dist; fallback to PNG if Pillow missing."""
    variants = {}
    if not dist_illustrations_dir.exists():
        return variants
    for png_path in sorted(dist_illustrations_dir.glob("*.png")):
        rel_png = f"assets/illustrations/{png_path.name}"
        if Image is None:
            variants[rel_png] = {"card": rel_png, "reader": rel_png, "w": 1200, "h": 896, "cw": 640, "ch": 478}
            continue
        with Image.open(png_path) as im:
            w, h = im.size
            rgb = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im
            reader_name = f"{png_path.stem}.webp"
            card_name = f"{png_path.stem}-640.webp"
            rgb.save(dist_illustrations_dir / reader_name, "WEBP", quality=82, method=6)
            cw = min(640, w)
            ch = round(h * (cw / w))
            card_im = rgb.resize((cw, ch), Image.Resampling.LANCZOS) if w > 640 else rgb
            card_im.save(dist_illustrations_dir / card_name, "WEBP", quality=80, method=6)
        png_path.unlink()
        variants[rel_png] = {
            "card": f"assets/illustrations/{card_name}",
            "reader": f"assets/illustrations/{reader_name}",
            "w": w, "h": h, "cw": cw, "ch": ch,
        }
    return variants


def generate_catalog_html(stories, base_url, img_variants):
    cards_html = []
    for idx, s in enumerate(stories):
        meta = s["meta"]
        story_id = meta.get("id", s["slug"])
        cat_key = s["category"]
        cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
        cat_color = CATEGORY_COLORS.get(cat_key, "#333")
        author = meta.get("author", "Asap Money")
        label = meta.get("label", "").strip()
        aigc_card_badge = f'<span class="card-aigc-badge">✨ {label}</span>' if label else ""
        has_audio = (ASSETS_DIR / "audio" / f"{story_id}.mp3").exists()
        audio_meta_tag = " • 🎧 အသံပါ" if has_audio else ""
        created_at = meta.get("created_at", "")
        iv = img_variants.get(s["img_web_path"], {"card": s["img_web_path"], "cw": 640, "ch": 478})
        img_attrs = 'loading="eager" fetchpriority="high"' if idx == 0 else 'loading="lazy"'

        pdf_filename = f"{s['slug']}.pdf" if s['slug'].startswith(meta.get('id', '')) else f"{meta.get('id')}-{s['slug']}.pdf"
        cards_html.append(f"""
        <div class="story-card" data-category="{cat_key}" data-id="{story_id}">
          <div class="card-img-wrapper">
            <span class="card-badge" style="background: {cat_color}">{cat_name}</span>
            <button class="btn-card-bookmark" onclick="toggleBookmark('{story_id}', event)" title="မှတ်သားထားမည်" aria-label="Bookmark">☆</button>
            <span class="card-read-badge" style="display: none;">✓ ဖတ်ပြီး</span>
            {aigc_card_badge}
            <img src="{iv['card']}" alt="{html_escape(meta.get('title_my', ''), quote=True)}" width="{iv['cw']}" height="{iv['ch']}" {img_attrs} decoding="async" />
          </div>
          <div class="card-body">
            <h3>{meta.get('title_my', '')}</h3>
            <div class="card-meta">
              ✍️ <strong>{author}</strong> • 📅 {created_at} • 🎯 {meta.get('target_audience', 'All Ages')}{audio_meta_tag}
            </div>
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
  <link rel="canonical" href="{html_escape(base_url, quote=True)}/">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <meta name="description" content="ကလေးလူငယ်များနှင့် မိဘဆရာများအတွက် အသိပညာပေး မူရင်းမြန်မာပုံပြင်များ">
{FONT_LINKS_HTML}
  <style>{BASE_CSS}</style>
</head>
<body>
  <header>
    <a href="./" class="brand-link">📖 မြန်မာပုံပြင်များ</a>
    <div class="header-actions">
      <a href="https://t.me/stellarpub_official" target="_blank" class="telegram-pill">
        <span>📢 @stellarpub_official</span>
      </a>
      <div class="theme-toggles">
        <button class="theme-btn" onclick="setTheme('light')" title="Light mode">☀️</button>
        <button class="theme-btn" onclick="setTheme('sepia')" title="Sepia mode">📜</button>
        <button class="theme-btn" onclick="setTheme('dark')" title="Dark mode">🌙</button>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="hero">
      <h1>မြန်မာပုံပြင်များ စုစည်းမှု</h1>
      <p>ဘဝအတွက် အဖိုးတန်သော အတွေးအမြင်နှင့် သင်ခန်းစာများ ပေးစွမ်းနိုင်မည့် ပုံပြင်များ</p>
    </div>

    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterStories('all', this)">အားလုံး ({len(stories)})</button>
      <button class="filter-btn" onclick="filterStories('children', this)">ကလေးပုံပြင်များ</button>
      <button class="filter-btn" onclick="filterStories('folklore', this)">ရိုးရာနှင့် ဒဏ္ဍာရီများ</button>
      <button class="filter-btn" onclick="filterStories('contemporary', this)">ခေတ်ပေါ်ပုံပြင်များ</button>
      <button class="filter-btn" id="filter-btn-bookmarks" onclick="filterStories('bookmarks', this)">⭐ မှတ်သားထားသည် (<span id="bookmark-count">0</span>)</button>
      <button class="filter-btn" id="filter-btn-unread" onclick="filterStories('unread', this)">📖 မဖတ်ရသေး</button>
    </div>

    <div id="empty-filter-msg" style="display: none; text-align: center; padding: 48px 16px; color: var(--text-muted);">
      <p style="font-size: 1.25rem; margin-bottom: 8px;">📭 မည်သည့်ပုံပြင်မျှ မရှိသေးပါ။</p>
      <p style="font-size: 0.95rem;">ကြိုက်နှစ်သက်သော ပုံပြင်များကို ⭐ နှိပ်၍ မှတ်သားထားနိုင်ပါသည်။</p>
    </div>

    <div class="story-grid">
      {''.join(cards_html)}
    </div>

    <footer class="site-footer">
      <p>မူပိုင်ခွင့် © 2026 <strong>Asap Money</strong> / StellarPub (@stellarpub_official)။ All rights reserved.</p>
      <p>ဤပုံပြင်များကို <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank">Creative Commons CC BY-NC-ND 4.0</a> ဖြင့် ထုတ်ဝေဖြန့်ချိပါသည်။ • Channel: <a href="https://t.me/stellarpub_official" target="_blank">@stellarpub_official</a></p>
    </footer>
  </div>

  <script>{READER_JS}</script>
</body>
</html>
"""

def generate_story_html(story, base_url, img_variants):
    meta = story["meta"]
    story_id = meta.get("id", story["slug"])
    body_html = render_markdown_to_html(story["body"])
    cat_key = story["category"]
    cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
    cat_color = CATEGORY_COLORS.get(cat_key, "#333")
    author = meta.get("author", "Asap Money")
    label = meta.get("label", "").strip()
    aigc_reader_badge = f'<span class="reader-aigc-badge">✨ {label}</span>' if label else ""
    has_audio = (ASSETS_DIR / "audio" / f"{story_id}.mp3").exists()
    audio_player_html = (
        f'<div class="audio-player-box">'
        f'<div class="audio-player-label">🎧 အသံဖြင့် နားဆင်ရန်</div>'
        f'<audio controls preload="none" src="../assets/audio/{story_id}.mp3"></audio>'
        f'</div>'
        if has_audio
        else ""
    )
    created_at = meta.get("created_at", "")
    pub_year = created_at[:4] if len(created_at) >= 4 else "2026"
    pdf_filename = f"{story['slug']}.pdf" if story['slug'].startswith(meta.get('id', '')) else f"{meta.get('id')}-{story['slug']}.pdf"
    iv = img_variants.get(story["img_web_path"], {"reader": story["img_web_path"], "w": 1200, "h": 896})
    desc = html_escape(str(meta.get("lesson") or meta.get("title_my", "")), quote=True)
    canonical = html_escape(f"{base_url}/stories/{story['slug']}.html", quote=True)

    return f"""<!DOCTYPE html>
<html lang="my">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{meta.get('title_my', '')} — မြန်မာပုံပြင်များ</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" href="/favicon.ico" sizes="any">
{FONT_LINKS_HTML}
  <style>{BASE_CSS}</style>
</head>
<body>
  <div class="watermark">{author} • StellarPub</div>

  <header>
    <a href="../" class="brand-link">← ပုံပြင်များသို့ ပြန်သွားရန်</a>
    <div class="header-actions">
      <button class="bookmark-btn" id="reader-bookmark-btn" data-id="{story_id}" onclick="toggleBookmark('{story_id}', event)" title="မှတ်သားမည်">
        <span id="reader-star-icon">☆</span> <span class="bookmark-text">မှတ်သားမည်</span>
      </button>
      <button class="font-btn" onclick="adjustFontSize(-0.1)" title="Smaller font">A-</button>
      <button class="font-btn" onclick="adjustFontSize(0.1)" title="Larger font">A+</button>
      <div class="theme-toggles">
        <button class="theme-btn" onclick="setTheme('light')" title="Light mode">☀️</button>
        <button class="theme-btn" onclick="setTheme('sepia')" title="Sepia mode">📜</button>
        <button class="theme-btn" onclick="setTheme('dark')" title="Dark mode">🌙</button>
      </div>
    </div>
  </header>

  <div class="reader-container">
    <div class="reader-header">
      <span style="background: {cat_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
        {cat_name}
      </span>{aigc_reader_badge}
      <h1 class="reader-title">{meta.get('title_my', '')}</h1>
      <div class="reader-meta">
        ✍️ ဖန်တီးရေးသားသူ: <strong>{author}</strong> • 📅 ထုတ်ဝေသည့်ရက်: <strong>{created_at}</strong> • 🎯 ပရိသတ်: <strong>{meta.get('target_audience', 'All Ages')}</strong>
      </div>
    </div>

    <img src="../{iv['reader']}" alt="{html_escape(meta.get('title_my', ''), quote=True)}" width="{iv['w']}" height="{iv['h']}" loading="eager" fetchpriority="high" decoding="async" class="reader-cover" />

    {audio_player_html}

    <div class="reader-content">
      {body_html}
    </div>

    <div class="copyright-box">
      <p><strong>မူပိုင်ခွင့် © {pub_year} {author} / StellarPub (@stellarpub_official)</strong></p>
      <p>ဤမူရင်းပုံပြင်နှင့် သရုပ်ဖော်ပုံများကို <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank">Creative Commons CC BY-NC-ND 4.0</a> အောက်တွင် လွတ်လပ်စွာ မျှဝေဖတ်ရှုနိုင်ပါသည်။ စီးပွားဖြစ် ကူးယူရောင်းချခြင်း မပြုရ။</p>
    </div>

    <div class="reader-footer">
      <a href="../" class="btn-pdf">← ပုံပြင်အားလုံး ကြည့်ရှုရန်</a>
      <div class="reader-footer-actions">
        <a href="../pdf/{pdf_filename}" class="btn-pdf" download>📄 A4 Print PDF ဒေါင်းလုဒ်</a>
        <a href="https://t.me/stellarpub_official" target="_blank" class="telegram-pill">📢 @stellarpub_official</a>
      </div>
    </div>
  </div>

  <script>
    {READER_JS}
    markAsRead('{story_id}');
  </script>
</body>
</html>
"""

def generate_sitemap_xml(stories, base_url):
    """Build XML sitemap for catalog root and all story pages."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{xml_escape(base_url)}/</loc>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]
    for s in stories:
        loc = xml_escape(f"{base_url}/stories/{s['slug']}.html")
        created_at = str(s["meta"].get("created_at", "")).strip()
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", created_at):
            lines.append(f"    <lastmod>{created_at}</lastmod>")
        lines.append("    <priority>0.8</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def generate_robots_txt(base_url):
    """Build robots.txt pointing crawlers to sitemap.xml."""
    return f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n"


def main():
    print("Building Web Reader...")
    # Prepare dist directory
    if DIST_SITE.exists():
        shutil.rmtree(DIST_SITE)
    DIST_SITE.mkdir(parents=True, exist_ok=True)
    (DIST_SITE / "stories").mkdir(parents=True, exist_ok=True)
    (DIST_SITE / "pdf").mkdir(parents=True, exist_ok=True)
    
    # Copy assets and build WebP variants
    shutil.copytree(ASSETS_DIR, DIST_SITE / "assets")
    img_variants = optimize_illustrations(DIST_SITE / "assets" / "illustrations")
    for icon_name in ("favicon.ico", "favicon.svg"):
        icon_src = ASSETS_DIR / icon_name
        if icon_src.exists():
            shutil.copy(icon_src, DIST_SITE / icon_name)

    # Copy DLC assets if present
    dlc_src = REPO_ROOT / "dlc"
    if dlc_src.exists():
        shutil.copytree(dlc_src, DIST_SITE / "dlc")

    # Resolve custom domain early for canonical + sitemap URLs
    cname_file = REPO_ROOT / "CNAME"
    if cname_file.exists():
        domain = cname_file.read_text(encoding="utf-8").strip() or "stellarpub.celestrionx.com"
        shutil.copy(cname_file, DIST_SITE / "CNAME")
    else:
        domain = "stellarpub.celestrionx.com"
        (DIST_SITE / "CNAME").write_text(f"{domain}\n", encoding="utf-8")
    base_url = f"https://{domain}"
    
    stories = get_stories()
    print(f"Loaded {len(stories)} stories.")
    
    # Build index.html
    index_html = generate_catalog_html(stories, base_url, img_variants)
    (DIST_SITE / "index.html").write_text(index_html, encoding="utf-8")
    
    # Build story pages
    for s in stories:
        story_html = generate_story_html(s, base_url, img_variants)
        (DIST_SITE / "stories" / f"{s['slug']}.html").write_text(story_html, encoding="utf-8")

    (DIST_SITE / "sitemap.xml").write_text(generate_sitemap_xml(stories, base_url), encoding="utf-8")
    (DIST_SITE / "robots.txt").write_text(generate_robots_txt(base_url), encoding="utf-8")

    print(f"Web reader successfully generated at {DIST_SITE}")

if __name__ == "__main__":
    main()
