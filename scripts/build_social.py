#!/usr/bin/env python3
"""
Social Media Packet & Carousel Generator for Burmese Stories
Generates 1080x1080 square carousel cards and formatted Telegram broadcast copy for @stellarpub_official.
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
DIST_SOCIAL = REPO_ROOT / "dist" / "social"

CATEGORY_NAMES = {
    "children": "ကလေးပုံပြင်",
    "folklore": "ရိုးရာဒဏ္ဍာရီ",
    "contemporary": "ခေတ်ပေါ်ပုံပြင်",
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
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body

def find_chromium():
    for cmd in ["chromium", "google-chrome", "chromium-browser"]:
        path = shutil.which(cmd)
        if path:
            return path
    return None

def generate_social_cards(md_path, chromium_bin):
    content = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    story_id = meta.get("id", "BS-000")
    slug = md_path.stem
    title = meta.get("title_my", "")
    title_en = meta.get("title_en", "")
    lesson = meta.get("lesson", "")
    category = meta.get("category", "children")
    cat_label = CATEGORY_NAMES.get(category, category)

    img_match = re.search(r"!\[.*?\]\((.*?)\)", body)
    if img_match:
        img_rel = img_match.group(1)
        img_abs = (md_path.parent / img_rel).resolve()
        img_url = f"file://{img_abs}"
    else:
        img_url = ""

    # Clean story text and extract first two paragraphs
    clean_body = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    clean_body = re.sub(r"^#.*$", "", clean_body, flags=re.MULTILINE)
    clean_body = re.sub(r"^##.*$", "", clean_body, flags=re.MULTILINE)
    paras = [p.strip() for p in clean_body.split("\n\n") if p.strip() and not p.strip().startswith("---")]
    
    teaser_para_1 = paras[0] if len(paras) > 0 else ""
    teaser_para_2 = paras[1] if len(paras) > 1 else ""

    story_social_dir = DIST_SOCIAL / story_id
    story_social_dir.mkdir(parents=True, exist_ok=True)

    # 1. Slide 1: Cover Card
    slide1_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  margin: 0; padding: 0;
  width: 1080px; height: 1080px;
  font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
  background: #0f172a;
  color: white;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}}
.bg-image {{
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 680px;
  background-image: url('{img_url}');
  background-size: cover;
  background-position: center;
}}
.gradient-overlay {{
  position: absolute;
  top: 400px; left: 0;
  width: 100%; height: 320px;
  background: linear-gradient(to bottom, transparent, #0f172a);
}}
.top-bar {{
  position: absolute;
  top: 40px; left: 50px; right: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}}
.badge {{
  background: rgba(230, 126, 34, 0.95);
  color: white;
  padding: 10px 24px;
  border-radius: 30px;
  font-size: 26px;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}}
.channel-pill {{
  background: rgba(0, 136, 204, 0.95);
  color: white;
  padding: 10px 24px;
  border-radius: 30px;
  font-size: 26px;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}}
.bottom-content {{
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 420px;
  background: #0f172a;
  padding: 20px 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
h1 {{
  font-size: 52px;
  line-height: 1.35;
  color: #fbbf24;
  margin: 0 0 10px 0;
}}
.en-title {{
  font-size: 28px;
  color: #94a3b8;
  margin-bottom: 20px;
}}
.footer-text {{
  display: flex;
  justify-content: space-between;
  font-size: 24px;
  color: #64748b;
  border-top: 1px solid #334155;
  padding-top: 16px;
}}
</style>
</head>
<body>
<div class="bg-image"></div>
<div class="gradient-overlay"></div>
<div class="top-bar">
  <span class="badge">{cat_label}</span>
  <span class="channel-pill">📢 @stellarpub_official</span>
</div>
<div class="bottom-content">
  <div>
    <h1>{title}</h1>
    <div class="en-title">{title_en}</div>
  </div>
  <div class="footer-text">
    <span>Burmese Stories Series</span>
    <span>Slide 1 / 3 →</span>
  </div>
</div>
</body>
</html>
"""

    # 2. Slide 2: Excerpt / Story Teaser
    slide2_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  margin: 0; padding: 60px;
  width: 960px; height: 960px;
  font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
  background: #1e293b;
  color: #f1f5f9;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #334155;
  padding-bottom: 24px;
}}
.story-tag {{
  font-size: 32px;
  color: #fbbf24;
  font-weight: bold;
}}
.channel {{
  font-size: 28px;
  color: #38bdf8;
  font-weight: bold;
}}
.text-body {{
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px 0;
}}
p {{
  font-size: 34px;
  line-height: 1.85;
  margin: 0 0 24px 0;
  color: #e2e8f0;
  text-align: justify;
}}
.footer {{
  display: flex;
  justify-content: space-between;
  font-size: 24px;
  color: #64748b;
  border-top: 1px solid #334155;
  padding-top: 20px;
}}
</style>
</head>
<body>
<div class="top">
  <span class="story-tag">📖 {title}</span>
  <span class="channel">@stellarpub_official</span>
