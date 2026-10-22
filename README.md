# Svensk ordträning – C1+

Swedish vocabulary trainer for advanced learners (CEFR C1 and above): fill-in-the-blank and synonym matching with spaced repetition.

Two levels, chosen under **Inställningar → Nivåer**:
- **C1** – 633 words from the Swedish Kelly list's C1 band.
- **Avancerat** – 121 hand-picked words rarer than C1.

**Use it:** https://jca374.github.io/swedish-c1-trainer/

## Your progress
Progress (levels, mistakes, what's due next) is saved in your own browser's local storage. Nothing is sent to a server.

- It stays on that browser and device. Another browser or computer starts fresh.
- Clearing site data or using a private window will lose it.
- To back up or move it to another device, use **Inställningar → Exportera framsteg**, then **Importera framsteg…** on the other device.

## Word sources
- **[Swedish Kelly list](https://spraakbanken.gu.se/resurser/kelly)** – Språkbanken, University of Gothenburg, CC BY-SA 3.0. It gives the C1 headwords. There is no official Council of Europe word list for Swedish. Kelly is the closest; its CEFR levels are frequency bands (1,404 words per level), not tested on learners.
- **[Folkets lexikon](https://folkets-lexikon.csc.kth.se/folkets/)** – KTH, CC BY-SA 2.5. It gives definitions, synonyms, example phrases and English translations.

The word data is therefore CC BY-SA. Entries are generated automatically, so expect the odd imperfect synonym or definition.

To rebuild the C1 list (downloads both sources and rewrites the block in `index.html`):

```
python3 build_wordlist.py            # or --dry-run to preview
```
