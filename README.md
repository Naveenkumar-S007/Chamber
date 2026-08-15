# Chamber — Legal Practice & Chamber Work Management for Frappe / ERPNext v15

**Chamber** is a Frappe v15 / ERPNext v15 app that implements the **Neethi vertical-wise feature specification** for Indian legal practice:

| Feature | What it does | Where |
|---|---|---|
| **1. Conditional / Dynamic Intake Forms** | One intake engine, configured per legal vertical. Selecting a vertical reveals its field set; sub-answers branch further (e.g. "Are you complainant or accused?"). Field sets are admin-editable templates — new verticals need no code. | `Intake Form Template` → `Intake Submission`, page `intake-form`, `public/js/intake_form_renderer.js` |
| **2. Template-Based Document Generation** | Word-style templates with `{{ client_name }}`, `{{ fir_number }}`, `{{ next_hearing_date }}` merge tags. One click renders a ready-to-review document from matter data; PDF export + review routing included. | `Document Template` → `Generated Document`, `chamber/api/documents.py`, `utils/merge_engine.py` |
| **3. Litigation Timeline / Visualization** | Chronological, filterable case timeline auto-populated from hearings, documents, notices and tasks; vertical milestone paths; **statutory/limitation countdown bands** (e.g. Sec. 138 15-day window, civil limitation period). | page `matter-timeline`, `utils/timeline_engine.py`, `public/js/timeline_view.js` |
| **4. eCourts Data Fetch (CNR sync)** | Pulls the full case-status bundle (next hearing, case stage, judge, order-sheet) via CNR from the eCourts NJDG public API. Hourly auto-poll for high-volume verticals (Cheque Bounce, etc.), manual fallback + state-coverage transparency. | `utils/ecourts_client.py`, `eCourts Sync Log` |
| **5. Neethi AI** | Vertical-aware AI drafting, bulk-read extraction and summarization via any OpenAI-compatible endpoint. Sensitive matters (DV / 498A / adoption) are **flagged for mandatory lawyer review**. | `utils/ai_client.py`, `chamber/api/ai.py` |
| **Chamber Work module** | Chamber applications (discovery, interim injunction, bail, etc.) with full data model — court/judge details, hearing history log, status/urgency, court fees, automated hearing reminders. | `Chamber Application`, `Chamber Application Hearing` |
| **E-signature flow** | Provider-agnostic signing: send a generated document, get an embeddable signing link, track Signed/Declined/Viewed via webhooks. Works with DocuSign, Dropbox Sign, SignDesk, eMudhra or any REST signing API. | `Signature Request`, `chamber/api/esign.py`, `utils/esign_client.py` |
| **Self-serve template import** | Firms upload their own `.docx`/`.txt`/`.pdf` templates, extract text + merge tags, and map tags to matter/intake fields — no engineering release. | `Document Template.import_from_file` |
| **Deadline tracker** | Separate Corporate/IP-style view: statutory deadlines, limitation expiry, IP renewals and caveat expiry in one filterable countdown feed. | page `deadline-tracker`, `chamber/api/deadlines.py` |
| **Caveat tracking** | Caveat filing with 90-day validity (Sec. 148A CPC), expiry band on the timeline, daily expiry job. | `Caveat` |
| **Portal sync (IP India / NCLT / RERA)** | Portal-aware sync — configurable endpoint per portal, manual status recording (with on-form coverage transparency) where no API exists; separate from eCourts per the spec. | `utils/portal_client.py`, `Legal Matter.portal_status` |
| **Cause list / judgment copies** | Optional eCourts endpoints fetch upcoming cause-list listings (timeline Hearing events) and download digitized judgment/order PDFs (attached to the matter). | `ecourts_client.fetch_causelist_entries` / `fetch_judgment_copies` |
| **Appeal parent-child chain** | `parent_matter` link on Legal Matter keeps appeal ↔ trial-court CNR relationships visible on both timelines automatically. | `ecourts_client.sync_appellate_chain` |
| **Mediation sessions & notices** | Dedicated `Mediation Session` (each session a distinct timeline marker) and `Notice` doctypes feeding the timeline. | `Mediation Session`, `Notice` |
| **Universal base intake** | Every intake form starts with the Client Details section (name/phone/email/address), auto-creating/updating the client Legal Party. | `chamber/api/intake.py` |
| **Per-vertical AI field map** | Admin-configurable `AI Extraction Field` table on each Legal Vertical routes extracted keys to Legal Matter fields or Intake Responses. | `Legal Vertical.ai_extraction_fields` |
| **Custody-change markers** | One-click custody status logging creates a `Custody Change` timeline marker. | `Legal Matter.log_custody_change` |
| **Portal connectors** | Real connector classes for IP India / NCLT / State RERA: GET-then-POST requests with JSON + HTML-table parsing, endpoint overrides, graceful manual fallback. | `utils/portal_client.py` (`IPIndiaConnector`, `NCLTConnector`, `RERAPortalConnector`) |
| **Connection tester** | **Test Connections** button on Chamber Settings checks eCourts / e-signature / AI / portal config + reachability. | `chamber/api/settings.py` |
| **Reports** | Upcoming Hearings, Matter Status (case load by vertical/status), Deadline Watch, Court Fees. | `chamber/chamber/report/*` |
| **Dashboard** | Chamber Dashboard page with charts (matters by vertical/status, hearings in next 30 days) + headline counters (court fees, pending signatures, active caveats, flagged deadlines). | page `chamber-dashboard`, `chamber/api/dashboard.py` |
| **Print Formats** | Professional Jinja print formats for Legal Matter Summary, Chamber Application and Generated Document (incl. defined terms). | `chamber/chamber/print_format/*` |
| **Document workflow** | Draft → Internal Review → Client Review → Finalized → Executed approval workflow on Generated Documents (validated transitions; sensitive docs cannot pass Internal Review unreviewed), **Defined Terms** child table, and **clause auto-suggestion** from the Clause Library. | `Generated Document.advance_workflow` / `suggest_clauses` |
| **Row-level permissions** | Opt-in matter-level security: when enabled, Advocates see/edit only their assigned (or shared) matters, applications and documents. Preconfigured **Role Profiles** (Chamber Manager / Advocate / Filing Clerk) created on install. | `Chamber Settings.enforce_matter_level_permissions`, `setup/install.py` |
| **In-desk notifications & invites** | Desk notification feed (`notification_config` wired) for hearings/caveats/documents, plus `.ics` calendar invites attached to hearing-reminder emails. | `chamber/notifications.py`, `utils/calendar.py` |
| **Sub-type routing (spec §5.2)** | Sync logic auto-routes by matter sub-type: DV → Magistrate Court, anticipatory bail/quashing → High Court, consumer → Consumer Forum, MACT → MACT Tribunal, family → Family Court; IP/IBC/RERA matters auto-map to their portal. Court-tier mismatches block eCourts sync with a clear error. | `Legal Matter.auto_route`, `utils/ecourts_client.py` |
| **Push webhook** | Courts/portals can push updates (secret-verified): case status, next hearing, judge, order summary → matter + Hearing + timeline + sync log. | `chamber/api/webhooks.py`, `Chamber Settings.webhook_secret` |
| **Archive & legal hold** | Archive/unarchive matters with reason + audit trail; legal-hold flag (red list indicator) freezes deletion/destruction. | `Legal Matter.is_archived` / `legal_hold` |
| **Live verification** | Beyond config checks: **live eCourts CNR lookup**, **portal dry-run** (fetch + parse, zero writes) and a **Sync Extended** action (order sheets / cause list / judgment copies) — all from Desk. | `chamber/api/settings.py`, `chamber/api/ecourts.py` |
| **Tests & i18n** | 21 unit tests (merge engine, timeline bands, eCourts parsing, esign status map, portal parsing) runnable without a bench; bench-only integration tests; CI runs tests on every push; translations for hi/ta/kn/te/fr/ar/es. | `chamber/tests/`, `.github/workflows/ci.yml` |

