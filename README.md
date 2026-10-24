# AyurSutra · The Living Library of Ayurveda

Premium React + TypeScript + Vite frontend and a **modular PHP 8.x API without a database**. Includes classical-text catalogue, real cited sample passages, reader controls, saved verses, daily MCQs, research area, editorial drafts and future-membership preview.

## Quick start

Requires Node.js 20+, npm and PHP 8.2+ (`json`, `mbstring`, `dom` extension for imports). In two local shells:

```bash
npm install
php -S 127.0.0.1:8000 -t server/public server/public/router.php
npm run dev
```

Visit `http://localhost:5173`. Vite proxies `/api` to the PHP development server.

`npm run build` compiles assets and prerenders 10 public React routes into `dist/`. Set `SITE_URL=https://your-public-domain.example` for canonical tags and a sitemap. `npm run preview` previews the built site. `php tests/api-smoke.php` runs a dependency-free storage test.

## Admin access

1. Set the server environment variable `AYURSUTRA_ADMIN_TOKEN` to a strong random value of at least 32 characters. Example local development: `AYURSUTRA_ADMIN_TOKEN=<your-private-token> php -S ...`.
2. Open `/admin`, enter the private token, create drafts with HTTPS source URLs, and publish reviewed drafts.
3. Never embed the token in `.env` used by Vite, in client bundle code or in GitHub. The React interface retains it only in memory; reload clears it. Production must enforce HTTPS and rate limiting at the web server or edge.

## Source texts and imports

`docs/sources.json` lists source URLs, licences, edition context and review requirements. The currently bundled reader contains **only three cited sample passages**, not the five full works. Source texts must be reviewed before import.

To stage a downloaded, authorized SARIT TEI XML file without publishing it:

```bash
php scripts/import-tei.php sarit-caraka /path/to/your/carakasamhita.xml
```

The importer validates TEI structure and stores the source hash, edition-path metadata and every extracted prose/verse group in private `server/storage/staging/`. It deliberately does not publish unreviewed text or claim reliable normalized chapter numbering. A full corpus importer/editor workflow is the next content milestone.

## Cloudways deployment

1. Build the frontend (`SITE_URL=... npm run build`). Deploy `dist/` into `public_html`.
2. Keep `server/src` and `server/storage` **outside** `public_html`, e.g. sibling `ayursutra-server`, to prevent exposing private JSON and tokens.
3. Deploy a thin `public_html/api/index.php` entry requiring the private backend PHP files; see `deploy/cloudways-api-index.php`. Configure `AYURSUTRA_BACKEND_ROOT`, `AYURSUTRA_STORAGE_PATH`, `AYURSUTRA_ADMIN_TOKEN` using server environment settings.
4. Install `deploy/cloudways-htaccess.txt` as `public_html/.htaccess` for `/api/` dispatch and React route fallback; verify API endpoints and refresh of nested routes.
5. Turn on HTTPS, request limits and IP/rate safeguards for `/api/v1/admin/*`.

## Honest scope

This is a functional **first-version foundation**, not a live production platform. Full five-text imports, editorial validation interface, account sync, production-grade admin session management, PWA offline coverage testing, paid subscriptions, Redis, R2, FastAPI, mobile app packaging and automated deployment are intentionally not yet completed. No payments, sensitive health profiles or AI-generated clinical recommendations are present.

The interface draws on patterns from Ayana Academy, AIIA Ayurvidya, Readwise Reader, Duolingo and The Ayurveda Experience; no proprietary designs or content have been copied.

## Optional integrations

- **Python/CV:** `services/vision` has a restricted FastAPI image-quality inspection endpoint (not OCR). Run and deploy it separately once its dependencies and private internal token are configured.
- **Capacitor:** `capacitor.config.ts` is included for later Android/iOS packaging (`npx cap add android` / `npx cap add ios` after installing native SDKs). No native builds are included.
- **Redis/R2:** architecture extension points only; neither Redis nor Cloudflare R2 is required for this file-backed launch and neither is configured or claimed operational.
