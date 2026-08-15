"""eCourts CNR sync client.

Pulls the full case-status bundle (next hearing date, case stage, judge,
order-sheet history where digitized) for a CNR from the eCourts National
Judicial Data Grid (NJDG) public API.

The public eCourts endpoint requires an `app_code` issued by the eCourts
portal (services.ecourts.gov.in). Configure it in Chamber Settings; without
it the sync fails gracefully and matters fall back to manual entry.
"""
import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, now_datetime

import requests

DEFAULT_API_URL = "https://services.ecourts.gov.in/ecourtindia_v6/api/casestatus_particularscnrp.php"

FIELD_MAP = {
	"cnr_number": "cnr_number",
	"case_number": "case_no",
	"case_year": "case_year",
	"case_type": "case_type",
	"case_status": "case_status",
	"case_stage": "case_stage",
	"next_hearing_date": "next_hearing_date",
	"first_hearing_date": "first_hearing_date",
	"decision_date": "decision_date",
	"court_no": "court_no",
	"judge": "judge",
	"petitioner": "petitioner",
	"respondent": "respondent",
	"filing_number": "filing_number",
}


def get_settings():
	return frappe.get_single("Chamber Settings")


def fetch_case_status(cnr):
	"""Call the eCourts API for a CNR. Returns the parsed status payload."""
	settings = get_settings()
	if not settings.ecourts_app_code:
		frappe.throw(
			_("eCourts sync is not configured. Set the eCourts App Code in Chamber Settings first.")
		)
	url = settings.ecourts_api_url or DEFAULT_API_URL
	resp = requests.get(
		url,
		params={"cnr_number": cnr, "app_code": settings.ecourts_app_code},
		timeout=30,
		headers={"User-Agent": "Mozilla/5.0 (compatible; Chamber/0.1)"},
	)
	resp.raise_for_status()
	payload = resp.json()
	if not payload or payload.get("status") is None:
		return None
	return payload.get("status")


def parse_hearing_date(value):
	if not value:
		return None
	try:
		return getdate(value)
	except Exception:
		return None


def sync_matter(legal_matter, commit=True):
	"""Sync one matter's CNR and update matter / hearing / timeline / log."""
	from chamber.chamber.doctype.ecourts_sync_log.ecourts_sync_log import ECourtsSyncLog

	matter = frappe.get_doc("Legal Matter", legal_matter)
	if not matter.cnr_number:
		return {"status": "No Data", "message": "Matter has no CNR number"}

	try:
		status = fetch_case_status(matter.cnr_number)
	except Exception as e:
		write_log(matter, "Failed", error=str(e), auto=False)
		matter.last_sync = now_datetime()
		matter.last_sync_status = "Failed"
		matter.save(ignore_permissions=True)
		return {"status": "Failed", "message": str(e)}

	if not status:
		write_log(matter, "No Data", error="No status returned for CNR", auto=False)
		matter.last_sync = now_datetime()
		matter.last_sync_status = "No Data"
		matter.save(ignore_permissions=True)
		return {"status": "No Data", "message": "No status returned for CNR"}

	changed = apply_status_to_matter(matter, status)
	next_hearing = parse_hearing_date(status.get("next_hearing_date"))
	if next_hearing:
		upsert_hearing(matter, next_hearing, status)
	create_timeline_entries(matter, status, changed)
	fetch_ordersheet_entries(matter)

	write_log(matter, "Success", response=status, auto=False)
	matter.last_sync = now_datetime()
	matter.last_sync_status = "Success"
	matter.save(ignore_permissions=True)
	msg = _("Case stage: {0}").format(status.get("case_stage") or status.get("case_status") or "updated")
	return {"status": "Success", "message": msg}


def apply_status_to_matter(matter, status):
	changed = []
	for field, key in FIELD_MAP.items():
		value = status.get(key)
		if value is None:
			continue
		value = str(value).strip()
		if not value or value.lower() in ("null", "none"):
			continue
		if field == "case_number":
			value = f"{status.get('case_type', '')} {value}/{status.get('case_year', '')}".strip()
		if getattr(matter, field, None) != value:
			setattr(matter, field, value)
			changed.append(field)
	return changed