</div>
<div class="text-body">
  <p>{teaser_para_1}</p>
  <p>{teaser_para_2}</p>
</div>
<div class="footer">
  <span>Burmese Stories Collection</span>
  <span>Slide 2 / 3 →</span>
</div>
</body>
</html>
"""

    # 3. Slide 3: Moral Card
    slide3_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  margin: 0; padding: 60px;
  width: 960px; height: 960px;
  font-family: "Noto Sans Myanmar", "Pyidaungsu", sans-serif;
  background: #0f172a;
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 12px solid #e67e22;
  box-sizing: border-box;
}}
.top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.badge {{
  background: #e67e22;
  color: white;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 26px;
  font-weight: bold;
}}
.channel {{
  font-size: 30px;
  color: #38bdf8;
  font-weight: bold;
}}
.center-box {{
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 20px;
}}
.moral-title {{
  font-size: 38px;
  color: #f59e0b;
  margin-bottom: 24px;
  font-weight: bold;
}}
.moral-text {{
  font-size: 44px;
  line-height: 1.7;
  color: #ffffff;
  font-weight: 600;
}}
.link-box {{
  background: #1e293b;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  font-size: 26px;
  color: #94a3b8;
}}
.link-box strong {{
  color: #38bdf8;
}}
</style>
</head>
<body>
<div class="top">
  <span class="badge">အဓိက သင်ခန်းစာ</span>
  <span class="channel">📢 @stellarpub_official</span>
</div>
<div class="center-box">
  <div class="moral-title">✨ သင်ခန်းစာ (Lesson) ✨</div>
  <div class="moral-text">"{lesson}"</div>
</div>
<div class="link-box">
  📖 ဇာတ်လမ်းအပြည့်အစုံ ဖတ်ရှုရန် & PDF ဒေါင်းလုဒ်:<br>
  <strong>https://winphay.github.io/burmese-stories/stories/{slug}.html</strong>
</div>
</body>
</html>
"""

    slides = [
        ("slide_01_cover.png", slide1_html),
        ("slide_02_story.png", slide2_html),
        ("slide_03_lesson.png", slide3_html),
    ]

    for fname, html in slides:
        tmp_f = REPO_ROOT / f".tmp_{fname}.html"
        tmp_f.write_text(html, encoding="utf-8")
        out_img = story_social_dir / fname
        cmd = [
            chromium_bin,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--window-size=1080,1080",
            f"--screenshot={out_img}",
            str(tmp_f)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if tmp_f.exists():
            tmp_f.unlink()

    print(f"Generated 3 social cards for {story_id} in {story_social_dir}")

def generate_telegram_broadcast_markdown(stories):
    lines = ["# Telegram Broadcast Post Templates (@stellarpub_official)\n"]
    lines.append("> Copy and paste directly into Telegram Channel `@stellarpub_official`.\n\n---\n")

    for s in stories:
        meta = s["meta"]
        slug = s["slug"]
        story_id = meta.get("id", "BS-000")
        title = meta.get("title_my", "")
        title_en = meta.get("title_en", "")
        lesson = meta.get("lesson", "")
        cat_name = CATEGORY_NAMES.get(s["category"], s["category"])

        pdf_name = f"{slug}.pdf" if slug.startswith(story_id) else f"{story_id}-{slug}.pdf"
        post = f"""## 📢 Post Template: {story_id} — {title}

**Photo attachment:** Attach `dist/social/{story_id}/slide_01_cover.png` (or 3-photo carousel: `slide_01`, `slide_02`, `slide_03`).

**Caption:**
```text
📖 {title}
({title_en})

ကဏ္ဍ - {cat_name}
ပစ်မှတ်စာဖတ်သူ - {meta.get('target_audience', 'All Ages')}

✨ သင်ခန်းစာ:
"{lesson}"

─────────────────────
🌟 ပုံပြင်အပြည့်အစုံကို Web တွင် သက်တောင့်သက်သာ ဖတ်ရှုရန်:
🔗 https://winphay.github.io/burmese-stories/stories/{slug}.html

📄 A4 Print PDF ရယူရန်:
🔗 https://winphay.github.io/burmese-stories/pdf/{pdf_name}

📢 Telegram Channel: @stellarpub_official
#BurmeseStories #မြန်မာပုံပြင်များ #{meta.get('category', 'story')} #StellarPub
```

---
"""
        lines.append(post)

    out_file = DIST_SOCIAL / "telegram_posts.md"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated Telegram post packet at {out_file}")

def main():
    print("Building Social Media Packets...")
    chromium_bin = find_chromium()
    if not chromium_bin:
        print("Error: Chromium not found.")
        sys.exit(1)

    DIST_SOCIAL.mkdir(parents=True, exist_ok=True)
    stories = []

    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
            continue
        generate_social_cards(md_file, chromium_bin)
        content = md_file.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(content)
        stories.append({
            "meta": meta,
            "slug": md_file.stem,
            "category": meta.get("category", "children")
        })

    generate_telegram_broadcast_markdown(stories)
    print("All social media packets successfully built.")

if __name__ == "__main__":
    main()
