import frappe
from frappe import _

from chamber.utils import esign_client


@frappe.whitelist()
def send_for_signature(legal_matter, generated_document, signer_name, signer_email, provider=None):
	"""Whitelisted endpoint used by the Generated Document form."""
	return esign_client.send_for_signature(
		legal_matter=legal_matter,
		generated_document=generated_document,
		signer_name=signer_name,
		signer_email=signer_email,
		provider=provider,
	)


@frappe.whitelist(allow_guest=True)
def receive_webhook():
	"""Provider webhook receiver — updates Signature Request status.

	Accepted payloads:
	  {"request_id": "...", "status": "signed"}                     (generic)
	  {"signature_request": {"request_id": "...", "status": ...}}   (Dropbox Sign style)
	  {"envelopeId": "...", "status": "completed"}                  (DocuSign style)

	The endpoint is idempotent and safe to call without auth; verify
	`esign_callback_secret` in Chamber Settings if your provider supports
	callback signing.
	"""
	from frappe.utils import cint, cstr

	payload = frappe.local.form_dict or {}
	data = payload.get("data") or payload

	# normalize nested provider payloads
	inner = data.get("signature_request") or data.get("envelope") or data
	request_id = inner.get("request_id") or inner.get("envelopeId") or data.get("request_id")
	raw_status = (
		inner.get("status")
		or inner.get("event")
		or data.get("event")
		or data.get("status")
		or ""
	).lower()

	settings = frappe.get_single("Chamber Settings")
	if settings.esign_callback_secret and not cint(frappe.local.flags.get("chamber_webhook_verified", 0)):
		secret = frappe.local.form_dict.get("secret") or data.get("secret")
		if secret != settings.esign_callback_secret:
			frappe.throw(_("Invalid webhook secret"), frappe.AuthenticationError)

	if not request_id:
		return {"ok": False, "error": "missing request_id"}

	status_map = {
		"signed": "Signed",
		"completed": "Signed",
		"sent": "Sent",
		"delivered": "Sent",
		"viewed": "Viewed",
		"declined": "Declined",
		"voided": "Expired",
		"expired": "Expired",
		"failed": "Failed",
		"error": "Failed",
		"cancelled": "Failed",
		"canceled": "Failed",
	}
	new_status = status_map.get(raw_status)
	if not new_status:
		return {"ok": True, "ignored": raw_status}

	req_name = frappe.db.get_value(
		"Signature Request", {"provider_request_id": request_id}, "name"
	)
	if not req_name:
		return {"ok": False, "error": f"no Signature Request for {request_id}"}

	req = frappe.get_doc("Signature Request", req_name)
	req.mark_status(new_status, notes=f"Webhook: {raw_status}")
	frappe.db.commit()
	return {"ok": True, "name": req_name, "status": new_status}


@frappe.whitelist()
def get_status(name):
	req = frappe.get_doc("Signature Request", name)
	return {
		"name": req.name,
		"status": req.status,
		"signing_url": req.signing_url,
		"signed_date": req.signed_date,
	}
