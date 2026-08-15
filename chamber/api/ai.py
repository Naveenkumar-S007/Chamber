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
