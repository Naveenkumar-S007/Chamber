import frappe
from frappe.model.document import Document


class GeneratedDocument(Document):
	def validate(self):
		self.enforce_review_requirement()

	def enforce_review_requirement(self):
		"""Sensitive templates always carry the mandatory-review flag until reviewed."""
		if self.requires_lawyer_review and self.status in ("Approved", "Sent", "Signed"):
			if not self.reviewed_by:
				self.status = "Review Required"

	def sync_timeline_entry(self):
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.legal_matter,
				"entry_date": self.creation.date() if hasattr(self.creation, "date") else frappe.utils.today(),
				"event_type": "Document",
				"title": f"Document generated — {self.title}",
				"description": f"From template {self.document_template} (status: {self.status})",
				"source": "Automated",
				"reference_doctype": "Generated Document",
				"reference_name": self.name,
			}
		).insert(ignore_permissions=True)


def validate(doc, method=None):
	pass
