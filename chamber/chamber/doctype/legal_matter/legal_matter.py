import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_years, date_diff, getdate, now_datetime


class LegalMatter(Document):
	def validate(self):
		self.compute_limitation()
		self.validate_matter_type_vertical()
		self.sync_client_from_parties()

	def after_insert(self):
		self.create_registration_timeline_entry()

	# ---------------------------------------------------------------- helpers
	def compute_limitation(self):
		"""Auto-compute limitation expiry from cause-of-action date and flag risk."""
		if self.cause_of_action_date and self.limitation_years:
			expiry = add_years(getdate(self.cause_of_action_date), int(self.limitation_years))
			self.limitation_expiry_date = expiry
			self.limitation_flagged = date_diff(expiry, getdate()) <= 0

	def validate_matter_type_vertical(self):
		if self.matter_type:
			mt = frappe.db.get_value("Matter Type", self.matter_type, "vertical")
			if mt and mt != self.vertical:
				frappe.throw(
					_("Matter Type {0} belongs to vertical {1}, not {2}").format(
						self.matter_type, mt, self.vertical
					)
				)

	def sync_client_from_parties(self):
		"""Keep the Client link in step with the parties child table."""
		client_party = None
		for p in self.parties:
			if p.role == "Client" or p.is_client:
				client_party = p.party
				break
		if client_party and self.client != client_party:
			self.client = client_party

	def create_registration_timeline_entry(self):
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.name,
				"entry_date": getdate(),
				"event_type": "Milestone",
				"milestone": "Matter Registered",
				"title": "Matter registered",
				"source": "Manual",
			}
		).insert(ignore_permissions=True)

	def get_merge_context(self):
		"""Structured data pulled into document templates / merge engine.

		Returns a flat dict of fields available as {{ ... }} merge tags plus
		named sub-dicts for parties, hearings and intake responses.
		"""
		ctx = {
			"matter": self.name,
			"matter_title": self.matter_title,
			"vertical": frappe.db.get_value("Legal Vertical", self.vertical, "vertical_name") if self.vertical else "",
			"matter_type": frappe.db.get_value("Matter Type", self.matter_type, "matter_type") if self.matter_type else "",
			"status": self.status,
			"case_number": self.case_number,
			"cnr_number": self.cnr_number,
			"case_category": self.case_category,
			"filing_date": self.filing_date,
			"cause_of_action_date": self.cause_of_action_date,
			"claim_amount": self.claim_amount,
			"suit_valuation": self.suit_valuation,
			"court": frappe.db.get_value("Court", self.court, "court_name") if self.court else "",
			"court_bench": self.court_bench,
			"judge_name": self.judge_name,
			"assigned_advocate": self.assigned_advocate,
			"opposing_counsel": self.opposing_counsel,
			"fir_number": self.fir_number,
			"police_station": self.police_station,
			"fir_date": self.fir_date,
			"sections_charged": self.sections_charged,
			"bail_status": self.bail_status,
			"custody_status": self.custody_status,
			"investigating_officer": self.investigating_officer,
			"statutory_deadline_date": self.statutory_deadline_date,
			"statutory_deadline_note": self.statutory_deadline_note,
			"today": frappe.utils.today(),
		}
		# Parties by role (first match wins) + full list
		ctx["parties"] = []
		by_role = {}
		for p in self.parties:
			party = frappe.db.get_value(
				"Legal Party", p.party, ["party_name", "party_type", "contact_number", "email", "address"], as_dict=True
			)
			if not party:
				continue
			party["role"] = p.role
			ctx["parties"].append(party)
			by_role.setdefault(p.role or "Other", party)
		for role, party in by_role.items():
			key = "party_" + role.lower().replace(" ", "_")
			ctx[key] = party.get("party_name", "")
		if self.client:
			client = frappe.db.get_value(
				"Legal Party", self.client, ["party_name", "contact_number", "email", "address"], as_dict=True
			)
			if client:
				ctx["client_name"] = client.party_name
				ctx["client_phone"] = client.contact_number
				ctx["client_email"] = client.email
				ctx["client_address"] = client.address
		# Hearings
		ctx["hearings"] = frappe.db.get_all(
			"Hearing",
			filters={"legal_matter": self.name},
			fields=["hearing_date", "purpose", "outcome", "next_hearing_date"],
			order_by="hearing_date desc",
		)
		ctx["next_hearing_date"] = self.get_next_hearing_date()
		# Latest intake responses merged flat (last submission wins)
		intake = frappe.db.get_all(
			"Intake Response",
			filters={"parenttype": "Intake Submission", "parent": ("in", self.get_intake_submission_names())},
			fields=["fieldname", "value"],
		)
		for r in intake:
			if r.value:
				ctx.setdefault("intake_" + r.fieldname, r.value)
		return ctx

	def get_intake_submission_names(self):
		return [
			d.name
			for d in frappe.db.get_all(
				"Intake Submission", filters={"legal_matter": self.name}, fields=["name"]
			)
		]

	def get_next_hearing_date(self):
		row = frappe.db.get_all(
			"Hearing",
			filters={"legal_matter": self.name, "hearing_date": (">=", getdate())},
			fields=["hearing_date"],
			order_by="hearing_date asc",
			limit=1,
		)
		return row[0].hearing_date if row else None

	def sync_ecourts(self, commit=True):
		"""Fetch latest case status bundle for this matter's CNR via eCourts."""
		from chamber.utils import ecourts_client

		return ecourts_client.sync_matter(self.name, commit=commit)

	# ---------------------------------------------------------------- buttons
	@frappe.whitelist()
	def sync_from_ecourts(self):
		self.reload()
		result = self.sync_ecourts()
		frappe.msgprint(
			_("eCourts sync {0}: {1}").format(result.get("status"), result.get("message", "")),
			alert=True,
		)
		return result


# ---------------------------------------------------------------- doc events
def validate(doc, method=None):
	pass


def on_update(doc, method=None):
	"""Keep matter-level derived fields fresh after any child update."""
	if not doc.flags.in_insert and doc.limitation_years and doc.cause_of_action_date:
		doc.compute_limitation()
