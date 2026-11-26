#!/usr/bin/env python3
"""
PDF Storybook Compiler for Burmese Stories
Compiles markdown stories + illustrations into print-ready A4 landscape PDF decks via headless Chromium.
"""

import os
import re
import sys
import subprocess
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"
ASSETS_DIR = REPO_ROOT / "assets"
DIST_PDF = REPO_ROOT / "dist" / "pdf"
DIST_SITE_PDF = REPO_ROOT / "dist" / "site" / "pdf"

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
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body

def find_chromium():
    for cmd in ["chromium", "google-chrome", "chromium-browser"]:
        path = shutil.which(cmd)
        if path:
            return path
    return None

def build_pdf_for_story(md_path, chromium_bin):
    content = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    story_id = meta.get("id", "BS-000")
    slug = md_path.stem
    title = meta.get("title_my", "")
    title_en = meta.get("title_en", "")
    author = meta.get("author", "Asap Money")
    label = meta.get("label", "").strip()
    aigc_badge_html = f'<span class="aigc-badge">✨ {label}</span>' if label else ""
    created_at = meta.get("created_at", "")
    lesson = meta.get("lesson", "")
    category = meta.get("category", "children")

    # Image path
    img_match = re.search(r"!\[.*?\]\((.*?)\)", body)
    if img_match:
        img_rel = img_match.group(1)
        img_abs = (md_path.parent / img_rel).resolve()
        img_url = f"file://{img_abs}"
    else:
        img_url = ""

    # Clean story text
    clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    clean_body = re.sub(r"^#\s+.*$", "", clean_body, flags=re.MULTILINE)
    
    # Extract beats
    beats = []
    current_title = ""
    current_paras = []
    
    for line in clean_body.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            if current_title or current_paras:
                beats.append((current_title, "\n".join(current_paras)))
                current_paras = []
            current_title = line.replace("## ", "").strip()
        elif line:
            current_paras.append(line)
    if current_title or current_paras:
        beats.append((current_title, "\n".join(current_paras)))

    author_escaped = author.replace('"', '\\"').replace("'", "\\'")
    footer_text = f"© 2026 {author_escaped} / StellarPub (@stellarpub_official) • CC BY-NC-ND 4.0 • {created_at}"

    # Generate print HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: A4 landscape;
  margin: 14mm 18mm 14mm 18mm;
  @bottom-left {{
    content: "{footer_text}";
    font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }}
  @bottom-right {{
    content: counter(page) " / " counter(pages);
    font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }}
}}
@page :first {{
  @bottom-left {{ content: ""; }}
  @bottom-right {{ content: ""; }}
}}
body {{
  font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
  color: #1a1a24;
  background: #ffffff;
  margin: 0;
  padding: 0;
  line-height: 1.85;
}}

.pdf-watermark {{
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-25deg);
  font-size: 38pt;
  font-weight: 800;
  color: rgba(140, 150, 165, 0.06);
  pointer-events: none;
  user-select: none;
  white-space: nowrap;
  letter-spacing: 5px;
  z-index: -1;
}}

/* Page 1: Cover */
.cover-page {{
  page-break-after: always;
  break-after: page;
  height: 175mm;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 24px;
  box-sizing: border-box;
}}
.cover-img-box {{
  width: 55%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.cover-img-box img {{
  max-width: 100%;
  max-height: 165mm;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}}
.cover-text-box {{
  width: 45%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.channel-badge {{
  display: inline-block;
  background: #0088cc;
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 11pt;
  font-weight: bold;
  margin-bottom: 20px;
}}
.aigc-badge {{
  display: inline-block;
  background: #1e293b;
  color: #fef3c7;
  border: 1px solid #f59e0b;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 10pt;
  font-weight: bold;
  margin-left: 8px;
  margin-bottom: 20px;
}}
h1 {{
  font-size: 26pt;
  color: #8b2500;
  line-height: 1.4;
  margin: 0 0 10px 0;
}}
.subtitle {{
  font-size: 13pt;
  color: #64748b;
  margin-bottom: 24px;
}}
.meta-tag {{
  font-size: 11pt;
  color: #475569;
  background: #f1f5f9;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}}

/* Narrative Pages */
.story-page {{
  columns: 2;
  column-gap: 32px;
  font-size: 11pt;
  text-align: justify;
}}
p {{
  margin: 0 0 13px 0;
  line-height: 1.85;
  text-indent: 1.5em;
}}

/* Moral Section */
.moral-container {{
  break-inside: avoid;
  background: #fff8f0;
  border-left: 5px solid #d35400;
  padding: 14px 18px;
  border-radius: 8px;
  margin-top: 16px;
}}
.moral-heading {{
  font-weight: bold;
  color: #d35400;
  font-size: 12pt;
  margin-bottom: 4px;
}}
</style>
</head>
<body>

<!-- Cover Page -->
<div class="cover-page">
  <div class="cover-img-box">
    <img src="{img_url}" />
  </div>
  <div class="cover-text-box">
    <div><span class="channel-badge">📢 Telegram: @stellarpub_official</span>{aigc_badge_html}</div>
    <h1>{title}</h1>
    <div class="subtitle">{title_en}</div>
    <div class="meta-tag"><strong>စာရေးသူ:</strong> {author}</div>
    <div class="meta-tag"><strong>ID:</strong> {story_id} • <strong>ကဏ္ဍ:</strong> {category}</div>
    <div class="meta-tag"><strong>ပရိသတ်:</strong> {meta.get('target_audience', 'All Ages')}</div>
    <div class="meta-tag"><strong>ထုတ်ဝေသည့်ရက်:</strong> {created_at}</div>
    <div class="meta-tag" style="background: #fdf2e9; color: #7c2d12; border: 1px solid #fed7aa; font-size: 9.5pt;">
      <strong>မူပိုင်ခွင့်:</strong> © 2026 {author} / StellarPub (@stellarpub_official) • CC BY-NC-ND 4.0
    </div>
  </div>
</div>

<!-- Narrative Page Flow -->
<div class="pdf-watermark">{author} • StellarPub</div>
<div class="story-page">
"""

    for b_title, b_text in beats:
        if "သင်ခန်းစာ" in b_title:
            continue
        for p in b_text.split("\n"):
            p = p.strip()
            if p:
                html_content += f"<p>{p}</p>\n"

    html_content += f"""
    <div class="moral-container">
      <div class="moral-heading">✨ သင်ခန်းစာ (Life Lesson)</div>
      <div style="font-size: 11pt; line-height: 1.7;">{lesson}</div>
    </div>
  </div>

</body>
</html>
"""

    temp_html = REPO_ROOT / f".temp_{slug}.html"
    temp_html.write_text(html_content, encoding="utf-8")

    pdf_name = f"{slug}.pdf" if slug.startswith(story_id) else f"{story_id}-{slug}.pdf"
    out_pdf = DIST_PDF / pdf_name
    cmd = [
        chromium_bin,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf}",
        str(temp_html)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_html.exists():
        temp_html.unlink()

    # Copy to site
    if DIST_SITE_PDF.exists():
        shutil.copy(out_pdf, DIST_SITE_PDF / pdf_name)

    print(f"Generated PDF: {out_pdf.name}")

def main():
    print("Building PDF Storybooks...")
    chromium_bin = find_chromium()
    if not chromium_bin:
        print("Error: Chromium not found on system.")
        sys.exit(1)

    DIST_PDF.mkdir(parents=True, exist_ok=True)
    DIST_SITE_PDF.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
            continue
        build_pdf_for_story(md_file, chromium_bin)

    print("All PDFs successfully built.")

if __name__ == "__main__":
    main()
