import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class IntakeSubmission(Document):
	def validate(self):
		self.ensure_unique_active_submission()

	def ensure_unique_active_submission(self):
		"""Only one active (Submitted) submission per template-matter pair."""
		if self.status == "Submitted":
			existing = frappe.db.get_value(
				"Intake Submission",
				{
					"legal_matter": self.legal_matter,
					"intake_form_template": self.intake_form_template,
					"status": "Submitted",
					"name": ("!=", self.name or ""),
				},
				"name",
			)
			if existing:
				frappe.throw(
					_("A submitted intake already exists for this matter ({0}). Create a new version or edit it.").format(
						existing
					)
				)

	def apply_to_matter(self):
		"""Copy responses onto the Legal Matter where a matching field exists."""
		if not self.legal_matter:
			return
		matter = frappe.get_doc("Legal Matter", self.legal_matter)
		meta = frappe.get_meta("Legal Matter")
		changed = []
		for r in self.responses:
			if not r.value:
				continue
			if meta.has_field(r.fieldname):
				setattr(matter, r.fieldname, r.value)
				changed.append(r.fieldname)
		if matter.status == "Intake Pending":
			matter.status = "Active"
		if matter.flags.ignore_permissions is None:
			matter.flags.ignore_permissions = True
		matter.save(ignore_permissions=True)
		if changed:
			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.legal_matter,
					"entry_date": getdate(),
					"event_type": "Task",
					"title": "Intake submitted",
					"description": "Responses from intake form {} applied to the matter.".format(
						self.intake_form_template
					),
					"source": "Manual",
				}
			).insert(ignore_permissions=True)


def validate(doc, method=None):
	pass
