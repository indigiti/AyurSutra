# SARIT corpus import recovery — 25 October 2026

Read-only structured Sanskrit editions were imported without modifying the editorial `chapters.json` collection. PHP readers prefer editor-published content; otherwise they serve the attributed source transcription.

| Book | Mapped chapters | Source text units |
| --- | ---: | ---: |
| Charaka Samhita | 120 | 10,385 |
| Sushruta Samhita | 186 | 9,888 |
| Ashtanga Hridaya | 120 | 7,726 |
| Ashtanga Sangraha | 150 | 22,670 |
| **Total** | **576** | **50,669** |

Text units are original XML paragraph, prose or verse-group records, **not** verified one-to-one Sanskrit ślokas. Charaka's 120 mapped source chapters differ from its 126-chapter catalogue; one extra source division was not mapped in Sushruta. Source text has not been independently proofread. The four editions contain IAST transliteration only; no verified translation, Devanagari conversion or commentary.

Source link and CC BY-SA 3.0 licence are preserved in each book record and server/storage/corpus/LICENSE-SOURCE.md. CC ShareAlike obligations apply to the adapted source text. Original files: https://github.com/sarit/SARIT-corpus.

API endpoints: `GET /api/v1/corpus/status`, `GET /api/v1/sections`, `GET /api/v1/chapters/{book}/{section}/{chapter}`, `GET /api/v1/search`. File datasets live under private server/storage/corpus; optionally override with `AYURSUTRA_CORPUS_PATH`. The JSON storage adapter and MariaDB migration boundary are unchanged.

**Not imported:** Madhava Nidana's complete text; Ayana's owned translations, notes and viva banks; complete AIAPGET papers and answer keys; images and audio. Accurate source exports or a usable licensed text file are necessary to complete these areas.
