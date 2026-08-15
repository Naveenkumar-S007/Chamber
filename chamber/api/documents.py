import json

import frappe
from frappe import _
from frappe.utils import getdate, today

from chamber.utils import merge_engine


@frappe.whitelist()
def get_available_templates(legal_matter):
	"""Templates usable for a matter (same vertical, published)."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	filters = {"status": "Published", "vertical": matter.vertical}
	return frappe.get_all(
		"Document Template",
		filters=filters,
		fields=["name", "template_name", "vertical", "matter_type", "drafting_type", "sensitive", "description"],
		order_by="template_name",
	)


@frappe.whitelist()
def render_document(legal_matter, document_template, title=None, use_ai=False, ai_instructions=None):
	"""Merge template with matter data and create a Generated Document."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	template = frappe.get_doc("Document Template", document_template)

	if template.status != "Published":
		frappe.throw(_("Document Template {0} is not published").format(document_template))

	merge_context = merge_engine.build_matter_context(legal_matter)
	content = merge_engine.render(template.template_body, merge_context)

	# Optional AI-assisted narrative fill on top of the structured merge
	drafted_by_ai = False
	if use_ai:
		from chamber.utils import ai_client

		content = ai_client.draft_content(
			matter=legal_matter,
			template_body=content,
			instructions=ai_instructions or "",
			vertical=matter.vertical,
		)
		drafted_by_ai = True

	doc = frappe.new_doc("Generated Document")
	doc.update(
		{
			"legal_matter": legal_matter,
			"document_template": document_template,
			"title": title or f"{template.template_name} — {matter.matter_title}",
			"content": content,
			"status": "Ready for Review",
			"requires_lawyer_review": template.sensitive or drafted_by_ai,
			"drafted_by_ai": drafted_by_ai,
			"merge_data": json.dumps(merge_engine.sanitize_merge_data(merge_context), indent=2, default=str),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.sync_timeline_entry()
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"requires_lawyer_review": doc.requires_lawyer_review,
		"content": doc.content,
	}


@frappe.whitelist()
def get_document(name):
	doc = frappe.get_doc("Generated Document", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"content": doc.content,
		"status": doc.status,
		"requires_lawyer_review": doc.requires_lawyer_review,
		"attachment": doc.attachment,
	}


@frappe.whitelist()
def generate_pdf(name):
	"""Render the generated document as a PDF and attach it to the record."""
	import frappe.utils.pdf as frappe_pdf

	doc = frappe.get_doc("Generated Document", name)
	html = f"""
	<!DOCTYPE html><html><head><meta charset="utf-8">
	<style>body {{ font-family: 'Liberation Serif', serif; font-size: 12pt; line-height: 1.5; }}
	pre {{ white-space: pre-wrap; font-family: inherit; }}</style></head>
	<body><pre>{frappe.utils.escape_html(doc.content)}</pre></body></html>
	"""
	try:
		pdf = frappe_pdf.get_pdf(html, {})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Chamber PDF generation")
		frappe.throw(_("PDF generation failed. Check that wkhtmltopdf/Playwright is configured on the bench."))

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{frappe.scrub(doc.title)}.pdf",
			"content": pdf,
			"attached_to_doctype": "Generated Document",
			"attached_to_name": doc.name,
			"is_private": 1,
		}
	)
	file_doc.save(ignore_permissions=True)
	doc.attachment = file_doc.file_url
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "attachment": doc.attachment, "file_url": file_doc.file_url}


@frappe.whitelist()
def send_for_review(name, recipients=None):
	"""Route generated document into the review flow: create a ToDo for review."""
	doc = frappe.get_doc("Generated Document", name)
	if doc.status in ("Approved", "Sent", "Signed"):
		frappe.throw(_("Document already {0}").format(doc.status))
	if not recipients:
		recipients = [frappe.session.user]
	elif isinstance(recipients, str):
		recipients = [r.strip() for r in recipients.split(",") if r.strip()]
	for recipient in recipients:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"owner": recipient,
				"assigned_by": frappe.session.user,
				"description": _("Review generated document: {0} (matter {1})").format(
					doc.title, doc.legal_matter
				),
				"reference_type": "Generated Document",
				"reference_name": doc.name,
			}
		).insert(ignore_permissions=True)
	doc.status = "Under Review"
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}
