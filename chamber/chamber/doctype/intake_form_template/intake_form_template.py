import json

import frappe
from frappe.model.document import Document


class IntakeFormTemplate(Document):
	def validate(self):
		self.validate_fieldnames()

	def validate_fieldnames(self):
		seen = set()
		for f in self.fields:
			if not f.fieldname:
				frappe.throw(frappe._("Fieldname is mandatory for field '{0}'").format(f.label))
			if f.fieldname in seen:
				frappe.throw(frappe._("Duplicate fieldname '{0}' in intake template").format(f.fieldname))
			seen.add(f.fieldname)

	def get_fields_dict(self):
		"""JSON-serializable representation used by the dynamic form renderer."""
		out = []
		for f in self.fields:
			out.append(
				{
					"fieldname": f.fieldname,
					"label": f.label,
					"fieldtype": f.fieldtype,
					"options": f.options,
					"reqd": f.reqd,
					"depends_on": f.depends_on,
					"section": f.section,
					"description": f.description,
				}
			)
		return out
