# Classical corpus ingestion report — 25 October 2026

The public read-only source corpus is independent of the editorial chapters collection. All source text is attributed and is not medical guidance.

| Book | Source-mapped chapters | Source text units | Source | Verification |
|---|---:|---:|---|---|
| charaka-samhita | 120 | 10385 | https://github.com/sarit/SARIT-corpus/blob/master/carakasamhita.xml | Source transcription; not independently proofread |
| sushruta-samhita | 186 | 9888 | https://github.com/sarit/SARIT-corpus/blob/master/susrutasamhita.xml | Source transcription; not independently proofread |
| ashtanga-hridaya | 120 | 7726 | https://github.com/sarit/SARIT-corpus/blob/master/astangahrdayasamhita.xml | Source transcription; not independently proofread |
| ashtanga-sangraha | 150 | 22670 | https://github.com/sarit/SARIT-corpus/blob/master/astangasangraha.xml | Source transcription; not independently proofread |
| madhava-nidana | 68 | 3286 | https://sa.wikisource.org/wiki/माधवनिदानम्?oldid=75848 | Devanagari transcription, not independently proofread; chapter 1 cross-referenced to mirror |

All **644** diagnostic/classical chapters now have machine-accessible source text (120 Charaka + 186 Sushruta + 120 Hridaya + 150 Sangraha + 68 Madhava), totaling **53,955 source text units**. These are not necessarily one verse each. The 70 Madhava reference entries include 68 diagnostic chapters and two appendices, which remain index/source pointers. Wikisource revision 75848 supplied 3,265 original text lines across chapters 2–68, pinned by source checksum. Chapter 1 retains 21 cross-reference passages. These are original transcription artifacts, not independently verified Sanskrit editions or Ayana-owned translations.

SARIT sources are separately attributed under CC BY-SA 3.0, and the 67 additional Wikisource chapters are separately attributed CC BY-SA 4.0. These source files should retain original attribution and ShareAlike obligations when redistributed.

**Actual Ayana content migration still pending:** all 16 catalogue examination sets have zero imported questions, notes collection is empty, and Ayana-owned commentary, audio and media assets remain absent. Nothing was filled with synthetic questions or unlicensed modern translations.

Next steps: scholarly source reconciliation and verse/chapter numbering QA, owner-provided Ayana learning content export, and staging/browser deployment tests.
