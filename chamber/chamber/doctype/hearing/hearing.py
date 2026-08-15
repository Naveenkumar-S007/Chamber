import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class Hearing(Document):
	def validate(self):
		self.set_next_hearing_on_matter()

	def set_next_hearing_on_matter(self):
		"""Surface the upcoming hearing date on the matter."""
		pass  # handled in on_update

	def sync_timeline_entry(self):
		"""Hearings always appear on the matter timeline."""
		existing = frappe.db.get_value(
			"Timeline Entry",
			{"reference_doctype": "Hearing", "reference_name": self.name},
			"name",
		)
		title = f"Hearing — {self.purpose or 'Court hearing'}"
		if existing:
			entry = frappe.get_doc("Timeline Entry", existing)
			entry.entry_date = self.hearing_date or getdate()
			entry.title = title
			entry.description = self.outcome
			entry.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.legal_matter,
					"entry_date": self.hearing_date or getdate(),
					"event_type": "Hearing",
					"title": title,
					"description": self.outcome,
					"source": self.source,
					"reference_doctype": "Hearing",
					"reference_name": self.name,
				}
			).insert(ignore_permissions=True)


def on_update(doc, method=None):
	doc.sync_timeline_entry()
