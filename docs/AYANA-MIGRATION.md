# Ayana → AyurSutra content migration (no database)

## Source ownership and limitations

This application supports transferring content that the Ayana operator is authorized to export. Public page indexing alone does **not** contain the full AIAPGET answer banks, chapter passages, or study notes. No real exam questions have been fabricated or recovered from incomplete snippets. The initial repository has only the three verified starter passages; all new imports are *drafts* until explicitly published.

## Option A — Admin dashboard: one chapter at a time

Open `/admin` and use **Ayana content migration** to select a `.json` file, stage a chapter, review its source, and publish. The browser upload allows at most 300 passages per file and about 1.4 MB. The status panel shows imported versus published records. A chapter file has this shape (sample structure, not a quote from the classical text):

```json
{
  "book_id": "sushruta-samhita",
  "section_slug": "sutrasthanam",
  "chapter_slug": "vedotpattyadhyayah",
  "title": "Vedotpatti",
  "source_url": "https://ayanaayurveda.com/learn/classical-texts/sushruta-samhita/",
  "passages": [
    {
      "reference": "1.1",
      "text_devanagari": "<actual source passage>",
      "text_iast": "<actual transliteration, optional>",
      "translation_en": "<authorized explanation, optional>",
      "commentary": "<authorized commentary, optional>",
      "key_terms": [{"term": "<term>", "definition": "<definition>"}]
    }
  ]
}
```

Use the exact `chapter_slug` values from `server/storage/sections.json`; some chapters are currently numbered placeholders. A mismatch is rejected rather than silently creating another page.

## Option B — Full offline export (preferred)

Prepare one JSON manifest (format `ayursutra-ay-1`) containing `chapters`, `papers`, and `notes`. All collections are optional; when supplied they are validated together before writing anything. The full importer is a Python 3 standard-library CLI without MySQL, Redis or other dependencies.

```json
{
  "format": "ayursutra-ay-1",
  "chapters": [
    {
      "book_id": "sushruta-samhita",
      "section_slug": "sutrasthanam",
      "chapter_slug": "vedotpattyadhyayah",
      "title": "Vedotpatti",
      "source_url": "https://ayanaayurveda.com/learn/classical-texts/sushruta-samhita/",
      "passages": [
        {"reference": "1.1", "text_devanagari": "<actual Sanskrit>", "text_iast": "", "translation_en": "", "commentary": "", "key_terms": []}
      ]
    }
  ],
  "papers": [
    {
      "id": "aiapget-2017",
      "questions": [
        {"id": "aiapget-2017-1", "question": "<actual question>", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "<reviewed explanation>", "subject": "General"}
      ]
    }
  ],
  "notes": [
    {"slug": "example-study-note", "title": "Example Study Note", "subject": "Shalya Tantra", "level": "BAMS", "body": "<authorized note>", "source_url": "https://ayanaayurveda.com/learn/notes/"}
  ]
}
```

**Illustrative placeholders in angle brackets above are NOT genuine migrated content.** Real papers must match the entire indexed exam question count (100 or 120, etc.) and have verified answers; an incomplete paper is rejected. Omit `papers` until the complete question set is available.

### Import workflow

1. Export the source data from the Ayana content application or CMS using its native backup/export tool. Ensure the original source URL, stable book/section/chapter identifiers, Sanskrit, available commentary, exam questions/answers and study notes are preserved.
2. Transform the export to the manifest schema above; original input can be retained privately for provenance and audit. Review rights for any third-party editions and editorial translations.
3. Run `python3 scripts/migrate-ayana.py path/to/ayana-export.json --report migration-preview.json`. This is **dry-run by default** and does not modify stored data.
4. Review errors, counts, source licensing and potential duplicates. Run `python3 scripts/migrate-ayana.py path/to/ayana-export.json --apply` only after validation.
5. On the private React admin screen publish verified chapters, complete exams and notes individually. Unpublished content is not exposed through public APIs.

The importer is idempotent on chapter and note IDs and exam paper IDs. Re-runs update drafts but **never overwrite published records**. Before writes, it creates timestamped backups under `server/storage/backups/`. Keep backups and draft content outside `public_html` in Cloudways.

### Cloudways security and rollout

Copy the JSON collections and source PHP files to the application-private storage path. Keep `AYURSUTRA_STORAGE_PATH` pointed at that folder. Avoid copying private manifests, question answer keys, draft commentary, admin secrets or backups into Vite's public assets. The HTTP chapter endpoint serves **only** published passages; exam answer keys are served only after scoring. Use production authentication and rate limiting before opening admin access. Perform a staging review before deploying to production.

### Remaining acceptance criteria

- Source export obtained and record count reconciled against Ayana's source dataset.
- Integrity checks of full Sanskrit chapter ordering, commentary, missing fields, and all 2017–2025 AIAPGET answer keys.
- Actual frontend install/build, route-by-route browser tests and Cloudways staging review.
- Post-publish search indexing, canonical URLs, and media/audio asset migration.
- Cross-collection atomic migration / rollback design before large concurrent production imports.
