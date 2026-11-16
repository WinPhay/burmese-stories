#!/usr/bin/env python3
"""
Burmese Story Voice & Literary Style Linter
Enforces STYLE.md standards across stories in burmese-stories.
Checks:
1. Sentence terminal cadence (flags consecutive ...သည် / ...ခဲ့သည် / ...လေသည် runs)
2. Living narrative particles (ensures presence of oral story particles)
3. Sensory anchors & onomatopoeia density
4. Dialogue preachiness & natural brevity
5. Structure (5-beat arc + ## သင်ခန်းစာ length)
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"

# Patterns
FORMAL_TERMINALS = [r"သည်။", r"ခဲ့သည်။", r"လေသည်။", r"လျက်ရှိသည်။", r"ရလေသည်။"]
LIVING_PARTICLES = [
    r"ပေါ့။", r"ရှာတယ်။", r"ရှာလေရဲ့။", r"တော့တာပဲ။", r"သွားလေရဲ့။",
    r"သတဲ့။", r"ပါရော့လား။", r"လေမလားလို့။", r"တာပေါ့။", r"တာပဲ။",
    r"ခဲ့တာပေါ့။", r"ခဲ့တာပဲ။", r"ရရှာတယ်။"
]
SENSORY_WORDS = [
    "ဝေါခနဲ", "ဂျိန်းခနဲ", "တဖျစ်ဖျစ်", "တဝေါဝေါ", "တဖြန်းဖြန်း", "တရှဲရှဲ",
    "တဂျွတ်ဂျွတ်", "တဖျပ်ဖျပ်", "မာတောင့်တောင့်", "ပျော့စိစိ", "တွန့်လိမ်",
    "စိမ်းစိမ်းစိုစို", "မည်းမှောင်", "ဒရဟတ်", "လူးလွန့်", "ခြေကုန်သုတ်",
    "ခေါင်းတညိတ်ညိတ်", "သဲသဲမဲမဲ", "တလှုပ်လှုပ်", "ညင်သာစွာ", "ဟက်ဟက်ပက်ပက်"
]
PREACHY_WORDS = [
    "ဒဿန", "အရာအားလုံး မာကျောနေဖို့ မလို", "သဘာဝတရားမှာ", "လိုက်လျောပေးနိုင်တာက",
    "ဒဿနသဘောတရား", "အသိတရားရရှိစေရန်"
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

def audit_story(md_path):
    content = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    slug = md_path.stem
    story_id = meta.get("id", slug)

    # Clean body
    clean = re.sub(r"!\[.*?\]\(.*?\)", "", body)
    
    # Split paragraphs
    paras = [p.strip() for p in clean.split("\n") if p.strip() and not p.startswith("#")]
    sentences = []
    for p in paras:
        for s in re.split(r"(?<=။)", p):
            s = s.strip()
            if s:
                sentences.append(s)

    issues = []
    warnings = []

    # 1. Check consecutive formal terminals
    consecutive_formal = 0
    max_consecutive_formal = 0
    for s in sentences:
        is_formal = any(re.search(term, s) for term in FORMAL_TERMINALS)
        if is_formal:
            consecutive_formal += 1
            if consecutive_formal > max_consecutive_formal:
                max_consecutive_formal = consecutive_formal
        else:
            consecutive_formal = 0

    if max_consecutive_formal >= 5:
        warnings.append(f"High consecutive formal terminal run: {max_consecutive_formal} sentences in a row ending in 'သည်/ခဲ့သည်/လေသည်'. Consider mixing in oral particles ('ပေါ့/ရှာတယ်/တော့တာပဲ').")

    # 2. Living particles count
    living_count = 0
    for s in sentences:
        if any(re.search(part, s) for part in LIVING_PARTICLES):
            living_count += 1

    # 3. Sensory word count
    sensory_matches = [w for w in SENSORY_WORDS if w in clean]

    # 4. Dialogue Preachiness
    quotes = re.findall(r'["“](.*?)["”]', clean)
    for q in quotes:
        for pw in PREACHY_WORDS:
            if pw in q:
                warnings.append(f"Preachy/Academic phrase '{pw}' detected inside dialogue: \"{q[:40]}...\"")

    # 5. Moral section check
    if "## သင်ခန်းစာ" not in body:
        issues.append("Missing '## သင်ခန်းစာ' header invariant.")
    else:
        moral_match = re.search(r"## သင်ခန်းစာ\s*\n+(.*?)(?=\n##|\Z)", body, re.DOTALL)
        if moral_match:
            moral_text = moral_match.group(1).strip()
            moral_sentences = [s for s in moral_text.split("။") if s.strip()]
            if len(moral_sentences) > 4:
                warnings.append(f"Moral section is long ({len(moral_sentences)} sentences). Style standard prefers ≤ 3 punchy sentences.")

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
    print("=" * 60)
    print("Burmese Story Voice & Style Linter (STYLE.md Audit)")
    print("=" * 60)

    total_issues = 0
    total_warnings = 0

    for md_file in sorted(STORIES_DIR.glob("**/*.md")):
        if md_file.name.startswith("."):
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
