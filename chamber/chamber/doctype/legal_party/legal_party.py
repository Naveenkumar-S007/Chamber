import frappe
from frappe.model.document import Document


class LegalParty(Document):
	def validate(self):
		self.set_is_client_flag()

	def set_is_client_flag(self):
		"""A party linked to a Legal Matter as Client is automatically flagged."""
		if self.role == "Client" and not self.is_client:
			self.is_client = 1


def on_erpnext_customer_after_insert(customer, method=None):
	"""ERPNext coupling: when a Customer is created in ERPNext, mirror it as a Legal Party."""
	if not frappe.db.exists("Legal Party", {"erpnext_customer": customer.name}):
		party = frappe.new_doc("Legal Party")
		party.party_name = customer.customer_name or customer.name
		party.party_type = "Individual" if customer.customer_type == "Individual" else "Company"
		party.role = "Client"
		party.is_client = 1
		party.erpnext_customer = customer.name
		party.flags.ignore_permissions = True
		party.insert(ignore_permissions=True)


def on_erpnext_contact_after_insert(contact, method=None):
	"""ERPNext coupling: mirror a Contact as a Legal Party (linked to its Customer if present)."""
	linked_customer = None
	if contact.links:
		for link in contact.links:
			if link.link_doctype == "Customer":
				linked_customer = link.link_name
				break
	if not frappe.db.exists("Legal Party", {"erpnext_contact": contact.name}):
		party = frappe.new_doc("Legal Party")
		party.party_name = contact.full_name or contact.name
		party.party_type = "Individual"
		party.contact_number = contact.mobile_no or contact.phone
		party.email = contact.email_id
		party.erpnext_contact = contact.name
		if linked_customer:
			party.erpnext_customer = linked_customer
		party.flags.ignore_permissions = True
		party.insert(ignore_permissions=True)
