import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class SignatureRequest(Document):
	def validate(self):
		if self.status == "Signed" and not self.signed_date:
			self.signed_date = now_datetime()

	def after_insert(self):
		self.sync_timeline_entry("Signature request created")

	def sync_timeline_entry(self, title):
		if not self.legal_matter:
			return
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.legal_matter,
				"entry_date": frappe.utils.today(),
				"event_type": "Task",
				"title": title,
				"description": f"{self.generated_document} → {self.signer_name} ({self.signer_email}) [{self.status}]",
				"source": "Automated",
				"reference_doctype": "Signature Request",
				"reference_name": self.name,
			}
		).insert(ignore_permissions=True)

	def mark_status(self, status, notes=None):
		self.status = status
		if status == "Signed":
			self.signed_date = now_datetime()
		if notes:
			self.notes = (self.notes or "") + "\n" + notes
		self.flags.ignore_permissions = True
		self.save(ignore_permissions=True)
		self.sync_timeline_entry(f"Signature {status.lower()}")
