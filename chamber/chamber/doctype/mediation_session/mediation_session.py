import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class MediationSession(Document):
	def on_update(self):
		self.sync_timeline_entry()

	def sync_timeline_entry(self):
		existing = frappe.db.get_value(
			"Timeline Entry",
			{"reference_doctype": "Mediation Session", "reference_name": self.name},
			"name",
		)
		title = f"Mediation session — {self.purpose or 'session'} ({self.status})"
		if existing:
			entry = frappe.get_doc("Timeline Entry", existing)
			entry.entry_date = self.session_date or getdate()
			entry.title = title
			entry.description = self.outcome
			entry.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.legal_matter,
					"entry_date": self.session_date or getdate(),
					"event_type": "Task",
					"milestone": "Mediation",
					"title": title,
					"description": self.outcome,
					"source": "Manual",
					"reference_doctype": "Mediation Session",
					"reference_name": self.name,
				}
			).insert(ignore_permissions=True)
