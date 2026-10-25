# Cloudways release ZIP (non-production package)

Every passing \`react-build\` GitHub Actions job publishes an artifact named \`ayursutra-cloudways-staging\`, containing a SHA-256 inventory and two separate top-level directories:

- \`public_html/\`: prerendered React assets, \`.htaccess\`, and the \`api/index.php\` PHP entrypoint only.
- \`private_app/\`: PHP classes and seed JSON collections including attributed Sanskrit source corpus; keep **outside** the public document root.

This package has no live editorial data, backup or deployment credentials. The seed JSON content is **not** a replacement for an existing application's databases or current private JSON collections. Do **not** overwrite a running site's data with repository seeds.

## Hosting deployment through an approved Cloudways staging app

1. Download the latest passing CI artifact. Verify its SHA256 and the bundled \`release-checksums.json\`.
2. In a dedicated, access-restricted staging application, configure its document root and place the two extracted directories according to the approved Cloudways application structure. Private files must not be web-accessible.
3. Keep the current staging storage outside the web root and back it up before changing releases. On initial deployment only, provision clean seed files from \`private_app/storage\`.
4. Configure private runtime values: \`AYURSUTRA_BACKEND_ROOT\` set to the absolute private \`private_app\` path; \`AYURSUTRA_STORAGE_PATH\` set to that application's persistent private storage; named credentials via \`AYURSUTRA_ADMIN_USERS_JSON\`; unique staging secrets. No \`VITE_\` variable for admin credentials.
5. Test \`https://STAGING_DOMAIN/api/v1/status\` and a source chapter, then perform the read-only staging acceptance workflow. Confirm that \`https://STAGING_DOMAIN/server/storage/exams.json\` and \`/private_app/storage/exams.json\` are inaccessible.
6. Do **not** promote to production until reviewer approval, complete backups, isolated restore verification, actual load measurements, SEO/UX acceptance and GitHub branch protection are recorded.

The CI artifact is not an authenticated deployment. A site's canonical URL and sitemap must be generated from its final \`SITE_URL\` during a site-specific build. Only Cloudways staging credentials and access with an authorized operator can complete a deployment.
