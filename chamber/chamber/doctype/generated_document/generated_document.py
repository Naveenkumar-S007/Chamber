import frappe
from frappe import _
from frappe.model.document import Document

WORKFLOW_STATES = ["Draft", "Internal Review", "Client Review", "Finalized", "Executed"]

WORKFLOW_TRANSITIONS = {
	"Draft": ["Internal Review"],
	"Internal Review": ["Draft", "Client Review"],
	"Client Review": ["Internal Review", "Finalized"],
	"Finalized": ["Client Review", "Executed"],
	"Executed": ["Finalized"],
}


class GeneratedDocument(Document):
	def validate(self):
		self.enforce_review_requirement()
		self.validate_workflow_transition()

	def enforce_review_requirement(self):
		"""Sensitive templates always carry the mandatory-review flag until reviewed."""
		if self.requires_lawyer_review and self.status in ("Approved", "Sent", "Signed"):
			if not self.reviewed_by:
				self.status = "Review Required"
		# The workflow cannot advance past internal review without a lawyer review
		if (
			self.workflow_state in ("Client Review", "Finalized", "Executed")
			and self.requires_lawyer_review
			and not self.reviewed_by
		):
			frappe.throw(
				_("This document requires lawyer review before it can move past Internal Review.")
			)

	def validate_workflow_transition(self):
		if self.is_new():
			return
		previous = self.get_doc_before_save()
		if not previous or not previous.workflow_state:
			return
		if previous.workflow_state == self.workflow_state:
			return
		allowed = WORKFLOW_TRANSITIONS.get(previous.workflow_state, [])
		if previous.workflow_state not in WORKFLOW_STATES:
			return
		if self.workflow_state not in allowed:
			frappe.throw(
				_("Workflow cannot move from {0} to {1}. Allowed: {2}").format(
					previous.workflow_state, self.workflow_state, ", ".join(allowed)
				)
			)

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

	# ---------------------------------------------------------------- workflow
	@frappe.whitelist()
	def advance_workflow(self, target=None):
		"""Move the document through the approval workflow (validated transitions).

		Returns the new workflow stage. Legal-only stages (Finalized/Executed)
		also sync a timeline entry.
		"""
		current = self.workflow_state or "Draft"
		allowed = WORKFLOW_TRANSITIONS.get(current, [])
		if target and target not in allowed:
			frappe.throw(
				_("Workflow cannot move from {0} to {1}. Allowed: {2}").format(
					current, target, ", ".join(allowed)
				)
			)
		target = target or (allowed[0] if allowed else current)
		self.workflow_state = target
		self.flags.ignore_permissions = True
		self.save(ignore_permissions=True)
		if target in ("Finalized", "Executed"):
			from frappe.utils import getdate

			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.legal_matter,
					"entry_date": getdate(),
					"event_type": "Document",
					"title": f"Document {self.title} — {target}",
					"description": f"Workflow stage: {target} (reviewed by: {self.reviewed_by or 'n/a'})",
					"source": "Automated",
					"reference_doctype": "Generated Document",
					"reference_name": self.name,
				}
			).insert(ignore_permissions=True)
		return {"workflow_state": self.workflow_state}

	@frappe.whitelist()
	def suggest_clauses(self, query=None):
		"""Suggest reusable clauses from the Clause Library for this document.

		Matches by drafting type (Litigation vs Transactional based on the
		matter's vertical), then by tags overlapping the template / matter.
		Returns up to 8 suggestions.
		"""
		from frappe.utils import cstr

		query = (query or "").strip().lower()
		drafting_type = self._infer_drafting_type()
		filters = {"applicable_drafting_type": ["in", [drafting_type, "All"]]}
		clauses = frappe.db.get_all(
			"Clause Library",
			filters=filters,
			fields=["name", "clause_title", "clause_text", "tags"],
			limit_page_length=0,
		)
		# Rank: explicit tag/query match first, then title match, then drafting-type default
		template_name = ""
		if self.document_template:
			template_name = cstr(
				frappe.db.get_value("Document Template", self.document_template, "template_name")
			)
		haystack = (template_name + " " + self.title + " " + (self.notes or "")).lower()

		def rank(c):
			tags = cstr(c.tags or "").lower()
			score = 0
			if query and (query in tags or query in cstr(c.clause_title).lower()):
				score += 3
			for word in haystack.split():
				if len(word) > 3 and word in tags:
					score += 1
			return score

		clauses.sort(key=rank, reverse=True)
		return [
			{"name": c["name"], "clause_title": c["clause_title"], "clause_text": c["clause_text"]}
			for c in clauses[:8]
		]

	def _infer_drafting_type(self):
		vertical = None
		if self.legal_matter:
			vertical = frappe.db.get_value("Legal Matter", self.legal_matter, "vertical")
		if vertical:
			vertical_name = frappe.db.get_value("Legal Vertical", vertical, "vertical_name") or ""
		else:
			vertical_name = ""
		if any(k in vertical_name.lower() for k in ("corporate", "property", "ip")):
			return "Transactional"
		return "Litigation"


def validate(doc, method=None):
	pass
