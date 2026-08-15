"""Neethi AI client — vertical-aware drafting / extraction / summarization.

Uses an OpenAI-compatible chat completions endpoint configured in Chamber
Settings. All prompts carry the matter's vertical + matter type so the same
engine behaves differently per practice area.
"""
import frappe
from frappe import _

import requests

SENSITIVE_VERTICALS = {"Family Law"}


def get_settings():
	return frappe.get_single("Chamber Settings")


def is_enabled():
	settings = get_settings()
	return settings.enable_ai and settings.ai_api_key and settings.ai_api_url


def _ensure_enabled():
	if not is_enabled():
		frappe.throw(
			_("AI is not configured. Enable it and set the API URL / key in Chamber Settings first.")
		)


def chat(system_prompt, user_prompt, max_tokens=None):
	"""Single chat completion call against the configured provider."""
	settings = get_settings()
	_ensure_enabled()
	url = settings.ai_api_url.rstrip("/")
	if not url.endswith("/chat/completions"):
		url = url + "/chat/completions"
	headers = {
		"Authorization": f"Bearer {settings.ai_api_key}",
		"Content-Type": "application/json",
	}
	payload = {
		"model": settings.ai_model or "gpt-4o-mini",
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		"temperature": 0.3,
		"max_tokens": max_tokens or settings.ai_max_tokens or 2000,
	}
	resp = requests.post(url, json=payload, headers=headers, timeout=120)
	resp.raise_for_status()
	data = resp.json()
	choices = data.get("choices") or []
	if not choices:
		frappe.throw(_("AI provider returned no completion"))
	return choices[0].get("message", {}).get("content", "").strip()


def vertical_prompt(matter):
	"""Context describing the vertical / matter type for AI prompts."""
	vertical = frappe.db.get_value("Legal Vertical", matter.vertical, "vertical_name") if matter.vertical else "General"
	return f"Legal practice area: {vertical}. Matter type: {matter.matter_type or 'General'}."


def is_sensitive_vertical(vertical_name):
	if not vertical_name:
		return False
	# DV / 498A / adoption sub-types sit under Family Law — treat the whole vertical sensitively
	return vertical_name in SENSITIVE_VERTICALS


def draft_content(matter, template_body, instructions="", vertical=None):
	"""AI-assisted drafting: fill narrative sections while the merge engine
	handles structured fields. AI drafts structure/facts, not legal argument
	strategy — flag where lawyer input is needed."""
	_ensure_enabled()
	context = vertical_prompt(matter)
	system = (
		"You are a legal drafting assistant for an Indian law firm. "
		+ context
		+ (
			" This is a SENSITIVE matter (domestic violence / 498A / adoption). "
			"Draft carefully and conservatively; never invent facts or legal arguments. "
			"Clearly mark any place where lawyer input is required as [LAWYER REVIEW REQUIRED]."
			if is_sensitive_vertical(frappe.db.get_value("Legal Vertical", matter.vertical, "vertical_name"))
			else " Draft conservatively; never invent facts or legal arguments. "
			"Mark any place needing lawyer input as [LAWYER REVIEW REQUIRED]."
		)
	)
	deadline_context = ""
	if matter.statutory_deadline_date:
		deadline_context = (
			"\nDEADLINE AWARENESS: this matter has a statutory deadline of "
			+ str(matter.statutory_deadline_date)
			+ (f" ({matter.statutory_deadline_note})." if matter.statutory_deadline_note else ".")
			+ " If the draft concerns filing or notice, keep the timeline in mind and flag any window that may be closing."
		)
	user = (
		"Using the structured data already merged into the template below, produce the final legal document text. "
		"Do not add invented facts, case citations or legal arguments beyond what the data supports."
		+ deadline_context
		+ "\n\n"
		+ ("Additional instructions: " + instructions + "\n\n" if instructions else "")
		+ "TEMPLATE:\n" + template_body
	)
	return chat(system, user)


def extract_fields(matter, text, field_hint=""):
	"""Bulk-read: extract vertical-specific fields from an uploaded case file."""
	_ensure_enabled()
	vertical = frappe.db.get_value("Legal Vertical", matter.vertical, "vertical_name") if matter.vertical else "General"
	system = (
		"You extract structured case data from legal documents for an Indian law firm. "
		f"Practice area: {vertical}. Return ONLY a JSON object of extracted fields. "
		"Use exactly these keys when found: "
		"fir_number, police_station, fir_date, sections_charged, bail_status, custody_status, "
		"investigating_officer, cheque_number, cheque_date, cheque_amount, drawee_bank, dishonour_reason, "
		"demand_notice_date, parties, claim_amount, cause_of_action_date, "
		"marriage_date, personal_law, court, case_number, filing_date, renewal_due_date, "
		"application_number, project_registration_number, other. "
		"Do not guess — omit keys you cannot find."
	)
	user = (
		"Extract fields from the document text below"
		+ (f" (expected fields: {field_hint})." if field_hint else ".")
		+ "\n\nDOCUMENT TEXT:\n" + text[:12000]
	)
	raw = chat(system, user)
	try:
		import json

		return json.loads(raw)
	except Exception:
		return {"raw": raw}


def summarize(matter, text, focus=""):
	"""Summarize a case file / contract / correspondence into a short brief."""
	_ensure_enabled()
	context = vertical_prompt(matter)
	system = (
		"You summarize legal case material for hearing prep. " + context + " "
		"Return a concise structured summary: key facts, parties, issues, deadlines, and action items."
	)
	user = (
		"Summarize the following material"
		+ (f" focusing on: {focus}." if focus else ".")
		+ "\n\nMATERIAL:\n" + text[:15000]
	)
	return chat(system, user)
