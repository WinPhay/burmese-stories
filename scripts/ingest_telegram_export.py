#!/usr/bin/env python3
"""
Ingests 10 legacy Telegram stories from result.json into burmese-stories repository.
Converts stories into standard Markdown files with frontmatter, 5-beat dramatic arcs,
and links to illustrations.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORIES_DIR = REPO_ROOT / "stories"
JSON_PATH = Path("/home/mss-swp/Downloads/Telegram Desktop/ChatExport_2026-11-18/result.json")

def load_telegram_messages():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    msgs = {}
    for m in data.get("messages", []):
        raw = m.get("text", "")
        if isinstance(raw, list):
            text = "".join([item if isinstance(item, str) else item.get("text", "") for item in raw])
        else:
            text = raw
        msgs[m["id"]] = {
            "text": text,
            "date": m.get("date", "").split("T")[0]
        }
    return msgs

STORY_SPECS = [
    {
        "id": "BS-008",
        "slug": "BS-008-rich-merchant-village-road",
        "title_my": "သူဌေးကြီး နှင့် လမ်းကလေး",
        "title_en": "The Wealthy Merchant and the Village Road",
        "category": "folklore",
        "target_audience": "All Ages",
        "msg_ids": [3],
        "img": "BS-008-rich-merchant-village-road.png",
        "characters": [
            "ဦးဘိုးသန်း (ကပ်စေးနှဲ သူဌေးကြီး)",
            "ရွာလူကြီးနှင့် ရွာသူရွာသားများ"
        ],
        "setting": "ဝေးလံခေါင်ဖျားသော သာယာကုန်း တောင်ကြားရွာနှင့် ရွှံ့ဗွက်ထူသော မြို့သွားလမ်း",
        "lesson": "ကောင်းမှုကုသိုလ် ပြုလုပ်ခြင်းနှင့် အများအကျိုးကို ဝိုင်းဝန်းဆောင်ရွက်ခြင်းသည် သူတစ်ပါးအတွက်သာ မဟုတ်ဘဲ တစ်နေ့နေ့တွင် မိမိကိုယ်တိုင်၏ အသက်နှင့် ဘဝကို ကာကွယ်ကယ်တင်ပေးသော ကျေးဇူးတရား ဖြစ်လာတတ်သည်။"
    },
    {
        "id": "BS-009",
        "slug": "BS-009-old-lantern-keeper",
        "title_my": "မီးအိမ်စောင့် အဘိုးကြီး",
        "title_en": "The Old Lantern Keeper",
        "category": "folklore",
        "target_audience": "All Ages",
        "msg_ids": [4],
        "img": "BS-009-old-lantern-keeper.png",
        "characters": [
            "အဘိုးဦးသာဒင် (မီးအိမ်စောင့် အဘိုးအို)",
            "မင်းသားငယ်နှင့် ခရီးသွားများ"
        ],
        "setting": "ညဉ့်နက်လမ်းဆုံနှင့် လေတိုက်ခတ်နေသော မြစ်ဆိပ်လမ်းမဟောင်း",
        "lesson": "လူမမြင် လူမသိသော နေရာ၌ စိတ်ရှည်စွာ တိတ်တဆိတ် ထွန်းညှိထားသော မီးအိမ်ငယ်လေးတစ်လုံးသည် မုန်တိုင်းထန်သော ညဉ့်နက်အချိန်တွင် လမ်းပျောက်နေသူ တစ်ဦးအတွက် တန်ဖိုးမဖြတ်နိုင်သော လမ်းပြအလင်းရောင် ဖြစ်စေနိုင်သည်။"
    },
    {
        "id": "BS-010",
        "slug": "BS-010-fragrant-monkey",
        "title_my": "အီးမွှေး (ရနံ့မွှေးသော မျောက်ကလေး)",
        "title_en": "Ee Mwe the Fragrant Monkey",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [5],
        "img": "BS-010-fragrant-monkey.png",
        "characters": [
            "မောင်ရွှေမျောက် (ရနံ့မွှေးသော မျောက်ငယ်)",
            "တောဝက်ကလေး (မနာလိုသော သူငယ်ချင်း)"
        ],
        "setting": "ရနံ့မွှေးသော သစ်သီးစုံတောအုပ်နှင့် မြို့စွန်သစ်တော",
        "lesson": "မာန်မာနနှင့် အပေါ်ယံ လောဘသည် မိမိ၌ ရှိရင်းစွဲ အဖိုးတန် ဂုဏ်သိက္ခာကို ပျက်စီးစေတတ်သည်။ သူတစ်ပါးကို မကောင်းကြံ၍ အယုံသွင်းခြင်းသည် နောက်ဆုံးတွင် မိမိကိုယ်တိုင်လည်း ဆုံးရှုံးမှုနှင့် ရင်ဆိုင်ရတတ်သည်။"
    },
    {
        "id": "BS-011",
        "slug": "BS-011-little-tiger-roaring-mountain",
        "title_my": "ကျားလေး နှင့် အော်တတ်သော တောင်",
        "title_en": "The Little Tiger and the Roaring Mountain",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [10],
        "img": "BS-011-little-tiger-roaring-mountain.png",
        "characters": [
            "ဗလ (သတ္တိရှိသော ကျားကလေး)",
            "ပဲ့တင်သံ တောင်ကြီး"
        ],
        "setting": "မိုးကြိုးသံလို ပဲ့တင်ထပ်သော ကျောက်တောင်ချောက်ကမ်းပါး",
        "lesson": "မသိနားမလည်သေးချိန်တွင် ကြောက်စရာဟု ထင်မှတ်ရသောအရာများသည် သတ္တိရှိရှိ စူးစမ်းလေ့လာကြည့်လိုက်ပါက အမှန်တရားမှာ သဘာဝ၏ ပဲ့တင်သံတစ်ခုသာ ဖြစ်ကြောင်း နားလည်လာနိုင်သည်။"
    },
    {
        "id": "BS-012",
        "slug": "BS-012-great-rooster-lost-sun",
        "title_my": "ကြက်ဖကြီး နှင့် ပျောက်ဆုံးနေသော နေမင်း",
        "title_en": "The Great Rooster and the Lost Sun",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [13],
        "img": "BS-012-great-rooster-lost-sun.png",
        "characters": [
            "ဖိုးတွန် (ကြက်ဖကြီး)",
            "နေမင်းကြီး",
            "တောတွင်းတိရစ္ဆာန်ငယ်များ"
        ],
        "setting": "မှောင်မိုက်နေသော အရုဏ်ဦး ကျေးရွာသစ်တော",
        "lesson": "မိမိ မျက်စိဖြင့် တစ်စိတ်တစ်ပိုင်း မြင်ရရုံမျှဖြင့် အလောတကြီး ကောက်ချက်မချသင့်ပေ။ စိုးရိမ်ထိတ်လန့်မှု မဖြစ်မီ အခြေအနေမှန်ကို စိတ်အေးချမ်းစွာ စိစစ်မေးမြန်းခြင်းကသာ အမှားကို ကာကွယ်နိုင်သည်။"
    },
    {
        "id": "BS-013",
        "slug": "BS-013-little-monkey-coconut",
        "title_my": "မျောက်ကလေး နှင့် အုန်းသီး",
        "title_en": "The Little Monkey and the Coconut",
        "category": "children",
        "target_audience": "Ages 4-10",
        "msg_ids": [16],
        "img": "BS-013-little-monkey-coconut.png",
        "characters": [
            "ဖိုးကျောက် (မျောက်ကလေး)",
            "မျောက်အိုကြီး ဦးဉာဏ်"
        ],
        "setting": "ပင်လယ်ကမ်းစပ် အုန်းပင်မြင့်တော",
        "lesson": "သာမန်သဘာဝ အဖြစ်အပျက်ကို အံ့ဖွယ်ထူးခြားသည်ဟု ထင်ယောင်ထင်မှားဖြစ်ကာ မာနထောင်လွှားမနေသင့်ပေ။ လက်တွေ့ကျသော အသိပညာဖြင့် ဆင်ခြင်ခြင်းကသာ အမှန်တရားကို မျက်ဝါးထင်ထင် တွေ့မြင်စေသည်။"
    },
    {
        "id": "BS-014",
        "slug": "BS-014-little-frog-moon-festival",
        "title_my": "ဖားကလေး နှင့် လမင်းဖမ်းပွဲ",
        "title_en": "The Little Frog and the Moon Catching Festival",
        "category": "children",
        "target_audience": "Ages 4-10",
        "msg_ids": [20],
        "img": "BS-014-little-frog-moon-festival.png",
        "characters": [
            "ဖိုးခုန် (စူးစမ်းလိုသော ဖားကလေး)",
            "ဦးဝိုင်း (ငါးကြီး)"
        ],
        "setting": "လပြည့်ည ကြာစုံရေအိုင်ငယ်",
        "lesson": "ရေပြင်ပေါ်က အရိပ်ကို အစစ်အမှန်ဟု အထင်မမှားသင့်သကဲ့သို့ အပေါ်ယံ မြင်ကွင်းတိုင်းကို မဆင်မခြင် မယုံကြည်သင့်ပေ။ အရာရာကို အမှန်တကယ် လက်တွေ့စူးစမ်းပြီးမှသာ ဆုံးဖြတ်ချက်ချသင့်သည်။"
    },
    {
        "id": "BS-015",
        "slug": "BS-015-little-fox-honey-pot",
        "title_my": "မြေခွေးလေး နှင့် ပျားရည်အိုး",
        "title_en": "The Little Fox and the Honey Pot",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [22],
        "img": "BS-015-little-fox-honey-pot.png",
        "characters": [
            "ဖိုးကောက် (မြေခွေးကလေး)",
            "ဦးဖား (ဝက်ဝံကြီး)"
        ],
        "setting": "ပျားအုံစွဲနေသော သစ်ခေါင်းဟောင်းနှင့် သစ်တောလမ်းဆုံ",
        "lesson": "သက်သေအထောက်အထား မရှိဘဲ သူတစ်ပါးကို မသင်္ကာစိတ်ဖြင့် စွပ်စွဲခြင်းသည် မိတ်ဆွေကောင်းများကို ဝေးကွာစေတတ်သည်။ ပြဿနာကြုံလာပါက သူတစ်ပါးကို အပြစ်မတင်မီ မိမိ၏ ပတ်ဝန်းကျင်ကို သေချာစွာ ဦးစွာ စစ်ဆေးသင့်သည်။"
    },
    {
        "id": "BS-016",
        "slug": "BS-016-kindness-beneath-old-tree",
        "title_my": "သစ်ပင်အိုကြီးအောက်က ကြင်နာမှု",
        "title_en": "Kindness Beneath the Old Tree",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [25, 26],
        "img": "BS-016-kindness-beneath-old-tree.png",
        "characters": [
            "မောင်ညို (သမင်ငယ်)",
            "သစ်ပင်အိုကြီး",
            "တောတွင်းတိရစ္ဆာန်များ"
        ],
        "setting": "မိုးသက်မုန်တိုင်း ကျရောက်နေသော သစ်တောအလယ်က သစ်ပင်အိုကြီးရိပ်",
        "lesson": "ကြင်နာမှုဟူသည် မိမိကို ပြန်လည်ကျေးဇူးဆပ်နိုင်သူများအပေါ်၌သာ မဟုတ်ဘဲ မတူကွဲပြားသူများနှင့် ခိုကိုးရာမဲ့သူများအပေါ်၌ပါ အတ္တကင်းစွာ ဖြန့်ဝေပေးဆပ်ခြင်း ဖြစ်သည်။"
    },
    {
        "id": "BS-017",
        "slug": "BS-017-white-rabbit-needy-friends",
        "title_my": "ယုန်ဖြူလေးနှင့် အမြဲတမ်းတောင်းဆိုနေသော သူငယ်ချင်းများ",
        "title_en": "The White Rabbit and the Needy Friends",
        "category": "children",
        "target_audience": "Ages 6-12",
        "msg_ids": [28],
        "img": "BS-017-white-rabbit-needy-friends.png",
        "characters": [
            "ဖိုးဖြူ (ယုန်ဖြူလေး)",
            "ဘုတ်ကြီး (ရှဉ့်ကလေး)",
            "ဝက်ဝံညို"
        ],
        "setting": "မုန်လာဥခင်းနှင့် စိမ်းလန်းသော သစ်တောအစွန်",
        "lesson": "သူတစ်ပါးကို ကြင်နာကူညီခြင်းသည် မွန်မြတ်သော်လည်း မိမိကိုယ်ကို ထိခိုက်နစ်နာသည်အထိ အဆုံးမဲ့ လိုက်လျောမနေဘဲ မှန်ကန်သော နယ်နိမိတ်ကို သတ္တိရှိရှိ သတ်မှတ်တတ်ရမည်။"
    }
]

def clean_story_body(raw_text):
    # Remove title header if present at top
    lines = raw_text.strip().split("\n")
    if lines and (lines[0].startswith("✨") or lines[0].startswith("🌳") or lines[0].startswith("🐇") or lines[0].startswith("ဖား") or lines[0].startswith("ကျား") or lines[0].startswith("ကြက်") or lines[0].startswith("မျောက်") or lines[0].startswith("မြေခွေး") or lines[0].startswith("သူဌေး") or lines[0].startswith("မီးအိမ်") or lines[0].startswith("အီးမွှေး")):
        lines = lines[1:]
    
    body = "\n".join(lines).strip()
    
    # Strip any trailing moral section from body
    if "သင်ခန်းစာ" in body:
        parts = re.split(r"(?:🌾\s*)?သင်ခန်းစာ", body, flags=re.MULTILINE)
        body = parts[0].strip()
        
    return body

def structure_into_beats(body):
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    n = len(paras)
    
    # Divide paragraphs proportionally into 5 beats
    b1_end = max(1, n // 5)
    b2_end = max(b1_end + 1, (2 * n) // 5)
    b3_end = max(b2_end + 1, (3 * n) // 5)
    b4_end = max(b3_end + 1, (4 * n) // 5)
    
    beat1 = "\n\n".join(paras[:b1_end])
    beat2 = "\n\n".join(paras[b1_end:b2_end])
    beat3 = "\n\n".join(paras[b2_end:b3_end])
    beat4 = "\n\n".join(paras[b3_end:b4_end])
    beat5 = "\n\n".join(paras[b4_end:])
    
    structured = (
        f"## ၁။ အစပျိုးခြင်း\n\n{beat1}\n\n"
        f"## ၂။ ဖြစ်စဉ်ပျိုးခြင်း\n\n{beat2}\n\n"
        f"## ၃။ အလှည့်အပြောင်း\n\n{beat3}\n\n"
        f"## ၄။ အဖြေထွက်ခြင်း\n\n{beat4}\n\n"
        f"## ၅။ နိဂုံး\n\n{beat5}"
    )
    return structured

def main():
    msgs = load_telegram_messages()
    
    for spec in STORY_SPECS:
        raw_texts = []
        date = "2026-05-21"
        for mid in spec["msg_ids"]:
            raw_texts.append(msgs[mid]["text"])
            date = msgs[mid]["date"]
            
        full_raw = "\n\n".join(raw_texts)
        cleaned_body = clean_story_body(full_raw)
        beats_text = structure_into_beats(cleaned_body)
        
        # Build YAML frontmatter
        characters_yaml = "\n".join([f'  - "{c}"' for c in spec["characters"]])
        
        content = f"""---
id: "{spec['id']}"
title_my: "{spec['title_my']}"
title_en: "{spec['title_en']}"
author: "Asap Money"
category: "{spec['category']}"
target_audience: "{spec['target_audience']}"
characters:
{characters_yaml}
setting: "{spec['setting']}"
lesson: "{spec['lesson']}"
created_at: {date}
status: "published"
---

# {spec['title_my']}

![{spec['title_my']}](../../assets/illustrations/{spec['img']})

{beats_text}

---

## သင်ခန်းစာ

{spec['lesson']}
"""
        target_dir = STORIES_DIR / spec["category"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{spec['slug']}.md"
        target_file.write_text(content, encoding="utf-8")
        print(f"Created {target_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
