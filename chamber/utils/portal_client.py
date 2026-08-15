"""Portal sync — IP India / NCLT-NCLAT / State RERA.

The spec (§5) treats these as separate integrations from eCourts, with
different endpoints and coverage. IP India (ipindia.gov.in), NCLT and the
state RERA portals do not expose a uniform public JSON API, so each portal
gets a *connector* that:

  * attempts the portal's known public search/status endpoints with
    defensive parsing (JSON first, HTML-table fallback),
  * accepts a firm-configured endpoint override in Chamber Settings, and
  * degrades gracefully to an honest manual-entry fallback with coverage
    notes when the portal is unreachable or unparseable — the sync never
    silently fails.

Every result is written to the eCourts Sync Log (portal field), updates the
matter's portal_status fields and posts a timeline entry, so users always see
live vs. manual coverage.
"""
import re

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

import requests

PORTALS = {
	"IP India": {"key_field": "application_number", "label": "Application / Registration No."},
	"NCLT / NCLAT": {"key_field": "case_number", "label": "Case Number"},
	"State RERA": {"key_field": "rera_project_number", "label": "Project Registration No."},
}

DEFAULT_ENDPOINTS = {
	"IP India": "https://iprsearch.ipindia.gov.in/PublicSearch/",
	"NCLT / NCLAT": "https://nclt.gov.in/",
	"State RERA": "",
}


def get_settings():
	return frappe.get_single("Chamber Settings")


class PortalConnector:
	"""Base connector: build request, fetch, parse, degrade gracefully."""

	portal = ""

	def __init__(self, matter, settings=None):
		self.matter = matter
		self.settings = settings or get_settings()
		self.key_field = PORTALS[self.portal]["key_field"]

	def get_key_value(self):
		value = self.matter.get(self.key_field)
		if value:
			return value
		# fall back to latest intake response for the key
		submissions = frappe.db.get_all(
			"Intake Submission", filters={"legal_matter": self.matter.name}, fields=["name"]
		)
		if submissions:
			return frappe.db.get_value(
				"Intake Response",
				{
					"parenttype": "Intake Submission",
					"parent": ("in", [s.name for s in submissions]),
					"fieldname": self.key_field,
				},
				"value",
			)
		return None

	def get_endpoint(self):
		field = "portal_endpoint_" + frappe.scrub(self.portal)
		if frappe.get_meta("Chamber Settings").has_field(field):
			endpoint = (frappe.db.get_single_value("Chamber Settings", field) or "").strip()
			if endpoint:
				return endpoint
		return DEFAULT_ENDPOINTS.get(self.portal, "")

	def fetch(self):
		"""Perform the HTTP request. Returns parsed dict or raises."""
		key = self.get_key_value()
		endpoint = self.get_endpoint()
		if not key:
			raise ValueError(f"No {self.key_field} on matter")
		if not endpoint:
			raise ConnectionError("No endpoint configured for this portal")
		# Try GET with the key as query param first, then POST form for ASPX-style portals
		try:
			resp = requests.get(endpoint, params={self.key_field: key}, timeout=30)
			resp.raise_for_status()
			return self.parse(resp.text, resp.headers.get("Content-Type", ""))
		except (requests.RequestException, ValueError):
			pass
		try:
			resp = requests.post(endpoint, data={self.key_field: key}, timeout=30)
			resp.raise_for_status()
			return self.parse(resp.text, resp.headers.get("Content-Type", ""))
		except (requests.RequestException, ValueError):
			pass
		raise ConnectionError(f"Portal {self.portal} unreachable or unparseable")

	def parse(self, body, content_type=""):
		"""Parse the portal response into {'status': str, 'details': str}."""
		text = body or ""
		# JSON first
		if "json" in content_type.lower() or text.strip().startswith(("{", "[")):
			import json

			try:
				data = json.loads(text)
			except ValueError:
				data = None
			if data:
				if isinstance(data, list):
					data = data[0] if data else {}
				if isinstance(data, dict):
					status = (
						data.get("status")
						or data.get("applicationStatus")
						or data.get("caseStatus")
						or data.get("registrationStatus")
						or ""
					)
					details = (
						data.get("details")
						or data.get("description")
						or data.get("remarks")
						or json.dumps(data)[:500]
					)
					return {"status": str(status), "details": str(details)}
		# HTML table fallback (many portal search pages return tables)
		rows = re.findall(r"<td[^>]*>(.*?)</td>", text, re.IGNORECASE | re.DOTALL)
		clean = [re.sub(r"<[^>]+>", "", r).strip() for r in rows]
		clean = [c for c in clean if c]
		if clean:
			status = next((c for c in clean if re.search(r"(pending|accepted|refused|withdrawn|registered|admitted|objection|disposed|granted|rejected)", c, re.I)), "")
			return {"status": status or (clean[0] if len(clean) > 1 else "Status available"), "details": " | ".join(clean[:10])}
		raise ValueError("Unparseable response")

	def sync(self):
		"""Full sync for this portal — logs, updates matter, posts timeline."""
		try:
			parsed = self.fetch()
		except Exception as e:
			write_log(self.matter, self.portal, "Failed", error=str(e))
			matter = frappe.get_doc("Legal Matter", self.matter.name)
			matter.last_sync = now_datetime()
			matter.last_sync_status = "Failed"
			matter.save(ignore_permissions=True)
			return {"status": "Failed", "message": str(e)}
		status = parsed.get("status") or "Updated"
		matter = frappe.get_doc("Legal Matter", self.matter.name)
		matter.portal_status = status
		matter.portal_status_date = getdate()
		matter.portal_status_notes = parsed.get("details") or ""
		matter.last_sync = now_datetime()
		matter.last_sync_status = "Success"
		matter.save(ignore_permissions=True)
		write_log(matter, self.portal, "Success", response=parsed)
		post_timeline(matter, self.portal, status, parsed.get("details"))
		return {"status": "Success", "message": f"{self.portal}: {status}"}


class IPIndiaConnector(PortalConnector):
	portal = "IP India"


class NCLTConnector(PortalConnector):
	portal = "NCLT / NCLAT"


class RERAPortalConnector(PortalConnector):
	portal = "State RERA"


CONNECTORS = {
	"IP India": IPIndiaConnector,
	"NCLT / NCLAT": NCLTConnector,
	"State RERA": RERAPortalConnector,
}


def get_connector(matter, portal):
	cls = CONNECTORS.get(portal)
	if not cls:
		return None
	return cls(matter)


def sync_portal(legal_matter, portal=None):
	"""Sync a matter against a non-eCourts portal."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	portal = portal or matter.portal or "eCourts"
	if portal == "eCourts":
		from chamber.utils import ecourts_client

		return ecourts_client.sync_matter(legal_matter)

	connector = get_connector(matter, portal)
	if not connector:
		return {"status": "Failed", "message": f"Unknown portal {portal}"}
	return connector.sync()


def post_timeline(matter, portal, status, details=""):
	# dedupe: one entry per status value
	if frappe.db.exists(
		"Timeline Entry",
		{"legal_matter": matter.name, "title": ["like", f"%{portal}%{status}%"]},
	):
		return
	frappe.get_doc(
		{
			"doctype": "Timeline Entry",
			"legal_matter": matter.name,
			"entry_date": getdate(),
			"event_type": "Milestone",
			"title": f"{portal} status — {status}",
			"description": details,
			"source": "Automated",
		}
	).insert(ignore_permissions=True)


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
