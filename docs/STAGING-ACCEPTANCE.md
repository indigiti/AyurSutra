# AyurSutra M1–M5 release acceptance

## Automated checks
- CI: PHP syntax, JSON API/security regressions, Unicode search index, source reconciliation, TypeScript build, sitemap generation, and Chromium browser tests.
- Staging manual workflow: read-only GET requests for public routes and APIs, anonymously blocked admin access, baseline response headers, and request latency.
- Generated sharded search index: run python3 scripts/build-search-index.py after every corpus update. Store indexes outside public_html, with AYURSUTRA_SEARCH_INDEX_PATH pointing to the private output directory.

## Blocking governance/hosting requirements
1. Protect main in GitHub Settings with mandatory PR, independent review, up-to-date checks, CODEOWNERS approvals and denied force pushes. Committing CODEOWNERS does not automatically protect the branch.
2. Restrict the GitHub staging Environment with required reviewers. A workflow mentioning an environment does not configure restrictions.
3. Use an isolated Cloudways staging app with unique secrets. Back up private JSON files first. Deploy dist/ publicly and PHP source/storage privately, separated from public_html. Never expose answer keys, staging archives or tokens.
4. Use approved authorized editions only. Review chapter ordering, source credits, reuse rights and text accuracy. Source transcriptions do not constitute individually verified medical guidance.
5. Run manual Staging read-only acceptance with its exact HTTPS origin. Review artifacts, PHP status, response latency, error rate, Core Web Vitals and a realistic concurrent-user load test. The probe alone is not a load test.
6. Perform a backup restoration drill using an isolated disposable copy of staged storage. Never corrupt or overwrite the production storage as part of a test. Record restore time, snapshot version and recovered content count.
7. Record release SHA, approver, staged health evidence, backup identifier, rollback target and deployment timestamp. Promote the exact approved artifact only through authenticated Cloudways access.

## Release hold conditions
- Unprotected main, red CI, broken staged routes, exposed admin or staging credentials, or missing valid backup.
- Unmeasured staging concurrency, missing rollback demonstration, or outstanding source licences.
- Incomplete source chapter entries displayed as fully verified; exam papers published without an owner-authorized complete answer key.

## Honest content boundary
The source-mapped corpus has 120 Caraka, 186 Suśruta, 120 Aṣṭāṅgahṛdaya, 150 Aṣṭāṅgasaṅgraha chapters, and one sourced Mādhava Nidāna chapter. Sixty-nine further Mādhava catalogue entries plus full Ayana exam banks, notes, and translations require original authorized exports and scholarly review.

This workflow does not deploy code, run destructive actions, configure branch rules, or verify production traffic.

## Backup and isolated recovery verification

Keep the archive path in private storage outside `public_html` and outside the live JSON collections. On approved staging, create an exclusive snapshot with:

```bash
python3 scripts/storage-snapshot.py --snapshot --storage /private/ayursutra/storage --archive /private/backups/ayursutra-YYYYMMDD.tar.gz
python3 scripts/storage-snapshot.py --verify --archive /private/backups/ayursutra-YYYYMMDD.tar.gz
python3 scripts/storage-snapshot.py --simulate-restore --archive /private/backups/ayursutra-YYYYMMDD.tar.gz
```

The restore drill operates in a temporary isolated directory and never replaces live files. Store backups encrypted off-host with restricted access: this snapshot may contain unpublished notes, exam answer keys, and editorial audit events. SHA-256 checks detect accidental corruption but do not authenticate the backup against a malicious attacker. After restoring a real isolated staging application, run browser/API acceptance and record the recovery duration. The automated CI test uses synthetic/disposable data only.
