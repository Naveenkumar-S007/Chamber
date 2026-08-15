"""E-signature flow — provider-agnostic adapter.

The Signature Request doctype drives the flow (send → embeddable signing
link → webhook status updates). The adapter is intentionally generic: it
POSTs the document to any REST e-signature provider configured in Chamber
Settings (DocuSign, Dropbox Sign, SignDesk, eMudhra, Aadhaar eSign via a
gateway, or a self-hosted endpoint) and maps the provider's signing URL
back into the request.

Expected provider contract (documented in README):
  POST {esign_api_url}
  Headers: Authorization: Bearer {esign_api_key}
  JSON: { "document_url": <pdf url>, "document_name": <name>,
          "signer_name": ..., "signer_email": ...,
          "callback_url": <webhook> }
  Response JSON: { "request_id": ..., "signing_url": ... }

Webhook: POST {site}/api/method/chamber.api.esign.receive_webhook
  payload: { "request_id" or "signature_request", "event" or "status" }
"""
import frappe
from frappe import _
from frappe.utils import now_datetime

import requests


def get_settings():
	return frappe.get_single("Chamber Settings")


def _ensure_configured():
	settings = get_settings()
	if not settings.enable_esign:
		frappe.throw(_("E-signature is not enabled. Turn it on in Chamber Settings first."))
	return settings


def build_callback_url(settings):
	callback = (settings.esign_callback_url or "").strip()
	if callback:
		return callback
	from frappe.utils import get_url

	return get_url("/api/method/chamber.api.esign.receive_webhook")


def send_to_provider(signature_request, settings):
	"""Create the envelope at the provider and return (request_id, signing_url)."""
	if signature_request.provider in ("Manual", ""):
		return None, None
	generated = frappe.get_doc("Generated Document", signature_request.generated_document)
	document_url = generated.attachment
	if not document_url:
		from chamber.api import documents as documents_api

		res = documents_api.generate_pdf(generated.name)
		document_url = res.get("attachment")

	url = settings.esign_api_url
	if not url:
		frappe.throw(_("Set the e-signature API URL in Chamber Settings."))
	payload = {
		"document_url": document_url,
		"document_name": generated.title,
		"signer_name": signature_request.signer_name,
		"signer_email": signature_request.signer_email,
		"callback_url": build_callback_url(settings),
	}
	headers = {"Content-Type": "application/json"}
	if settings.esign_api_key:
		headers["Authorization"] = f"Bearer {settings.esign_api_key}"
	resp = requests.post(url, json=payload, headers=headers, timeout=60)
	resp.raise_for_status()
	data = resp.json() if resp.content else {}
	return data.get("request_id"), data.get("signing_url")


def send_for_signature(legal_matter, generated_document, signer_name, signer_email, provider=None):
	"""Create a Signature Request, send it to the provider and persist the signing link."""
	settings = _ensure_configured()
	req = frappe.new_doc("Signature Request")
	req.update(
		{
			"legal_matter": legal_matter,
			"generated_document": generated_document,
			"signer_name": signer_name,
			"signer_email": signer_email,
			"provider": provider or settings.esign_provider or "Generic REST",
			"status": "Draft",
		}
	)
	req.flags.ignore_permissions = True
	req.insert(ignore_permissions=True)

	try:
		request_id, signing_url = send_to_provider(req, settings)
	except Exception as e:
		req.mark_status("Failed", notes=str(e))
		frappe.log_error(frappe.get_traceback(), "Chamber e-signature send")
		frappe.throw(_("Failed to send signature request to provider: {0}").format(e))

	req.provider_request_id = request_id
	req.signing_url = signing_url
	req.status = "Sent"
	req.sent_date = now_datetime()
	req.flags.ignore_permissions = True
	req.save(ignore_permissions=True)
	req.sync_timeline_entry("Signature request sent")

	generated = frappe.get_doc("Generated Document", generated_document)
	generated.status = "Sent"
	generated.flags.ignore_permissions = True
	generated.save(ignore_permissions=True)

	return {
		"name": req.name,
		"signing_url": signing_url,
		"status": req.status,
	}
