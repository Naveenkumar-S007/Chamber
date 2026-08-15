"""Portal sync — IP India / NCLT-NCLAT / State RERA.

The spec (§5) treats these as separate integrations from eCourts, with
different endpoints and coverage. IP India (ipindia.gov.in), NCLT and the
state RERA portals do not expose a uniform public JSON API, so this module
implements:

  * a configurable best-effort HTTP fetch for portals that expose an endpoint
    (e.g. an NCLT/state portal API configured by the firm), and
  * an honest manual-entry fallback with coverage notes when no endpoint is
    configured — the sync never silently fails.

Every result is written to the eCourts Sync Log (portal field) and to the
matter timeline so users can see live vs. manual coverage.
"""
import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

import requests

PORTALS = {
	"IP India": {"key_field": "application_number", "default_url": ""},
	"NCLT / NCLAT": {"key_field": "case_number", "default_url": ""},
	"State RERA": {"key_field": "rera_project_number", "default_url": ""},
}


def get_settings():
	return frappe.get_single("Chamber Settings")


def sync_portal(legal_matter, portal=None):
	"""Sync a matter against a non-eCourts portal."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	portal = portal or matter.portal or "eCourts"
	if portal == "eCourts":
		from chamber.utils import ecourts_client

		return ecourts_client.sync_matter(legal_matter)

	meta = PORTALS.get(portal)
	if not meta:
		return {"status": "Failed", "message": f"Unknown portal {portal}"}

	key_field = meta["key_field"]
	key_value = matter.get(key_field) or frappe.db.get_value(
		"Intake Response",
		{
			"parenttype": "Intake Submission",
			"parent": ("in", [s.name for s in frappe.db.get_all("Intake Submission", filters={"legal_matter": matter.name}, fields=["name"])]),
			"fieldname": key_field,
		},
		"value",
	)

	if not key_value:
		write_log(matter, portal, "No Data", error=f"No {key_field} on matter — manual entry only.")
		return {"status": "No Data", "message": f"Set {key_field} to enable {portal} sync"}

	# Configurable endpoint for portals that expose one; falls back to manual guidance.
	settings_meta = frappe.get_meta("Chamber Settings")
	endpoint = ""
	field = "portal_endpoint_" + frappe.scrub(portal)
	if settings_meta.has_field(field):
		endpoint = (frappe.db.get_single_value("Chamber Settings", field) or "").strip()
	endpoint = endpoint or meta["default_url"]
	if not endpoint:
		write_log(
			matter,
			portal,
			"No Data",
			error=f"{portal} has no configured API endpoint — status is manual-entry fallback. Coverage varies by state/authority.",
		)
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": matter.name,
				"entry_date": getdate(),
				"event_type": "Other",
				"title": f"{portal} sync — manual entry fallback",
				"description": f"{portal} does not expose a configured endpoint for this authority. Log status manually.",
				"source": "Automated",
			}
		).insert(ignore_permissions=True)
		return {"status": "No Data", "message": f"{portal} coverage not configured — manual entry"}

	try:
		resp = requests.get(endpoint, params={key_field: key_value}, timeout=30)
		resp.raise_for_status()
		data = resp.json()
	except Exception as e:
		write_log(matter, portal, "Failed", error=str(e))
		matter.last_sync = now_datetime()
		matter.last_sync_status = "Failed"
		matter.save(ignore_permissions=True)
		return {"status": "Failed", "message": str(e)}

	write_log(matter, portal, "Success", response=data)
	matter.last_sync = now_datetime()
	matter.last_sync_status = "Success"
	matter.save(ignore_permissions=True)
	return {"status": "Success", "message": f"{portal} status refreshed"}


def write_log(matter, portal, status, response=None, error=None):
	frappe.get_doc(
		{
			"doctype": "eCourts Sync Log",
			"legal_matter": matter.name,
			"cnr_number": matter.cnr_number,
			"portal": portal,
			"sync_date": now_datetime(),
			"status": status,
			"response": frappe.as_json(response) if response else None,
			"error": error,
			"auto": False,
		}
	).insert(ignore_permissions=True)


def poll_portal_matters():
	"""Scheduled job: refresh matters flagged for non-eCourts portal sync."""
	if not get_settings().enable_portal_sync:
		return
	matters = frappe.db.get_all(
		"Legal Matter",
		filters={"portal_sync_enabled": 1, "portal": ["not in", ["", "eCourts"]]},
		fields=["name"],
	)
	for row in matters:
		try:
			sync_portal(row.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Portal sync failed for {row.name}")
	frappe.db.commit()
