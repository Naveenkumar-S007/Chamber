import frappe
from frappe import _

# Universal base section prepended to every vertical intake form (spec §2.1)
BASE_FIELDS = [
	{
		"fieldname": "client_name",
		"label": "Client Name",
		"fieldtype": "Data",
		"reqd": 1,
		"section": "Client Details",
		"description": "Captured once and linked to the matter as the client party.",
	},
	{
		"fieldname": "client_phone",
		"label": "Phone",
		"fieldtype": "Data",
		"reqd": 0,
		"section": "Client Details",
	},
	{
		"fieldname": "client_email",
		"label": "Email",
		"fieldtype": "Data",
		"reqd": 0,
		"section": "Client Details",
	},
	{
		"fieldname": "client_address",
		"label": "Address",
		"fieldtype": "Small Text",
		"reqd": 0,
		"section": "Client Details",
	},
]


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
	"""Return an intake form template with field definitions for dynamic rendering.

	The universal base section (client details) is prepended to every form.
	"""
	template_name = template
	if not template_name:
		filters = {"status": "Published", "active": 1}
		if vertical:
			filters["vertical"] = vertical
		if matter_type:
			filters["matter_type"] = matter_type
		rows = frappe.get_all(
			"Intake Form Template", filters=filters, fields=["name"], order_by="modified desc", limit=1
		)
		if not rows:
			frappe.throw(_("No published intake form found for the given vertical / matter type."))
		template_name = rows[0].name

	doc = frappe.get_doc("Intake Form Template", template_name)
	fields = list(BASE_FIELDS) + doc.get_fields_dict()
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"vertical": doc.vertical,
		"matter_type": doc.matter_type,
		"description": doc.description,
		"fields": fields,
	}


@frappe.whitelist()
def submit(legal_matter, intake_form_template, responses, submission_date=None, status="Submitted"):
	"""Create (or update) an Intake Submission from the rendered form values,
	apply base client fields to the matter's client party, and copy responses
	onto matching Legal Matter fields."""
	import json

	from frappe.utils import getdate

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
	all_fields = list(BASE_FIELDS) + [f for f in template.fields]
	for f in all_fields:
		value = responses.get(f.fieldname)
		if value in (None, ""):
			continue
		doc.append(
			"responses",
			{
				"fieldname": f.fieldname,
				"label": f.get("label") or f.label,
				"value": value if not isinstance(value, (dict, list)) else json.dumps(value),
				"section": f.get("section") or f.section,
			},
		)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	doc.apply_to_matter()

	# Universal base fields → client Legal Party
	apply_client_base_fields(matter, responses)

	return {"name": doc.name, "legal_matter": legal_matter}


def apply_client_base_fields(matter, responses):
	"""Create/update the client Legal Party from the base intake fields."""
	client_name = (responses.get("client_name") or "").strip()
	if not client_name:
		return
	party = frappe.db.get_value("Legal Party", {"party_name": client_name}, "name")
	if not party and responses.get("client_email"):
		party = frappe.db.get_value("Legal Party", {"email": responses["client_email"]}, "name")
	if not party and responses.get("client_phone"):
		party = frappe.db.get_value("Legal Party", {"contact_number": responses["client_phone"]}, "name")
	if party:
		party_doc = frappe.get_doc("Legal Party", party)
	else:
		party_doc = frappe.new_doc("Legal Party")
		party_doc.party_name = client_name
	party_doc.contact_number = responses.get("client_phone") or party_doc.contact_number
	party_doc.email = responses.get("client_email") or party_doc.email
	party_doc.address = responses.get("client_address") or party_doc.address
	party_doc.role = "Client"
	party_doc.is_client = 1
	party_doc.flags.ignore_permissions = True
	party_doc.save(ignore_permissions=True)
	if not party:
		party = party_doc.name

	matter = frappe.get_doc("Legal Matter", matter.name)
	if matter.client != party:
		matter.client = party
		# also reflect in the parties child table
		if not any(p.party == party for p in matter.parties):
			matter.append("parties", {"party": party, "role": "Client", "is_client": 1})
		matter.flags.ignore_permissions = True
		matter.save(ignore_permissions=True)
