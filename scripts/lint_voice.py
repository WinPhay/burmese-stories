#!/usr/bin/env python3
"""
Burmese Story Voice & Literary Style Linter
Enforces STYLE.md standards (including G10-G12 native syntax & morphology rules) across stories.
Checks:
1. Sentence terminal cadence (consecutive ...သည်/ခဲ့သည် runs & stock-particle crutch stuffing)
2. Living narrative particles (presence of varied oral story particles)
3. Sensory anchors & onomatopoeia density
4. English translation calques & abstract nominalization (-မှု/-ခြင်း) density
5. Dialogue preachiness & multi-sentence monologue length
6. Structure (## သင်ခန်းစာ length)
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"

FORMAL_TERMINALS = [r"သည်။", r"ခဲ့သည်။", r"လေသည်။", r"လျက်ရှိသည်။", r"ရလေသည်။"]
STOCK_CRUTCHES = [r"ပေါ့။", r"လေရဲ့။", r"တော့တာပဲ။", r"ရှာတယ်။"]
LIVING_PARTICLES = [
    r"ပေါ့။", r"ရှာတယ်။", r"ရှာလေရဲ့။", r"တော့တာပဲ။", r"သွားလေရဲ့။",
    r"သတဲ့။", r"ပါရော့လား။", r"လေမလားလို့။", r"တာပေါ့။", r"တာပဲ။",
    r"ခဲ့တာပေါ့။", r"ခဲ့တာပဲ။", r"ရရှာတယ်။", r"လေရော။", r"ပေတော့။", r"ကွယ်။"
]
SENSORY_WORDS = [
    "ဝေါခနဲ", "ဂျိန်းခနဲ", "တဖျစ်ဖျစ်", "တဝေါဝေါ", "တဖြန်းဖြန်း", "တရှဲရှဲ",
    "တဂျွတ်ဂျွတ်", "တဖျပ်ဖျပ်", "မာတောင့်တောင့်", "ပျော့စိစိ", "တွန့်လိမ်",
    "စိမ်းစိမ်းစိုစို", "မည်းမှောင်", "ဒရဟတ်", "လူးလွန့်", "ခြေကုန်သုတ်",
    "ခေါင်းတညိတ်ညိတ်", "သဲသဲမဲမဲ", "တလှုပ်လှုပ်", "ညင်သာစွာ", "ဟက်ဟက်ပက်ပက်",
    "စိမ်ပြေနပြေ", "အေးအေးလူလူ", "သေသေသပ်သပ်", "တင့်တောင့်တင့်တယ်"
]
PREACHY_WORDS = [
    "ဒဿန", "အရာအားလုံး မာကျောနေဖို့ မလို", "သဘာဝတရားမှာ", "လိုက်လျောပေးနိုင်တာက",
    "ဒဿနသဘောတရား", "အသိတရားရရှိစေရန်"
]
CALQUE_PHRASES = [
    "ကနေတစ်ဆင့်", "မှတစ်ဆင့်", "မည်သည့်အခါမျှ", "လက်တုန်သမား",
    "အဓိပ္ပာယ်ရှိသော", "နေရာတိုင်းနဲ့ မကိုက်ညီ"
]


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


def split_sentences(text):
    clean = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    paras = [p.strip() for p in clean.split("\n") if p.strip() and not p.startswith("#") and p.strip() != "---"]
    sentences = []
    for p in paras:
        for s in re.split(r"(?<=။)", p):
            s = s.strip()
            if s:
                sentences.append(s)
    return clean, sentences


def audit_story(md_path):
    content = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    slug = md_path.stem
    story_id = meta.get("id", slug)

    narrative_body = re.split(r"^##\s+သင်ခန်းစာ", body, maxsplit=1, flags=re.MULTILINE)[0]
    clean, sentences = split_sentences(body)
    _, narrative_sentences = split_sentences(narrative_body)

    issues = []
    warnings = []

    # 1. Consecutive formal terminal runs
    consecutive_formal = 0
    max_consecutive_formal = 0
    for s in sentences:
        if any(re.search(term, s) for term in FORMAL_TERMINALS):
            consecutive_formal += 1
            max_consecutive_formal = max(max_consecutive_formal, consecutive_formal)
        else:
            consecutive_formal = 0

    if max_consecutive_formal >= 5:
        warnings.append(
            f"High consecutive formal terminal run: {max_consecutive_formal} sentences ending in 'သည်/ခဲ့သည်/လေသည်'."
        )

    # 2. Stock-particle crutch stuffing (STYLE.md §8.3)
    consecutive_crutch = 0
    max_consecutive_crutch = 0
    same_crutch_run = 0
    max_same_crutch_run = 0
    prev_crutch = None
    for s in narrative_sentences:
        matched = next((c for c in STOCK_CRUTCHES if re.search(c, s)), None)
        if matched:
            consecutive_crutch += 1
            max_consecutive_crutch = max(max_consecutive_crutch, consecutive_crutch)
            same_crutch_run = same_crutch_run + 1 if matched == prev_crutch else 1
            max_same_crutch_run = max(max_same_crutch_run, same_crutch_run)
            prev_crutch = matched
        else:
            consecutive_crutch = 0
            same_crutch_run = 0
            prev_crutch = None

    if max_same_crutch_run >= 3:
        warnings.append(f"Repeated identical stock ending {max_same_crutch_run}x in a row (STYLE.md §8.3).")
    elif max_consecutive_crutch >= 5:
        warnings.append(f"Stock-particle crutch stuffing: {max_consecutive_crutch} consecutive crutch endings (STYLE.md §8.3).")

    # 3. Living particles & sensory anchors
    living_count = sum(1 for s in sentences if any(re.search(part, s) for part in LIVING_PARTICLES))
    sensory_matches = [w for w in SENSORY_WORDS if w in clean]

    # 4. English syntax calques & abstract nominalization density (STYLE.md §8.1-8.2)
    for cp in CALQUE_PHRASES:
        if cp in clean:
            warnings.append(f"Translation-calque or synthetic phrase '{cp}' detected (STYLE.md §8.1-8.2).")

    abstract_hits = sum(s.count("မှု") + s.count("ခြင်း") for s in narrative_sentences)
    if narrative_sentences and abstract_hits >= 5 and (abstract_hits / len(narrative_sentences)) > 0.35:
        warnings.append(
            f"High abstract nominalization (-မှု/-ခြင်း: {abstract_hits} hits in {len(narrative_sentences)} narrative sentences; STYLE.md §8.1)."
        )

    # 5. Dialogue preachiness & monologue length (STYLE.md §4 & §8.4)
    quotes = re.findall(r'["“](.*?)["”]', clean, flags=re.DOTALL)
    for q in quotes:
        for pw in PREACHY_WORDS:
            if pw in q:
                warnings.append(f"Preachy/Academic phrase '{pw}' detected inside dialogue: \"{q[:40]}...\"")
        q_sentences = [seg for seg in q.split("။") if seg.strip()]
        if len(q_sentences) >= 4:
            warnings.append(f"Long monologue in dialogue ({len(q_sentences)} sentences); prefer elliptical turns (STYLE.md §8.4).")

    # 6. Moral section check
    if "## သင်ခန်းစာ" not in body:
        issues.append("Missing '## သင်ခန်းစာ' header invariant.")
    else:
        moral_match = re.search(r"## သင်ခန်းစာ\s*\n+(.*?)(?=\n##|\Z)", body, re.DOTALL)
        if moral_match:
            moral_text = moral_match.group(1).strip()
            moral_sentences = [s for s in moral_text.split("။") if s.strip()]
            if len(moral_sentences) > 4:
                warnings.append(f"Moral section is long ({len(moral_sentences)} sentences). Style standard prefers <= 3 punchy sentences.")

    return {
        "slug": slug,
        "id": story_id,
        "sentences": len(sentences),
        "max_consecutive_formal": max_consecutive_formal,
        "living_particles": living_count,
        "sensory_count": len(sensory_matches),
        "sensory_words": sensory_matches,
        "issues": issues,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Burmese Story Voice & Style Linter (STYLE.md Audit)")
    parser.add_argument("--story", type=str, help="Audit a specific Story ID (e.g. BS-019)")
    args = parser.parse_args()

    print("=" * 60)
    print("Burmese Story Voice & Style Linter (STYLE.md Audit)")
    print("=" * 60)

    total_issues = 0
    total_warnings = 0

    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
            continue
        if args.story and not md_file.stem.upper().startswith(args.story.upper()):
            continue

        report = audit_story(md_file)
        status = "FAIL" if report["issues"] else ("WARN" if report["warnings"] else "PASS")
        status_icon = "❌" if status == "FAIL" else ("⚠️" if status == "WARN" else "✅")

        print(f"\n{status_icon} [{status}] {report['id']} — {report['slug']}")
        print(f"   ├─ Sentences: {report['sentences']} | Max formal run: {report['max_consecutive_formal']}")
        print(f"   ├─ Living particles: {report['living_particles']} | Sensory anchors: {report['sensory_count']} {report['sensory_words'][:4]}")

        for issue in report["issues"]:
            print(f"   ❌ ISSUE: {issue}")
            total_issues += 1
        for warn in report["warnings"]:
            print(f"   ⚠️  WARN: {warn}")
            total_warnings += 1

    print("\n" + "=" * 60)
    print(f"Audit Summary: {total_issues} issues, {total_warnings} warnings.")
    print("=" * 60)

    if total_issues > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
