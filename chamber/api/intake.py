import frappe
from frappe import _


@frappe.whitelist()
def get_available_templates(vertical=None, matter_type=None):
	"""Published intake templates, optionally filtered by vertical / matter type."""
	filters = {"status": "Published", "active": 1}
	if vertical:
		filters["vertical"] = vertical
	if matter_type:
		filters["matter_type"] = matter_type
	return frappe.get_all(
		"Intake Form Template",
		filters=filters,
		fields=["name", "template_name", "vertical", "matter_type", "description"],
		order_by="template_name",
	)


@frappe.whitelist()
def get_form(template=None, vertical=None, matter_type=None):
	"""Return an intake form template with its field definitions for dynamic rendering."""
	template_name = template
	if not template_name:
		filters = {"status": "Published", "active": 1}
		if vertical:
			filters["vertical"] = vertical
		if matter_type:
			filters["matter_type"] = matter_type
		rows = frappe.get_all("Intake Form Template", filters=filters, fields=["name"], order_by="modified desc", limit=1)
		if not rows:
			frappe.throw(_("No published intake form found for the given vertical / matter type."))
		template_name = rows[0].name

	doc = frappe.get_doc("Intake Form Template", template_name)
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"vertical": doc.vertical,
		"matter_type": doc.matter_type,
		"description": doc.description,
		"fields": doc.get_fields_dict(),
	}


@frappe.whitelist()
def submit(legal_matter, intake_form_template, responses, submission_date=None, status="Submitted"):
	"""Create (or update) an Intake Submission from the rendered form values."""
	import json

	from frappe.utils import getdate, nowdate

	if isinstance(responses, str):
		responses = json.loads(responses)

	matter = frappe.get_doc("Legal Matter", legal_matter)
	template = frappe.get_doc("Intake Form Template", intake_form_template)

	# Re-submitting? Update the existing submitted record for this template-matter pair.
	existing = frappe.db.get_value(
		"Intake Submission",
		{"legal_matter": legal_matter, "intake_form_template": intake_form_template, "status": "Submitted"},
		"name",
	)
	doc = frappe.get_doc("Intake Submission", existing) if existing else frappe.new_doc("Intake Submission")
	doc.update(
		{
			"legal_matter": legal_matter,
			"intake_form_template": intake_form_template,
			"vertical": matter.vertical,
			"submission_date": getdate(submission_date) if submission_date else getdate(),
			"status": status,
		}
	)
	doc.responses = []
	for f in template.fields:
		value = responses.get(f.fieldname)
		if value in (None, ""):
			continue
		doc.append(
			"responses",
			{
				"fieldname": f.fieldname,
				"label": f.label,
				"value": value if not isinstance(value, (dict, list)) else json.dumps(value),
				"section": f.section,
			},
		)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	doc.apply_to_matter()
	return {"name": doc.name, "legal_matter": legal_matter}
