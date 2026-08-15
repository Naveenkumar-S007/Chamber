import frappe
from frappe import _

from chamber.api import documents as documents_api
from chamber.utils import ai_client


@frappe.whitelist()
def draft(legal_matter, document_template, instructions=None):
	"""AI-assisted document generation (merge + narrative fill)."""
	return documents_api.render_document(
		legal_matter=legal_matter,
		document_template=document_template,
		use_ai=True,
		ai_instructions=instructions or "",
	)


@frappe.whitelist()
def extract(legal_matter, file_url=None, text=None, field_hint=None):
	"""Bulk-read: extract vertical-specific fields from an uploaded case file.

	Pass either file_url (attached file) or raw text. For PDFs a best-effort
	text extraction is attempted (PyPDF2 if installed).
	"""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	content = text or ""
	if file_url and not content:
		content = read_attached_text(file_url)
	if not content.strip():
		frappe.throw(_("No readable text found. Upload a text/docx file or pass text directly."))
	result = ai_client.extract_fields(matter, content, field_hint=field_hint)
	return {"fields": result}


@frappe.whitelist()
def apply_extraction(legal_matter, file_url=None, text=None, field_hint=None):
	"""Bulk-read auto-fill: extract vertical-specific fields from an uploaded
	case file and apply them onto the Legal Matter / intake responses."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	content = text or ""
	if file_url and not content:
		content = read_attached_text(file_url)
	if not content.strip():
		frappe.throw(_("No readable text found."))
	result = ai_client.extract_fields(matter, content, field_hint=field_hint)

	# Route extracted values via the vertical's admin-configurable field map
	# (targets: Legal Matter fields or Intake Response fieldnames).
	field_map = ai_client.get_extraction_map(matter.vertical)
	meta = frappe.get_meta("Legal Matter")
	applied, skipped = [], []
	intake_updates = []
	if field_map:
		for mapping in field_map:
			value = (result or {}).get(mapping["source_key"])
			if not isinstance(value, str) or not value.strip() or value.lower() in ("null", "none"):
				continue
			if mapping["target_doctype"] == "Legal Matter" and meta.has_field(mapping["target_field"]):
				setattr(matter, mapping["target_field"], value)
				applied.append(f"matter.{mapping['target_field']}")
			elif mapping["target_doctype"] == "Intake Response":
				intake_updates.append((mapping["target_field"], mapping["source_key"], value))
			else:
				skipped.append(mapping["source_key"])
	else:
		# No map configured: apply to matter fields that share the same name.
		for key, value in (result or {}).items():
			if not isinstance(value, str) or not value.strip():
				continue
			if meta.has_field(key) and value.lower() not in ("null", "none"):
				setattr(matter, key, value)
				applied.append(key)
			else:
				skipped.append(key)

	if applied:
		matter.flags.ignore_permissions = True
		matter.save(ignore_permissions=True)

	# Write intake-targeted extractions into an Intake Submission (draft) so
	# they flow into the timeline/deadline engines (e.g. IP renewal_due_date).
	if intake_updates:
		write_intake_responses(legal_matter, intake_updates)
		applied += [f"intake.{field}" for field, _, _ in intake_updates]

	if applied:
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": legal_matter,
				"entry_date": frappe.utils.today(),
				"event_type": "Task",
				"title": "AI bulk-read applied",
				"description": "Extracted fields applied: " + ", ".join(applied),
				"source": "AI",
			}
		).insert(ignore_permissions=True)
	return {"extracted": result, "applied": applied, "skipped": skipped}


def write_intake_responses(legal_matter, updates):
	"""Append AI-extracted values to the latest Intake Submission (draft)."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	submission = None
	names = frappe.db.get_all(
		"Intake Submission",
		filters={"legal_matter": legal_matter, "status": "Draft"},
		fields=["name"],
		order_by="modified desc",
	)
	if names:
		submission = frappe.get_doc("Intake Submission", names[0].name)
	else:
		# fall back to a submitted one, else create a new draft
		submitted = frappe.db.get_all(
			"Intake Submission", filters={"legal_matter": legal_matter}, fields=["name"], limit=1
		)
		if submitted:
			submission = frappe.get_doc("Intake Submission", submitted[0].name)
	if submission is None:
		submission = frappe.new_doc("Intake Submission")
		submission.update(
			{
				"legal_matter": legal_matter,
				"vertical": matter.vertical,
				"submission_date": frappe.utils.today(),
				"status": "Draft",
			}
		)
		# use the matter's vertical intake template if one exists
		template = frappe.db.get_value(
			"Intake Form Template",
			{"vertical": matter.vertical, "status": "Published", "active": 1},
			"name",
		)
		if template:
			submission.intake_form_template = template
	for fieldname, source_key, value in updates:
		if any(r.fieldname == fieldname for r in submission.responses):
			for r in submission.responses:
				if r.fieldname == fieldname:
					r.value = value
		else:
			submission.append(
				"responses",
				{"fieldname": fieldname, "label": source_key.replace("_", " ").title(), "value": value},
			)
	submission.flags.ignore_permissions = True
	submission.save(ignore_permissions=True)


@frappe.whitelist()
def summarize(legal_matter, file_url=None, text=None, focus=None):
	matter = frappe.get_doc("Legal Matter", legal_matter)
	content = text or ""
	if file_url and not content:
		content = read_attached_text(file_url)
	if not content.strip():
		frappe.throw(_("No readable text found."))
	return {"summary": ai_client.summarize(matter, content, focus=focus or "")}


def read_attached_text(file_url):
	"""Best-effort text extraction from an attached file."""
	content = ""
	try:
		from frappe.utils.file_manager import get_file

		_, content = get_file(file_url)
		if isinstance(content, bytes):
			content = content.decode("utf-8", errors="ignore")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Chamber AI file read")
	if file_url.lower().endswith(".pdf"):
		try:
			from PyPDF2 import PdfReader

			from frappe.utils.file_manager import get_file_path

			path = get_file_path(file_url)
			reader = PdfReader(path)
			content = "\n".join((page.extract_text() or "") for page in reader.pages)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chamber AI PDF extraction")
	return content or ""
