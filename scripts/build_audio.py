#!/usr/bin/env python3
"""
Audio Narration Builder for Burmese Stories
Generates lightweight 32kbps mono MP3 narration using edge-tts + ffmpeg,
storing outputs in gitignored assets/audio/ and optionally uploading to GitHub Releases.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"
AUDIO_DIR = REPO_ROOT / "assets" / "audio"


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
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def extract_narration_text(meta, body):
    """Convert story markdown into clean spoken Burmese narration."""
    clean = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    clean = re.sub(r"^#\s+.*$", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^##\s*[၀-၉\d]+[။\.\)]\s*.*$", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^---\s*$", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^##\s+သင်ခန်းစာ\s*$", "သင်ခန်းစာ။", clean, flags=re.MULTILINE)
    clean = re.sub(r"^##\s+", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

    title = meta.get("title_my", "").strip()
    if title:
        return f"{title}။\n\n{clean}"
    return clean


def resolve_edge_tts_cmd():
    """Locate edge-tts CLI or fallback to uvx edge-tts."""
    direct = shutil.which("edge-tts")
    if direct:
        return [direct]
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx, "edge-tts"]
    raise RuntimeError("Neither 'edge-tts' nor 'uvx' found in PATH.")


def synthesize_story(story_path, voice, rate, bitrate):
    """Synthesize a single story markdown file into a 32kbps mono MP3."""
    content = story_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    story_id = meta.get("id", story_path.stem)
    narration = extract_narration_text(meta, body)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_mp3 = AUDIO_DIR / f"{story_id}.mp3"
    edge_cmd = resolve_edge_tts_cmd()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        txt_file = tmp_path / f"{story_id}.txt"
        raw_mp3 = tmp_path / f"{story_id}_raw.mp3"
        txt_file.write_text(narration, encoding="utf-8")

        subprocess.run(
            edge_cmd + ["--voice", voice, f"--rate={rate}", "--file", str(txt_file), "--write-media", str(raw_mp3)],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_mp3), "-codec:a", "libmp3lame", "-b:a", bitrate, "-ac", "1", str(out_mp3)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return out_mp3


def upload_to_release(mp3_files, tag):
    """Ensure GitHub Release tag exists and upload MP3 assets."""
    gh = shutil.which("gh")
    if not gh:
        raise RuntimeError("'gh' CLI not found in PATH.")

    view = subprocess.run([gh, "release", "view", tag], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if view.returncode != 0:
        subprocess.run(
            [gh, "release", "create", tag, "--title", "Story Audio Narration", "--notes", "Pre-baked 32kbps mono MP3 narration assets."],
            cwd=REPO_ROOT,
            check=True,
        )

    subprocess.run(
        [gh, "release", "upload", tag, *[str(p) for p in mp3_files], "--clobber"],
        cwd=REPO_ROOT,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Build 32kbps mono MP3 narration for Burmese Stories")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--story", type=str, help="Story ID to synthesize (e.g. BS-019)")
    group.add_argument("--all", action="store_true", help="Synthesize all stories missing local MP3s")
    parser.add_argument("--voice", type=str, default="my-MM-NilarNeural", help="edge-tts Burmese voice")
    parser.add_argument("--rate", type=str, default="-5%", help="Speaking rate adjustment (e.g. -5%%)")
    parser.add_argument("--bitrate", type=str, default="32k", help="Output MP3 bitrate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing local MP3 files")
    parser.add_argument("--upload", action="store_true", help="Upload generated MP3(s) to GitHub Release")
    parser.add_argument("--release-tag", type=str, default="audio-v1", help="Target GitHub Release tag")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg not found in PATH.", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(p for p in STORIES_DIR.glob("**/*.md") if not p.name.startswith("."))
    if args.story:
        md_files = [p for p in md_files if p.stem.upper().startswith(args.story.upper())]
        if not md_files:
            print(f"Error: Story '{args.story}' not found.", file=sys.stderr)
            sys.exit(1)

    generated = []
    for idx, md_path in enumerate(md_files):
        meta, _ = parse_frontmatter(md_path.read_text(encoding="utf-8"))
        story_id = meta.get("id", md_path.stem)
        target_mp3 = AUDIO_DIR / f"{story_id}.mp3"
        if target_mp3.exists() and not args.force and not args.story:
            print(f"[SKIP] {story_id}.mp3 already exists")
            continue

        print(f"[SYNTH] {story_id} ({args.voice}, rate={args.rate}, bitrate={args.bitrate})...")
        out = synthesize_story(md_path, args.voice, args.rate, args.bitrate)
        print(f"  -> {out} ({out.stat().st_size / 1024:.1f} KB)")
        generated.append(out)
        if idx + 1 < len(md_files):
            time.sleep(2.5)

    if args.upload and generated:
        print(f"[UPLOAD] Uploading {len(generated)} file(s) to release '{args.release_tag}'...")
        upload_to_release(generated, args.release_tag)
        print(f"[DONE] Uploaded to release '{args.release_tag}'.")


if __name__ == "__main__":
    main()
