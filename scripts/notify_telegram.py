#!/usr/bin/env python3
"""
Telegram Channel Notification CLI for Burmese Stories
Zero-dependency script to broadcast story notifications and cover artwork to Telegram channels.
"""

import os
import re
import sys
import json
import uuid
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"
ASSETS_DIR = REPO_ROOT / "assets" / "illustrations"
CATALOG_PATH = REPO_ROOT / "CATALOG.md"
ENV_PATH = REPO_ROOT / ".env"

CATEGORY_NAMES = {
    "children": "ကလေးပုံပြင်",
    "folklore": "ရိုးရာဒဏ္ဍာရီ",
    "contemporary": "ခေတ်ပေါ်ပုံပြင်",
}

def load_env_file():
    """Load key-value pairs from .env into os.environ if present."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

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

def get_all_stories():
    stories = []
    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
            continue
        content = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        story_id = meta.get("id")
        if not story_id:
            continue
        stories.append({
            "id": story_id,
            "path": md_file,
            "meta": meta,
            "body": body,
            "slug": md_file.stem
        })
    stories.sort(key=lambda s: s["id"])
    return stories

def find_illustration(story):
    # 1. Search markdown body image syntax
    img_match = re.search(r"!\[.*?\]\((.*?)\)", story["body"])
    if img_match:
        img_rel = img_match.group(1)
        img_path = (story["path"].parent / img_rel).resolve()
        if img_path.exists():
            return img_path
    
    # 2. Search assets/illustrations by ID
    for candidate in ASSETS_DIR.glob(f"{story['id']}*"):
        if candidate.is_file() and candidate.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            return candidate
            
    return None

def build_telegram_caption(story):
    meta = story["meta"]
    slug = story["slug"]
    story_id = story["id"]
    title_my = meta.get("title_my", "ခေါင်းစဉ်မဲ့ ပုံပြင်")
    title_en = meta.get("title_en", "")
    category = meta.get("category", "children")
    cat_label = CATEGORY_NAMES.get(category, category)
    target_audience = meta.get("target_audience", "All Ages")
    lesson = meta.get("lesson", "")

    title_en_line = f"<i>{title_en}</i>\n" if title_en else ""
    
    caption = (
        f"✨ <b>{title_my}</b> ({story_id})\n"
        f"{title_en_line}"
        f"🏷️ အမျိုးအစား: <b>{cat_label}</b> | {target_audience}\n\n"
        f"💡 <b>သင်ခန်းစာ:</b>\n"
        f"« {lesson} »\n\n"
        f"─────────────────────\n"
        f"📖 <b>Web တွင် ဖတ်ရှုရန်:</b>\n"
        f"🔗 https://stellarpub.celestrionx.com/stories/{slug}.html\n\n"
        f"📄 <b>A4 Print PDF ရယူရန်:</b>\n"
        f"🔗 https://stellarpub.celestrionx.com/pdf/{slug}.pdf\n\n"
        f"📢 Telegram Channel: @stellarpub_official\n"
        f"#BurmeseStories #မြန်မာပုံပြင်များ #{category} #StellarPub"
    )
    return caption

def send_telegram_photo(token, chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    
    body = bytearray()
    
    def add_field(name, value):
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))
        
    def add_file(name, filepath):
        filename = filepath.name
        mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        body.extend(filepath.read_bytes())
        body.extend(b"\r\n")
        
    add_field("chat_id", chat_id)
    add_field("caption", caption)
    add_field("parse_mode", "HTML")
    add_file("photo", photo_path)
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    load_env_file()

    parser = argparse.ArgumentParser(description="Broadcast Burmese Story to Telegram Channel")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--latest", action="store_true", help="Broadcast the latest published story")
    group.add_argument("--story", type=str, help="Story ID to broadcast (e.g. BS-007)")
    group.add_argument("--list", action="store_true", help="List all available stories")

    parser.add_argument("--dry-run", action="store_true", help="Preview notification without calling API")
    parser.add_argument("--token", type=str, default=os.environ.get("TELEGRAM_BOT_TOKEN"), help="Telegram Bot Token")
    parser.add_argument("--chat-id", "--channel", type=str, default=os.environ.get("TELEGRAM_CHAT_ID", "@stellarpub_official"), help="Target Channel (@name or -100...)")

    args = parser.parse_args()

    stories = get_all_stories()
    if not stories:
        print("Error: No stories found in repository.", file=sys.stderr)
        sys.exit(1)

    if args.list:
        print("Available Stories:")
        for s in stories:
            print(f"  [{s['id']}] {s['meta'].get('title_my')} - {s['meta'].get('title_en')}")
        sys.exit(0)

    if args.latest:
        target = stories[-1]
    else:
        matched = [s for s in stories if s["id"].upper() == args.story.upper()]
        if not matched:
            print(f"Error: Story '{args.story}' not found. Use --list to view all.", file=sys.stderr)
            sys.exit(1)
        target = matched[0]

    photo_path = find_illustration(target)
    caption = build_telegram_caption(target)

    print("==================================================")
    print(f"Target Story : {target['id']} — {target['meta'].get('title_my')}")
    print(f"Channel      : {args.chat_id}")
    print(f"Illustration : {photo_path if photo_path else 'None (text-only fallback)'}")
    print("==================================================")

    if args.dry_run:
        print("\n--- [DRY RUN: Telegram HTML Caption Preview] ---")
        print(caption)
        print("-------------------------------------------------")
        print("\n[DRY RUN] No API request dispatched. Payload verified successfully.")
        sys.exit(0)

    if not args.token:
        print("\nError: Telegram Bot Token missing.", file=sys.stderr)
        print("Provide via --token, TELEGRAM_BOT_TOKEN env variable, or .env file.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDispatching notification to {args.chat_id} via Telegram Bot API...")
    try:
        if photo_path and photo_path.exists():
            res = send_telegram_photo(args.token, args.chat_id, photo_path, caption)
        else:
            res = send_telegram_message(args.token, args.chat_id, caption)

        if res.get("ok"):
            msg_id = res["result"].get("message_id")
            print(f"✅ Success! Message broadcasted to {args.chat_id} (Message ID: {msg_id})")
        else:
            print(f"❌ Telegram API Error: {res}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Network/Dispatch Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
