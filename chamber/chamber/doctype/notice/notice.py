import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class Notice(Document):
	def on_update(self):
		self.sync_timeline_entry()

	def sync_timeline_entry(self):
		existing = frappe.db.get_value(
			"Timeline Entry",
			{"reference_doctype": "Notice", "reference_name": self.name},
			"name",
		)
		title = f"Notice {self.status.lower()} — {self.title}"
		if existing:
			entry = frappe.get_doc("Timeline Entry", existing)
			entry.entry_date = self.issued_date or getdate()
			entry.title = title
			entry.description = self.notes or f"To: {self.recipient}"
			entry.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.legal_matter,
					"entry_date": self.issued_date or getdate(),
					"event_type": "Notice",
					"title": title,
					"description": self.notes or f"To: {self.recipient}",
					"source": "Manual",
					"reference_doctype": "Notice",
					"reference_name": self.name,
				}
			).insert(ignore_permissions=True)
