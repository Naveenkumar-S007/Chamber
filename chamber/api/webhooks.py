"""Push webhook receiver for court / portal status updates.

Courts and portals that cannot be polled (or that support webhooks) can push
status updates here:

    POST /api/method/chamber.api.webhooks.receive_update
    Header: X-Chamber-Secret: <webhook_secret from Chamber Settings>
    Body (JSON):
    {
        "cnr_number": "KA01-000123-2024",     # or "matter": "MATTER-...-00001"
        "case_status": "Next Hearing Listed",
        "case_stage": "For Arguments",
        "next_hearing_date": "2026-09-01",
        "judge": "Justice X",
        "order_summary": "..." ,
        "portal": "eCourts"
    }

A matching matter is updated (portal_status, next hearing, timeline entries)
and every push is recorded in the eCourts Sync Log. Unknown secrets are
rejected with 401.
"""

import hmac

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime


@frappe.whitelist(allow_guest=True)
def receive_update():
	"""Endpoint for court/portal push updates. Verifies the shared secret."""
	settings = frappe.get_single("Chamber Settings")
	secret = settings.webhook_secret or ""
	provided = frappe.get_request_header("X-Chamber-Secret") or ""

	if not secret:
		frappe.throw(_("Push webhook is not configured — set a Webhook Secret in Chamber Settings."), frappe.AuthenticationError)
	if not provided or not hmac.compare_digest(secret, provided):
		frappe.throw(_("Invalid or missing X-Chamber-Secret header."), frappe.AuthenticationError)

	payload = frappe.local.form_dict or {}
	if not payload:
		payload = frappe.request.get_json(force=True, silent=True) or {}

	matter_name = payload.get("matter")
	cnr = payload.get("cnr_number")
	if not matter_name and cnr:
		matter_name = frappe.db.get_value("Legal Matter", {"cnr_number": cnr}, "name")
	if not matter_name:
		frappe.throw(_("No matter found for cnr_number / matter in payload."))

	# Update the matter
	matter = frappe.get_doc("Legal Matter", matter_name)
	updates = []
	if payload.get("case_status"):
		matter.portal_status = payload["case_status"]
		updates.append("portal_status")
	if payload.get("portal"):
		matter.portal = payload["portal"]
		updates.append("portal")
	if payload.get("judge"):
		matter.judge_name = payload["judge"]
		updates.append("judge_name")
	matter.last_sync = now_datetime()
	matter.last_sync_status = "Success"
	matter.flags.ignore_permissions = True
	matter.save(ignore_permissions=True)

	# Upsert a Hearing for the pushed next-hearing date
	hearing_date = getdate(payload["next_hearing_date"]) if payload.get("next_hearing_date") else None
	if hearing_date:
		existing = frappe.db.get_value(
			"Hearing",
			{"legal_matter": matter_name, "hearing_date": hearing_date, "source": "Webhook"},
			"name",
		)
		fields = {
			"legal_matter": matter_name,
			"hearing_date": hearing_date,
			"purpose": payload.get("case_stage") or "Pushed by court/portal",
			"source": "Webhook",
			"judge": payload.get("judge"),
		}
		if existing:
			doc = frappe.get_doc("Hearing", existing)
			doc.update(fields)
			doc.flags.ignore_permissions = True
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc({"doctype": "Hearing", **fields}).insert(ignore_permissions=True)

	# Timeline entry (deduped per payload signature)
	title = payload.get("case_status") or payload.get("case_stage") or "Status pushed"
	if not frappe.db.exists("Timeline Entry", {"legal_matter": matter_name, "title": ["like", f"%{title[:50]}%"], "source": "Webhook"}):
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": matter_name,
				"entry_date": getdate(),
				"event_type": "Milestone",
				"title": f"Webhook status — {title}",
				"description": payload.get("order_summary") or "",
				"source": "Webhook",
			}
		).insert(ignore_permissions=True)

	# Sync log
	frappe.get_doc(
		{
			"doctype": "eCourts Sync Log",
			"legal_matter": matter_name,
			"cnr_number": matter.cnr_number,
			"portal": payload.get("portal") or "Webhook",
			"sync_date": now_datetime(),
			"status": "Success",
			"response": frappe.as_json(payload),
			"auto": True,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	return {"ok": True, "matter": matter_name, "updated": updates}
