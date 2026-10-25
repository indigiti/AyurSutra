# Technical architecture and migration seam

## Runtime topology

- Public UI: React 19, TypeScript, Vite 6, Tailwind CSS 4 + premium editorial CSS.
- SEO: prerendered HTML for the nine public routes; dynamic interactions hydrate client-side. Set `SITE_URL` during build to generate sitemap and canonical links.
- Offline/PWA: manifest, icon, service worker with cached previously visited public routes. API, admin and private paths are never cached.
- API: independent PHP 8.2+ modules; no Slim dependency required. JSON /api/v1/ endpoints.
- Persistence today: PHP FileStore. Every collection mutation uses exclusive `flock` and an atomic file rename. Private admin identity tokens support named reviewer/editor/publisher/admin roles, and successful administrative mutations append to a minimal private operational audit file. Neither mechanism replaces independently audited production identity/session management.
- Editorial security: private backend directory, HTTPS bearer admin token set server-side, no payment handling, no public editorial writes.
- Optional later: Redis cache/queues, R2 storage, FastAPI for image/computer vision tasks, Capacitor and Tauri.

## Data migrations

The application depends on `StoreInterface` (`read` and atomic `mutate`), currently implemented by `FileStore`. A future `MariaDBStore` can implement the same interface, with explicit schema migrations for `books`, `editions`, `sections`, `chapters`, `passages`, `translations`, `source_licences`, `articles`, `users`, `bookmarks` and `audit_log`.

### API available now

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | /api/v1/status | Health and storage type |
| GET | /api/v1/books | Edition catalogue |
| GET | /api/v1/books/:slug/verses | File-backed sample passages |
| GET | /api/v1/articles | Published editorial items |
| GET | /api/v1/admin/status | Bearer-authenticated readiness |
| GET | /api/v1/admin/articles | Entire editorial queue |
| POST | /api/v1/admin/articles | Write draft |
| POST | /api/v1/admin/articles/:id/publish | Publish reviewed draft |

Source-text search now supports an optional private sharded index with IAST-normalized and Devanagari text lookups, alongside published chapters, exams and notes. It is not an external scalable search service. Account synchronization, billing, production AI, Redis and R2 are not configured. The UI uses a small explicitly attributed starter dataset. The importer writes unpublished staging material to enable a later editorial import screen.

## Source integrity

Original editions and modern translations are separate intellectual-property assets. Never mix commentary with source passages or silently replace verse numbering. Each imported unit records source ID, its TEI hierarchy, SHA-256 and original text. Staged files are private and require a manual approval process before public display. See `docs/sources.json`.

## Optional Python manuscript-image inspector

`services/vision/main.py` is an independently deployable FastAPI service. With the `AYURSUTRA_VISION_KEY` configured on that separate host, it accepts authenticated PNG/JPEG images under 8 MB and calculates dimensions plus a heuristic Laplacian blur/focus metric. It does **not** run OCR, publish text or diagnose patients; no deployment or model dependency is assumed. It can be introduced later behind the PHP administrative workflow.

## Mobile packaging

`capacitor.config.ts` identifies the Android/iOS app and consumes the compiled `dist/` assets. Native targets must be added and validated in separate SDK-equipped environments. The web PWA is the supported initial distribution. Tauri remains a future option for desktop packaging.
