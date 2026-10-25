# Mādhava Nidāna: controlled source recovery

The Sanskrit Wikisource page https://sa.wikisource.org/wiki/माधवनिदानम् presents **68 diagnostic headings**, followed by a subject index and source references. The frontend preserves 70 catalogue entries for navigation, but correctly distinguishes 68 chapters from two appendices. The original opening chapter is already sourced in the immutable corpus; 67 additional diagnostic chapters require source extraction and review.

A repeatable wikitext staging tool exists at \`scripts/stage-madhava-wikisource.py\`. Run on a trusted private workstation:

\`\`\`bash
python3 scripts/stage-madhava-wikisource.py --fetch --output /private/staging/madhava-drafts.json
python3 scripts/migrate-ayana.py /private/staging/madhava-drafts.json --report /private/staging/madhava-review.json
\`\`\`

The first command stages unreviewed lines for chapter IDs 02–68 without altering the live corpus or chapter publications. The second command is DRY RUN ONLY. No imported line is labelled a verified verse; line splitting may retain Wikisource markup and needs full manual reconciliation against a scholarly edition. Approve licences (Sanskrit Wikisource CC BY-SA 4.0 and any linked supplementary rights), textual source revisions, numbered chapters, Devanagari text, references and attribution before any \`--apply\` or publication. **Do not publish unreviewed extracts, current commentary or a fabricated translation.**

Only the owner/editor can approve and supply an authorized modern translation, exam bank, viva items or notes. The repository contains no such missing licensed data.

## Source recovery evidence (25 October 2026)

GitHub Actions workflow `Madhava source extraction preview` successfully downloaded Sanskrit Wikisource revision `75848` and staged **67 additional diagnostic chapter records containing 3,265 raw source lines**. The source wikitext hash was `d726be9abd42def48814c5dec748b295e6a887cc9697c9df3deec8e41bacd44b`. It also stripped MediaWiki indentation markers for legible draft text. The short-lived Actions artifact is `madhava-unreviewed-chapters`; it is not a live server import or a claim of scholastic verification.

An authorized editor can download the reviewed artifact, then use the `Bulk owner-authorized content staging` control at `/admin` to stage the `owner-review-drafts.json` file. Only chapter drafts are created; 67 chapters must receive individual source/licence attestation and publisher approval before being made public. No direct PHP console access is required for dashboard import. Keep the original source archive and editorial reviewer register for provenance.
