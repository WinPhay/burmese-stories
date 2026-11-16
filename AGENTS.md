# AGENTS.md — burmese-stories

## 1. Project Purpose & Operational Scope
- **Domain**: Original Burmese stories crafted for children and adults, conveying exactly one practical life lesson through natural narrative.
- **Audience**: Children (Ages 4-10), Folklore enthusiasts, and General/Contemporary readers.
- **Zero Runtime Code**: This is a Markdown-only literary and metadata repository.

---

## 2. Language & Formatting Invariants
- **Strict Unicode Standard**: All Burmese text must be compliant with Unicode 5.2+ standard (Pyidaungsu, Myanmar3, Noto Sans Myanmar). **Strictly zero Zawgyi encoding**.
- **Living Oral Story Voice (STYLE.md)**: All stories must strictly adhere to [`STYLE.md`](STYLE.md). Use natural oral storytelling register (`ပုံပြင်ပြော စကားပြေ`), ban consecutive `...ခဲ့သည် / ...လေသည်` terminal runs, mandate living particles (`...ပေါ့ / ...ရှာတယ် / ...တော့တာပဲ`), and forbid academic/essay dialogue.
- **YAML Frontmatter**: Every story file in `stories/<category>/` must include a complete frontmatter block conforming to `templates/story_template.md`.

---

## 3. Story Generation Protocol (SKILL-17)
Whenever drafting, expanding, or revising a story:

1. **Pre-Flight Continuity Scan**:
   - Inspect `continuity/lessons_matrix.md` to avoid duplicating recent morals.
   - Inspect `continuity/character_roster.md` to avoid recycled names/archetypes.
   - Inspect `continuity/settings_index.md` to ensure environmental variety.
2. **5-Beat Dramatic Arc**:
   - **Opening (အစပျိုးခြင်း)**: Introduce setting and characters naturally.
   - **Development (ဖြစ်စဉ်ပျိုးခြင်း)**: Establish conflict, goal, or situation.
   - **Turning Point (အလှည့်အပြောင်း)**: Force a hard decision or critical challenge.
   - **Resolution (အဖြေထွက်ခြင်း)**: Reveal natural consequences and internal growth.
   - **Conclusion (နိဂုံး)**: Deliver a warm, emotionally satisfying close.
3. **Moral Section Invariant**:
   - Header must be exactly `## သင်ခန်းစာ`.
   - Exactly one practical, memorable life lesson in 1-3 simple sentences.
   - No preachy lecturing, moral superiority, or unrelated secondary lessons.
4. **Post-Draft Registration**:
   - Register entry in `CATALOG.md`.
   - Append records to `continuity/lessons_matrix.md`, `character_roster.md`, and `settings_index.md`.

---

## 4. Repository Structure & Naming Conventions
- `stories/children/` — `BS-###-<kebab-slug>.md`
- `stories/folklore/` — `BS-###-<kebab-slug>.md`
- `stories/contemporary/` — `BS-###-<kebab-slug>.md`
- `continuity/` — Anti-repetition logs (`lessons_matrix.md`, `character_roster.md`, `settings_index.md`).
- `templates/` — Authoring templates (`story_template.md`).
- `STYLE.md` — Literary style, voice cadence, and sensory language standard.
- `assets/illustrations/` — Story-matched visual assets (`BS-###-<slug>.png`).
- `scripts/` — Automated publication suite (`build_site.py`, `build_pdf.py`, `build_social.py`, `build_all.py`, `lint_voice.py`).
- `.github/workflows/` — Automated GitHub Pages deployment pipeline (`deploy-pages.yml`).

---

## 5. Branch & Commit Policy
- **Protected Branches**: Direct commits or pushes to `main` or `master` are strictly forbidden.
- **Working Branches**: All creation and edits must occur on isolated branches prefixed with `feat/*` (e.g. `feat/BS-001-story-name` or `feat/scaffold-architecture`).
- **Commit Format**: Conventional commit syntax (e.g., `feat(children): add story BS-001 <title>`, `docs: update catalog and continuity index`).

---

## 6. Verification Gate
Before declaring any task complete or submitting for review, verify:
```bash
test -f AGENTS.md && test -f CATALOG.md && test -f STYLE.md && python3 scripts/lint_voice.py
```
Ensure all created story files have valid YAML frontmatter, valid Unicode, no unresolved placeholders (`[TODO]`, `<!-- ... -->`), and conform to `STYLE.md`.