## Vertical coverage

All **7 priority verticals** ship pre-configured (as data, editable in Desk):

1. Criminal Defense (bail / anticipatory bail / quashing / cyber / NDPS / POCSO / appeal / revision)
2. Cheque Bounce / NI Act 138 (statutory 15-day window tracking)
3. Civil Litigation (recovery, injunction, eviction, MACT, consumer…)
4. Family Law (full matter-type range — not divorce alone; sensitive-flagged)
5. Property / Real Estate Disputes (incl. RERA, partition, land acquisition)
6. Corporate / Commercial (deadline/compliance driven)
7. IP Law (deadline/renewal driven, not hearing-driven)

## Installation (bench, Frappe v15)

```bash
cd frappe-bench
bench get-app https://github.com/Naveenkumar-S007/Chamber.git
bench --site your-site install-app chamber
bench --site your-site migrate
bench build --app chamber
```

The app runs **standalone on Frappe v15** and **couples with ERPNext v15**:

- Legal Parties mirror ERPNext `Customer` / `Contact` records (hooks are guarded — no ERPNext, no problem).
- Matters can be linked to ERPNext parties through `Legal Party.erpnext_customer`.

## Configuration

1. **Roles & profiles** — `Chamber Manager`, `Advocate`, `Filing Clerk` roles **and** matching Role Profiles are created on install; assign a profile to each user in Desk. For matter-level isolation, enable **Enforce Matter-Level Permissions** in Chamber Settings (advocates then see only their assigned/shared matters).
2. **Chamber Settings** (`Chamber > Chamber Settings`):
   - **eCourts**: toggle sync, set the eCourts **App Code** (obtainable from [services.ecourts.gov.in](https://services.ecourts.gov.in)). Without an app code the sync fails gracefully and matters fall back to manual entry. Optional order-sheet / cause-list / judgments URLs enable the extended fetches (see Endpoint contracts below).
   - **E-signature**: toggle, pick provider, set API URL / key / callback secret. Webhook receiver: `POST {site}/api/method/chamber.api.esign.receive_webhook` (payload `{request_id, status}`).
   - **AI**: enable and set API URL / key / model (OpenAI-compatible — works with OpenAI, DeepSeek, Ollama, vLLM…).
   - **Portal sync**: toggle for IP India / NCLT / RERA polls; override each portal's endpoint.
   - **Push webhook**: set a **Webhook Secret** to accept court/portal push updates.
3. **Verify before going live** — use the buttons on Chamber Settings: **Test Connections** (config + reachability), **Test eCourts Lookup (Live)** (real CNR status call, read-only) and **Test Portal (Dry-run)** (connector fetch + parse, no writes).
4. **eCourts auto-sync** — tick `Auto-Sync from eCourts` on a matter; the hourly job refreshes its CNR. Sync respects the matter's auto-computed **Routing Tier** (DV → Magistrate, etc.).
5. **Portal auto-sync** — set `Portal` (IP India / NCLT / RERA) + `Auto-Sync from Portal` on the matter (portal is auto-suggested from the matter sub-type).
6. **Hearing reminders** — daily job emails the assigned advocate (with an `.ics` calendar invite) and posts an in-desk notification before upcoming chamber hearings; caveat-expiry reminders work the same way.
7. **Documents** — use **Workflow → …** on a Generated Document to move it Draft → Internal Review → Client Review → Finalized → Executed, and **Suggest Clauses** to pull relevant boilerplate from the Clause Library.
8. **Archive / hold** — **Archive Matter** (or **Unarchive**) and **Legal Hold** buttons on any matter; archived matters show a grey list indicator, legal hold a red one.

## Endpoint contracts (integration hooks)

These endpoints are **best-effort configurable hooks** — eCourts does not publish order-sheet / cause-list / judgment endpoints publicly, so they only fire when you configure a firm- or vendor-provided endpoint that returns the shapes below.

### eCourts extended fetches (Chamber Settings)

- **Order Sheet URL** — GET with `cnr_number` & `app_code` params. Expect `{"order_sheets": [{"order_date": "YYYY-MM-DD", "order_text": "..."}]}` → posted to the timeline as Order events.
- **Cause List URL** — GET with `cnr_number` & `app_code`. Expect `{"cause_list": [{"listing_date": "YYYY-MM-DD", "purpose": "..."}]}` → posted as Hearing events.
- **Judgments URL** — GET with `cnr_number` & `app_code`. Expect `{"judgments": [{"title": "...", "pdf_url": "https://..."}]}` → PDFs downloaded and attached to the matter.

Trigger them manually with the **Sync Extended** button on a Legal Matter.

### Push webhook (`chamber.api.webhooks.receive_update`)

```bash
curl -X POST https://your-site/api/method/chamber.api.webhooks.receive_update \
  -H "X-Chamber-Secret: <webhook_secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "cnr_number": "KA01-000123-2024",        // or "matter": "MATTER-2026-00001"
    "case_status": "Next Hearing Listed",
    "case_stage": "For Arguments",
    "next_hearing_date": "2026-09-01",
    "judge": "Justice A",
    "order_summary": "...",
    "portal": "eCourts"
  }'
```

Updates the matter, upserts a Hearing, posts a timeline entry and logs to the eCourts Sync Log. Wrong/missing secret → 401.

## Typical flow

1. Create a **Legal Matter** (vertical + matter type).
2. Open **Intake Form** from the matter → dynamic vertical field set → submit. Responses auto-fill matter fields.
3. **Generate Document** from the matter → pick a template (e.g. *Section 138 Legal Demand Notice*) → merge + (optional) AI fill → PDF → route for review.
4. Watch the **Matter Timeline** — hearings, filings, caveats and documents appear in order, with deadline countdown bands and the property document-collection track.
5. Mark the matter for **eCourts auto-sync** to keep case stage and hearing dates live.
6. **AI Bulk Upload** from the matter → extract FIR/sections/cheque/party data from an uploaded file and auto-fill fields.
7. **Send for Signature** from a Generated Document → signing link → webhook updates status → timeline entry.
8. Corporate/IP matters → open **Deadline Tracker** to watch statutory deadlines, limitation expiry, IP renewals and caveat expiry.

## Tests

```bash
# without a bench (uses a minimal frappe stub)
python -m unittest discover -s chamber/tests -t . -v

# inside a bench
bench --site <site> run-tests --app chamber
```

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs the unit tests on every push; the bench-only integration tests in `chamber/tests/test_integration.py` run under `bench run-tests` and skip when the bench isn't available.

## Development notes

- All vertical configuration (milestones, intake fields, templates) is **data**, stored in `chamber/setup/seed.py` and editable in Desk — the engines are vertical-agnostic (the "build once, configure per vertical" pattern).
- Scheduler: `poll_auto_sync_matters` + `poll_portal_matters` (hourly), `send_hearing_reminders` + `expire_overdue_caveats` (daily).
- Merge engine uses Frappe's Jinja — templates support filters, loops and conditionals.
- Demo data: `bench --site <site> execute chamber.setup.demo.run` (or the guarded `chamber.api.demo.load` API) seeds sample matters, courts, parties and hearings in developer mode.

## License

MIT
