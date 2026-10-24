# AyurSutra — research-to-design decisions (24 October 2026)

The benchmarks below were inspected through publicly accessible pages and documentation; they are not claims of access to proprietary UX research, conversion rates or private application screens.

| Product | Direct source | Publicly observable pattern | AyurSutra decision |
| --- | --- | --- | --- |
| Ayana Academy | https://ayanaayurveda.com/learn/ | Classical books + search + notes + MCQ/viva navigation | Book/section/chapter/verse hierarchy; one primary discovery search |
| AIIA Ayurvidya | https://ayurvidya.aiia.gov.in/enroll-user | LMS courses combining multimedia and interactive material | Standalone study area distinct from classical library |
| The Ayurveda Experience | https://theayurvedaexperience.com/products/ayurveda-you | Course outline, instructor information, testimonials, instant-access product offer | A future course detail template with sample syllabus, credential and clear entitlement |
| The Ayurveda Experience subscription | https://theayurvedaexperience.com/products/ayurveda-all-access-oto | Bundled video access and annual offer | Plan for bundles only after verifiable licensed premium lessons exist |
| Readwise Reader | https://docs.readwise.io/reader/docs | Distraction-free, customizable reading, highlights, notes, saved library | Reading-room layout, script/font controls, bookmarks, source citation |
| Readwise Pricing | https://readwise.io/pricing | Free trial followed by feature comparison and annual/monthly choice | Pricing comparison template; NO active trials, checkout or fictional prices |
| Duolingo | https://www.duolingo.com/help/what-is-a-streak | Small daily goal and repeat practice mechanics | Daily three-question sample activity; no manufactured streak counts |

## Screen hierarchy

1. Homepage — editorial hero → utility action strip → primary texts → featured verse → study cards → research list.
2. Library — catalogue search, focus filter, contextual description, explicit source status.
3. Text details — immutable passage + transliteration switch + accessible controls + reference + bookmarking.
4. Daily study — one-question-at-a-time MCQ, immediate explanation, review result; don't reward guessing using artificial scarcity.
5. Research desk — categorized links, publication provenance and explicit evidence constraints.
6. Membership — free access clearly first; experimental premium offer is labelled as a future concept.
7. My Library — low-friction saved passages; clear note that bookmarks are browser-only and not synced.
8. Admin — password-like server-configured token, draft review then publish; editor sees canonical HTTPS source.

## Important flows

- Discovery: Home → Library → Book → Verse → Bookmark → Saved Library → Reopen.
- Study: Home → Daily Learning → Pick answer → Reveal explanation → Next → Summary.
- Research: Home → Research → Category filter → Original source (external site opens in new tab).
- Editorial: Admin unlock → Create draft with original HTTPS source → Review link → Publish → Public research page.
- Monetization *later*: Membership compare → Sample lesson → Clear terms → Account → Billing through a compliant provider. **Not implemented or offered today**.

## Safety and design guardrails

- Original Sanskrit remains distinct from English educational glosses, with linked source.
- Modern health evidence and traditional doctrine are labelled separately, particularly when discussing interventions.
- No paywall blocking public-domain classics; additional value comes from authored educational services.
- High contrast, keyboard controls, visible focus, reduced-motion support, responsive layouts.
- No fabricated review counts, member numbers, false urgency, or unverified clinical efficacy claims.

## Acceptance checklist for production

- [ ] Automated frontend build and accessibility test after dependency installation.
- [ ] Responsive screenshots at 375, 768 and 1440 pixels from a running Vite site.
- [ ] Tested cross-origin restrictions and HTTPS headers on target hosting.
- [ ] Approved and fully ingested corpus, with edition provenance audit.
- [ ] Account/session architecture, role management, and audit logs.
- [ ] Privacy policy, cookie notice (if applicable), editorial policy and corrections process.
- [ ] Payment terms and compliant checkout only when a real premium product is ready.
