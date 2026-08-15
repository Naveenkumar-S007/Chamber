import frappe
from frappe import _


@frappe.whitelist()
def test_connections():
	"""Verify each integration's configuration (and reachability where safe).

	Returns per-integration status so the firm can see exactly what to
	configure before going live. Live data calls are NOT made — only
	config presence + an optional lightweight reachability ping.
	"""
	settings = frappe.get_single("Chamber Settings")
	results = {}

	# ---- eCourts
	ec = {"configured": bool(settings.ecourts_app_code)}
	if ec["configured"]:
		ec["status"] = "OK — App Code set. Sync will use the NJDG case-status endpoint."
	else:
		ec["status"] = "MISSING — obtain an App Code from services.ecourts.gov.in"
	results["eCourts"] = ec

	# ---- e-signature
	es = {"configured": bool(settings.enable_esign)}
	if es["configured"]:
		missing = []
		if not settings.esign_api_url:
			missing.append("API URL")
		if not settings.esign_api_key:
			missing.append("API Key")
		if missing:
			es["configured"] = False
			es["status"] = "PARTIAL — enable_esign is on but missing: " + ", ".join(missing)
		else:
			es["status"] = "OK — provider flow ready. Webhook: /api/method/chamber.api.esign.receive_webhook"
	else:
		es["status"] = "OFF — enable and set API URL / key to send documents for signature."
	results["E-Signature"] = es

	# ---- AI
	ai = {"configured": bool(settings.enable_ai and settings.ai_api_url and settings.ai_api_key)}
	if ai["configured"]:
		ai["status"] = "OK — will call " + settings.ai_api_url.rstrip("/") + "/chat/completions with model " + (settings.ai_model or "default")
	else:
		ai["status"] = "OFF/MISSING — enable AI and set API URL + key."
	results["Neethi AI"] = ai

	# ---- portals
	for portal in ("IP India", "NCLT / NCLAT", "State RERA"):
		field = "portal_endpoint_" + frappe.scrub(portal)
		endpoint = ""
		if frappe.get_meta("Chamber Settings").has_field(field):
			endpoint = (frappe.db.get_single_value("Chamber Settings", field) or "").strip()
		results[portal] = {
			"configured": bool(endpoint),
			"status": (
				f"OK — connector will use {endpoint}"
				if endpoint
				else "DEFAULT — uses the built-in connector URL; configure an override if your portal differs"
			),
		}

	# ---- optional reachability ping (short timeout, non-fatal)
	if settings.enable_ai and settings.ai_api_url:
		results["Neethi AI"]["reachable"] = ping(settings.ai_api_url)
	if settings.ecourts_app_code:
		results["eCourts"]["reachable"] = ping(
			settings.ecourts_api_url or "https://services.ecourts.gov.in/ecourtindia_v6/api/casestatus_particularscnrp.php"
		)

	return results


def ping(url, timeout=5):
	import requests

	try:
		resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (Chamber)"})
		return {"ok": True, "http": resp.status_code}
	except Exception as e:
		return {"ok": False, "error": str(e)[:200]}
