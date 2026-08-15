import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today


class Caveat(Document):
	def validate(self):
		if not self.valid_until and self.filed_date:
			self.valid_until = add_days(getdate(self.filed_date), 90)

	def after_insert(self):
		self.sync_timeline_entry("Caveat filed")

	def sync_timeline_entry(self, title):
		if not self.legal_matter:
			return
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.legal_matter,
				"entry_date": self.filed_date or getdate(),
				"event_type": "Filing",
				"title": title,
				"description": f"{self.caveat_number} — valid until {self.valid_until}",
				"source": "Manual",
				"reference_doctype": "Caveat",
				"reference_name": self.name,
			}
		).insert(ignore_permissions=True)

	def expire_if_due(self):
		if self.status == "Active" and self.valid_until and getdate(self.valid_until) < getdate():
			self.status = "Expired"
			self.flags.ignore_permissions = True
			self.save(ignore_permissions=True)
			self.sync_timeline_entry("Caveat expired")


def expire_overdue_caveats():
	"""Daily job: flip expired caveats to Expired status."""
	for name in frappe.db.get_all("Caveat", filters={"status": "Active"}, pluck="name"):
		try:
			frappe.get_doc("Caveat", name).expire_if_due()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Caveat expiry check")
	frappe.db.commit()
