# Editorial access (no database mode)

## Named identities and roles

Set \`AYURSUTRA_ADMIN_USERS_JSON\` as a server-side JSON array with:

\`\`\`json
[{"id":"senior-editor","role":"publisher","sha256":"64 lowercase hexadecimal SHA-256 hash of a random private bearer token"}]
\`\`\`

Generate each independent 48+-character token with a secure password manager, hash locally using SHA-256, and set the JSON configuration in the Cloudways application's private environment. Never commit bearer tokens or hashes derived from weak passwords to the repository. Supported roles:
- viewer: read editorial queue and import counts.
- editor: viewer rights plus create drafts, import chapters/questions and create notes.
- publisher: editor rights plus publish content.
- admin: publisher rights plus read the last 50 private audit events.

**Migration:** When AYURSUTRA_ADMIN_USERS_JSON is non-empty, the legacy AYURSUTRA_ADMIN_TOKEN is explicitly disabled. Without named configuration, the legacy token still has full admin privileges for backwards compatibility. Remove it once named credentials are verified. The current browser token input accepts either credential; the backend is authoritative.

Each successful authenticated administrative mutation is logged to \`server/storage/private/audit/events.jsonl\` (or configured private storage), recording UTC time, actor ID, role, route, HTTP method and status. No token or request body is logged. Files are private and must remain outside public_html, with backups and rotation procedures. Audit is an operational log, **not** a tamperproof forensic ledger. A missing audit write causes a server-side error and an operator must verify whether the operation applied.

A 15-minute per-IP failed-token throttle is present; it does not replace edge protections and can cause lockouts behind shared IPs. Configure Cloudways/WAF rate rules with trusted proxy topology. A bearer token is still a shared secret, not an authenticated browser session with MFA: require a modern identity provider, per-user session controls, revocation and professional review before high-risk multi-editor production use.