def upsert_hearing(matter, hearing_date, status):
	existing = frappe.db.get_value(
		"Hearing",
		{"legal_matter": matter.name, "hearing_date": hearing_date, "source": "eCourts"},
		"name",
	)
	judge = status.get("judge")
	fields = {
		"legal_matter": matter.name,
		"hearing_date": hearing_date,
		"purpose": "eCourts synced hearing",
		"source": "eCourts",
		"judge": judge,
		"court": matter.court,
	}
	if existing:
		doc = frappe.get_doc("Hearing", existing)
		doc.update(fields)
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Hearing", **fields}).insert(ignore_permissions=True)


def create_timeline_entries(matter, status, changed):
	stage = status.get("case_stage") or status.get("case_status")
	if stage and not frappe.db.exists(
		"Timeline Entry",
		{"legal_matter": matter.name, "title": ["like", f"%{stage}%"]},
	):
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": matter.name,
				"entry_date": getdate(),
				"event_type": "Milestone",
				"title": f"Case stage updated — {stage}",
				"source": "eCourts",
			}
		).insert(ignore_permissions=True)
	if changed:
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": matter.name,
				"entry_date": getdate(),
				"event_type": "Order",
				"title": "eCourts sync updated case details",
				"description": "Updated: " + ", ".join(changed),
				"source": "eCourts",
			}
		).insert(ignore_permissions=True)


def fetch_ordersheet_entries(matter):
	"""Best-effort order-sheet history fetch (configurable endpoint).

	Order sheets are not part of the core case-status bundle; where the
	configured endpoint returns entries they are posted to the timeline as
	Order events and deduplicated by the entry text.
	"""
	settings = get_settings()
	url = settings.ecourts_ordersheet_url
	if not url or not matter.cnr_number:
		return
	try:
		resp = requests.get(
			url,
			params={"cnr_number": matter.cnr_number, "app_code": settings.ecourts_app_code or ""},
			timeout=30,
		)
		resp.raise_for_status()
		payload = resp.json()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Chamber order-sheet fetch")
		return

	entries = payload.get("order_sheets") or payload.get("data") or []
	if isinstance(entries, dict):
		entries = [entries]
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		entry_date = parse_hearing_date(entry.get("order_date") or entry.get("date"))
		text = str(entry.get("order_text") or entry.get("order") or "").strip()
		if not text:
			continue
		if frappe.db.exists(
			"Timeline Entry",
			{"legal_matter": matter.name, "title": ["like", f"%{text[:60]}%"], "event_type": "Order"},
		):
			continue
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": matter.name,
				"entry_date": entry_date or getdate(),
				"event_type": "Order",
				"title": "Order sheet entry — " + text[:80],
				"description": text[:2000],
				"source": "eCourts",
			}
		).insert(ignore_permissions=True)



def write_log(matter, status, response=None, error=None, auto=False):
	frappe.get_doc(
		{
			"doctype": "eCourts Sync Log",
			"legal_matter": matter.name,
			"cnr_number": matter.cnr_number,
			"sync_date": now_datetime(),
			"status": status,
			"response": frappe.as_json(response) if response else None,
			"error": error,
			"auto": auto,
		}
	).insert(ignore_permissions=True)


def poll_auto_sync_matters():
	"""Scheduled job: refresh every matter marked for eCourts auto-sync."""
	if not get_settings().enable_ecourts_sync:
		return
	matters = frappe.db.get_all(
		"Legal Matter",
		filters={"ecourts_auto_sync": 1, "cnr_number": ["is", "set"]},
		fields=["name"],
	)
	for row in matters:
		try:
			sync_matter(row.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"eCourts auto-sync failed for {row.name}")
	frappe.db.commit()
