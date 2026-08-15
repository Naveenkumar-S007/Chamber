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

1. **Roles** — `Chamber Manager`, `Advocate`, `Filing Clerk` are created on install; assign users in Desk.
2. **Chamber Settings** (`Chamber > Chamber Settings`):
   - **eCourts**: toggle sync, set the eCourts **App Code** (obtainable from [services.ecourts.gov.in](https://services.ecourts.gov.in)). Without an app code the sync fails gracefully and matters fall back to manual entry.
   - **AI**: enable and set API URL / key / model (OpenAI-compatible — works with OpenAI, DeepSeek, Ollama, vLLM…).
3. **eCourts auto-sync** — tick `Auto-Sync from eCourts` on a matter; the hourly job refreshes its CNR.
4. **Hearing reminders** — daily job emails the assigned advocate before upcoming chamber hearings.

## Typical flow

1. Create a **Legal Matter** (vertical + matter type).
2. Open **Intake Form** from the matter → dynamic vertical field set → submit. Responses auto-fill matter fields.
3. **Generate Document** from the matter → pick a template (e.g. *Section 138 Legal Demand Notice*) → merge + (optional) AI fill → PDF → route for review.
4. Watch the **Matter Timeline** — hearings, filings and documents appear in order, with deadline countdown bands.
5. Mark the matter for **eCourts auto-sync** to keep case stage and hearing dates live.

## Development notes

- All vertical configuration (milestones, intake fields, templates) is **data**, stored in `chamber/setup/seed.py` and editable in Desk — the engines are vertical-agnostic (the "build once, configure per vertical" pattern).
- Scheduler: `poll_auto_sync_matters` (hourly) and `send_hearing_reminders` (daily).
- Merge engine uses Frappe's Jinja — templates support filters, loops and conditionals.

## License

MIT
