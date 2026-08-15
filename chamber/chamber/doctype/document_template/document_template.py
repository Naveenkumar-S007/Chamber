import re

import frappe
from frappe.model.document import Document

MERGE_TAG_RE = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")


class DocumentTemplate(Document):
	def validate(self):
		self.sync_merge_tags()

	def sync_merge_tags(self):
		"""Auto-discover {{ merge_tags }} used in the template body."""
		if not self.template_body:
			return
		tags = []
		for match in MERGE_TAG_RE.finditer(self.template_body):
			path = match.group(1)
			if path not in [t.tag for t in tags]:
				tags.append(path)
		self.merge_tags = []
		for tag in tags:
			source = self.resolve_tag_source(tag)
			self.append(
				"merge_tags",
				{
					"tag": tag,
					"source": source,
					"description": "Merge tag used in template body",
				},
			)

	def resolve_tag_source(self, tag):
		"""Best-effort mapping of a merge tag to where the value comes from."""
		known = {
			"client_name": "Legal Matter → Client (Legal Party)",
			"client_phone": "Legal Matter → Client contact",
			"client_email": "Legal Matter → Client email",
			"client_address": "Legal Matter → Client address",
			"matter": "Legal Matter name",
			"matter_title": "Legal Matter → Matter Title",
			"vertical": "Legal Matter → Legal Vertical",
			"matter_type": "Legal Matter → Matter Type",
			"case_number": "Legal Matter → Case Number",
			"cnr_number": "Legal Matter → CNR Number",
			"filing_date": "Legal Matter → Filing Date",
			"cause_of_action_date": "Legal Matter → Cause of Action Date",
			"claim_amount": "Legal Matter → Claim Amount",
			"suit_valuation": "Legal Matter → Suit Valuation",
			"court": "Legal Matter → Court",
			"court_bench": "Legal Matter → Court/Bench",
			"judge_name": "Legal Matter → Judge",
			"assigned_advocate": "Legal Matter → Assigned Advocate",
			"opposing_counsel": "Legal Matter → Opposing Counsel",
			"fir_number": "Legal Matter → FIR Number",
			"police_station": "Legal Matter → Police Station",
			"fir_date": "Legal Matter → Date of FIR",
			"sections_charged": "Legal Matter → Sections Charged",
			"bail_status": "Legal Matter → Bail Status",
			"custody_status": "Legal Matter → Custody Status",
			"investigating_officer": "Legal Matter → Investigating Officer",
			"statutory_deadline_date": "Legal Matter → Statutory Deadline",
			"statutory_deadline_note": "Legal Matter → Deadline Note",
			"next_hearing_date": "Legal Matter → Next Hearing",
			"today": "Today's date",
		}
		return known.get(tag, "Legal Matter merge context / intake responses")
