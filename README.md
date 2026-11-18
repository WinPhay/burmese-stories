# Burmese Stories (မြန်မာပုံပြင်များ)

> မြန်မာစာဖတ်ပရိသတ်များနှင့် ကလေး၊ လူငယ်များအတွက် အတွေးအမြင်နှင့် လက်တွေ့ဘဝ သင်ခန်းစာများ ပေးစွမ်းနိုင်မည့် မူရင်းမြန်မာပုံပြင်များ စုစည်းမှု။

---

## 1. Catalog & Reading Guide

- **Live Web Reader**: [https://stellarpub.celestrionx.com/](https://stellarpub.celestrionx.com/)
- **Official Telegram Channel**: [@stellarpub_official](https://t.me/stellarpub_official)
- **Master Index**: [CATALOG.md](CATALOG.md)

| ကဏ္ဍ (Category) | ဖော်ပြချက် | လမ်းကြောင်း (Path) |
| :--- | :--- | :--- |
| **ကလေးပုံပြင်များ** | အသက် ၄ နှစ်မှ ၁၀ နှစ်အရွယ် ကလေးများအတွက် ဖတ်ရလွယ်ကူပြီး နွေးထွေးသော သင်ခန်းစာပေးပုံပြင်များ | [`stories/children/`](stories/children/) |
| **ရိုးရာနှင့် ဒဏ္ဍာရီများ** | မြန်မာ့ရိုးရာ ယဉ်ကျေးမှု၊ ဒဏ္ဍာရီနှင့် သဘာဝအခြေပြု ပုံပြင်များ | [`stories/folklore/`](stories/folklore/) |
| **ခေတ်ပေါ်ပုံပြင်များ** | ခေတ်သစ်လူမှုဘဝ၊ အတွေးအခေါ်နှင့် လူငယ်/လူကြီးများအတွက် တင်စားပုံပြင်များ | [`stories/contemporary/`](stories/contemporary/) |

---

## 2. Publication Suite (3-in-1 Engine)

ဤ repository တွင် အောက်ပါ ထုတ်ဝေမှုစနစ်များကို အလိုအလျောက် ထုတ်လုပ်နိုင်သည့် tool များ ထည့်သွင်းထားပါသည်:
1. **Web Reader (PWA)**: GitHub Pages ပေါ်တွင် အလိုအလျောက် deploy ဖြစ်သည့် static reader (`scripts/build_site.py`).
2. **Print-ready A4 PDF**: စာအုပ်ထုတ်ဝေရန်နှင့် ကလေးများအတွက် print ထုတ်နိုင်သော landscape PDF များ (`scripts/build_pdf.py`).
3. **Social Media Kit**: Telegram (@stellarpub_official) နှင့် Facebook အတွက် ၁၀၈၀x၁၀၈၀ carousel cards နှင့် စာသားများ (`scripts/build_social.py`).

တစ်ချက်တည်းဖြင့် အားလုံး build လုပ်ရန်:
```bash
python3 scripts/build_all.py
```

---

## 2. Standards & Continuity

- **အရေးအသားနှင့် လေသံစံနှုန်း (Style & Voice)**: ပုံပြင်တိုင်းသည် သက်ဝင်လှုပ်ရှားပြီး အသံထွက်ဖတ်ကောင်းသော စကားပြေဟန်ဖြင့် ရေးသားရမည်။ စည်းမျဉ်းအသေးစိတ်ကို [STYLE.md](STYLE.md) တွင် ကြည့်ရှုပါ။
- **ယူနီကုဒ် စံစနစ် (Unicode 5.2+)**: Zawgyi လုံးဝ အသုံးမပြုဘဲ စံယူနီကုဒ် (Pyidaungsu / Myanmar3) စနစ်ဖြင့်သာ စနစ်တကျ ရေးသားထားပါသည်။
- **ဇာတ်လမ်းဖွဲ့စည်းပုံ (5-Beat Arc)**: အစပျိုးခြင်း → ဖြစ်စဉ်ပျိုးခြင်း → အလှည့်အပြောင်း → အဖြေထွက်ခြင်း → နိဂုံး။
- **လက်တွေ့ကျသော သင်ခန်းစာ**: ပုံပြင်တိုင်း၏ အဆုံးတွင် ဘဝအတွက် တန်ဖိုးရှိသော လက်တွေ့ကျ သင်ခန်းစာ (၁) ခုတည်းကိုသာ ရှင်းလင်းစွာ ဖော်ပြထားပါသည်။
- **ဇာတ်ကောင်နှင့် သင်ခန်းစာ ထပ်ခါတလဲလဲ မဖြစ်စေရေး**: [`continuity/`](continuity/) တွင် အသုံးပြုခဲ့ပြီးသော ဇာတ်ကောင်၊ နောက်ခံပတ်ဝန်းကျင်နှင့် သင်ခန်းစာများကို မှတ်တမ်းတင် ထိန်းသိမ်းထားပါသည်။

---

## 3. Agent & Contributor Guidance

ပုံပြင်အသစ်များ ထည့်သွင်းခြင်းနှင့် ပြင်ဆင်ခြင်းအတွက် စည်းမျဉ်းများကို [AGENTS.md](AGENTS.md) နှင့် [STYLE.md](STYLE.md) တွင် ကြည့်ရှုပါ။
အသုံးပြုရန် ပုံစံခွက်: [templates/story_template.md](templates/story_template.md)
