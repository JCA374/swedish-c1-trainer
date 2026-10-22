# Swedish C1+ Vocabulary Trainer — Project Summary

## What this is
A single self-contained HTML app for drilling advanced (C1 level and above)
Swedish vocabulary. Works fully offline, no dependencies, no build step, no
network calls. Progress persists in the browser via `localStorage`.

**Main file:** `index.html` — open by double-click.

## Current features
- **124 curated C1+ words** embedded as `SEED_WORDS`. Each entry:
  `{ id, word, pos, definitionSv, synonyms[], examples[], english, difficulty(1-5) }`.
- **Two exercise types** (toggleable in Inställningar):
  - **Lucktext** (fill-in-the-blank): the target word is blanked out of a real
    example sentence; user types it.
  - **Synonymmatchning**: shows the word + Swedish definition; user picks the
    correct synonym from 4 choices (distractors drawn from other words).
- **Spaced repetition**: Leitner levels 0–6 + ease factor + weighted picker.
  Missed/hard words (and words where the English "cheat" was used) recycle more
  often; mastered words fade to the back. Verified via a 6000-review simulation.
- **Swedish-first**: definitions and synonyms are Swedish. English translation is
  hidden behind a **"Visa engelska (fusk)"** button; using it flags the attempt
  so it can't promote the word (cheating doesn't inflate mastery).
- **Audio 🔊 (offline TTS)**: browser Web Speech API with `sv-SE` voice.
  - Synonym-match: speaker next to the visible word.
  - Fill-in-the-blank: speaker appears only in feedback AFTER answering (so it
    doesn't spoil the answer).
  - Button doesn't render if the browser has no speech synthesis.
- **Import/export** (Settings): import JSON word lists (merge/dedup by `id`),
  export progress, export full word list, reset progress.

## Key implementation notes
- Storage keys: `svc1.state.v1` (progress/settings), `svc1.words.v1` (word list).
- Pure-ish logic functions: `pickNextWord`, `pickWeight`, `schedule`,
  `normalizeAnswer`, `buildSynonymChoices`, `chooseMode`, `speakWord`, `speakBtn`.
- `LEITNER_INTERVALS = [0,1,2,4,8,16,32]` (ticks until due per level).

## Fixes already applied
- Removed duplicate word `id` (`foga`/`fogas` collision).
- **Synonym-leak fix**: `buildSynonymChoices` never uses a synonym that appears
  in the word's definition as the correct answer (the definition is shown next
  to the choices). Verified: 0 leaks across 124 words × 50 samples.
  (Note: 91 of 124 definitions contain at least one synonym — natural for
  dictionary-style Swedish — but none have ALL synonyms in the definition, so a
  safe correct answer always exists.)

## User instructions / decisions so far
1. Build an HTML app for Swedish C1+ exercises focused on ~1000 most-common
   C1-level words; words in context; spaced repetition (repeat hard words more,
   easy less); Swedish definitions with synonyms; English shown only on command.
2. Design choices confirmed: **curated seed (~120) + expandable via import**
   (not 1000 hand-authored, which can't be reliably verified); exercises limited
   to **fill-in-the-blank + synonym match**; **single HTML file + localStorage**.
3. Reported bug: synonym answer appeared inside the definition → fixed (see above).
4. Requested audio from **Forvo**. Forvo needs a paid API key, restricts
   bundling/redistribution, and has CORS issues → user chose **browser speech
   (offline TTS)** instead. Implemented.
5. Requested **American English translations via DeepL**. DeepL needs an API key
   (got 403, no key in env) and is CORS-blocked from browsers → must run as a
   build step. Existing glosses are already American-English-compatible
   (e.g. `judgment`, no `-ise`/`colour`/Briticisms).
6. **User said DON'T run DeepL.** No translation was performed; glosses unchanged.

## Loose ends / open items
- `deepl_translate.mjs` exists in the project (a ready-to-run build script that
  would re-translate glosses via DeepL EN-US and rewrite the HTML in place).
  It is currently UNUSED. User has not decided whether to keep or delete it.
  Running it requires `DEEPL_API_KEY=... node deepl_translate.mjs`.
  Caveat: it translates the headword and would replace the richer
  "primary / alternative" dual-gloss format with DeepL's single rendering.
- Word data is best-effort curated (spot-checked, not authoritative) — worth
  proofreading before relying on any single entry.
- Reaching ~1000 words is intended via the import feature over time.

## How to verify
- Syntax: extract the `<script>` block and `node --check`.
- Logic: the SRS picker/scheduler and synonym-leak fix have been tested with
  standalone Node harnesses (see prior chat). No automated test files are
  committed.
- Manual: open the HTML in a browser; check a card renders in Swedish, TTS 🔊
  works, cheat button reveals English, and repetition favors missed words.

## Files
- `index.html` — the app (only file needed to use it).
- `deepl_translate.mjs` — optional, unused DeepL build script.
- `PROJECT_SUMMARY.md` — this file.
