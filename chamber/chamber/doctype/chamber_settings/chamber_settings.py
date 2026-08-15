import frappe
from frappe import _
from frappe.model.document import Document


class ChamberSettings(Document):
	def validate(self):
		self.validate_ecourts()
		self.validate_ai()

	def validate_ecourts(self):
		if self.enable_ecourts_sync and not self.ecourts_app_code:
			self.enable_ecourts_sync = 0
			frappe.msgprint(
				_("eCourts sync requires an App Code — disabled until configured."),
				alert=True,
			)

	def validate_ai(self):
		if self.enable_ai and (not self.ai_api_url or not self.ai_api_key):
			self.enable_ai = 0
			frappe.msgprint(
				_("AI requires an API URL and key — disabled until configured."),
				alert=True,
			)
