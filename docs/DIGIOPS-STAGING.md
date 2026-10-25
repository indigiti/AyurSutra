# AyurSutra → DigiOps staging integration

## Target from the existing DigiOps application

- Repository: \`indigiti/AyurSutra\`
- **Stage** candidate branch: \`staging/ayursutra\` (do not select the older \`main\` or \`hardening/m1-m5-release-foundation\`)
- DigiOps artifact name: \`digiops-release\`
- Application public route: \`/ayursutra/\`
- Public target: \`public_html/ayursutra/\`
- Private target: \`private_html/ayursutra/\`
- Intended target: the already configured "This Cloudways application"

DigiOps's own ReleaseManager recognizes **top-level** \`public/\` and \`private/\` directories. The GitHub Actions artifact is therefore published from the \`release/\` directory, not from a nested ZIP. The top-level \`RELEASE.json\` contains hashes for all packaged files.

The staging workflow builds Vite and the prerendered pages with \`VITE_BASE_PATH=/ayursutra/\`. React basename, API requests, web manifest, service worker, and script/static asset URLs use this prefix. PHP requests under \`/ayursutra/api/v1\` are resolved to the original versioned API.

The private payload contains \`src/\`, \`seeds/*.json\`, \`seeds/corpus/\`, and a generated \`seeds/search-index/\`. Runtime data is **never included** in the GitHub release. On first request the PHP entrypoint initializes \`private_html/ayursutra/runtime/storage/\` from the seed collections. Subsequent deploys/rollbacks preserve that directory and its editorial data, tokens, auth-limit records, and audit log.

The PHP entrypoint resolves \`private_html/ayursutra\` relative to the DigiOps public directory. Cloudways must serve both sibling folders from the same application home, as DigiOps expects. Configure PHP environment variables \`AYURSUTRA_ADMIN_USERS_JSON\` or the temporary migration-only \`AYURSUTRA_ADMIN_TOKEN\` in the private server settings; **do not enter them into DigiOps release artifacts**.

## No-console staging procedure

1. In DigiOps open **AyurSutra → Deploy** (not the Overview tab).
2. Under **Release source branch**, enter \`staging/ayursutra\`. The existing application configuration may continue to show \`main\` in Overview — staging candidates can override it without changing production routing.
3. Select **Check update**. Require a **completed / successful** \`AyurSutra checks\` workflow with an exact \`digiops-release\` artifact, verify commit SHA and artifact ID.
4. Review staged commit/artifact identity and click **Deploy**. DigiOps will validate the exact candidate and publish \`public/\` and overlay \`private/\`.
5. Open the registered staging URL at \`/ayursutra/\`, then validate \`/ayursutra/api/v1/status\`, \`/ayursutra/library/madhava-nidana\`, a reader chapter, \`/ayursutra/search\`, and \`/ayursutra/admin\`.
6. Confirm public requests to \`/ayursutra/private/\`, \`/ayursutra/seeds/\`, \`/ayursutra/server/\`, and \`/ayursutra/runtime/\` return no private data.
7. Review DigiOps **Health**, **Files**, and **Releases** for the exact commit, server-side health, immutable source files, and rollback availability.

A successful GitHub Actions workflow means a **deployment candidate** is available. It is not proof of an actual Cloudways deployment. Do not click production release or merge feature changes into main solely to make staging discoverable.
