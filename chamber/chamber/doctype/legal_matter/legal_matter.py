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
		self.auto_route()
		self.compute_ecourts_coverage()

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

	def auto_route(self):
		"""Auto-route the sync portal and court tier by matter sub-type (spec §5.2).

		DV (PWDVA) runs through the Magistrate Court; anticipatory bail /
		quashing through the High Court; consumer/MACT through their forums;
		IP, IBC and RERA matters map to the matching portal. Only fills empty
		fields — the firm can always override.
		"""
		mt = (self.matter_type or "").lower()
		vertical = (frappe.db.get_value("Legal Vertical", self.vertical, "vertical_name") or "").lower() if self.vertical else ""
		if not self.portal:
			mt_words = set(mt.replace("(", "").replace(")", "").replace("/", " ").replace("-", " ").split())
			if any(k in mt_words for k in ("ip",)) or any(k in mt for k in ("trademark", "patent", "copyright", "design")) or "ip" in vertical.split():
				self.portal = "IP India"
			elif any(k in mt for k in ("ibc", "insolvency", "nclt", "company petition", "liquidation")) or "corporate" in vertical:
				self.portal = "NCLT / NCLAT"
			elif any(k in mt for k in ("rera", "real estate")) or "property" in vertical:
				self.portal = "State RERA"
		# Court-tier routing hint for eCourts sync
		if not self.routing_tier:
			if "domestic violence" in mt or "dv" in mt:
				self.routing_tier = "Magistrate Court"
			elif any(k in mt for k in ("anticipatory bail", "quashing", "appeal")):
				self.routing_tier = "High Court"
			elif "consumer" in mt:
				self.routing_tier = "Consumer Forum"
			elif "mact" in mt or "motor accident" in mt:
				self.routing_tier = "MACT Tribunal"
			elif "family" in vertical or any(k in mt for k in ("divorce", "maintenance", "custody", "guardianship")):
				self.routing_tier = "Family Court"

	def compute_ecourts_coverage(self):
		"""State-coverage transparency surfaced on the form: live sync vs manual fallback."""
		if self.portal and self.portal != "eCourts":
			self.ecourts_coverage = f"{self.portal}: coverage depends on the portal connector/manual entry."
			return
		if not self.cnr_number:
			self.ecourts_coverage = "No CNR number — manual entry only."
			return
		if self.court and frappe.db.get_value("Court", self.court, "ecourts_enabled") == 0:
			self.ecourts_coverage = "Court flagged as manual-entry fallback (digitization coverage varies by state/tier)."
			return
		self.ecourts_coverage = "Live eCourts sync available for this CNR."

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

	@frappe.whitelist()
	def log_custody_change(self, custody_status, note=None):
		"""Log a custody-status change as a timeline marker and update the matter."""
		if custody_status:
			self.custody_status = custody_status
		self.flags.ignore_permissions = True
		self.save(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.name,
				"entry_date": getdate(),
				"event_type": "Custody Change",
				"title": f"Custody status changed to {custody_status}",
				"description": note or "",
				"source": "Manual",
			}
		).insert(ignore_permissions=True)
		return {"custody_status": custody_status}

	@frappe.whitelist()
	def update_portal_status(self, status, status_date=None, notes=None):
		"""Record manual portal status (IP India / NCLT / RERA) when no API connector exists."""
		self.portal_status = status
		self.portal_status_date = status_date or getdate()
		self.portal_status_notes = notes
		self.flags.ignore_permissions = True
		self.save(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.name,
				"entry_date": getdate(),
				"event_type": "Milestone",
				"title": f"Portal status updated — {status}",
				"description": notes or "",
				"source": "Manual",
			}
		).insert(ignore_permissions=True)
		return {"portal_status": status}


# ---------------------------------------------------------------- doc events
def validate(doc, method=None):
	pass


def on_update(doc, method=None):
	"""Keep matter-level derived fields fresh after any child update."""
	if not doc.flags.in_insert and doc.limitation_years and doc.cause_of_action_date:
		doc.compute_limitation()


# ---------------------------------------------------------------- permissions
def _enforce_matter_level():
	"""Opt-in row-level permissions: only when enabled in Chamber Settings."""
	try:
		return bool(frappe.db.get_single_value("Chamber Settings", "enforce_matter_level_permissions"))
	except Exception:
		return False


def _is_manager(user):
	return "System Manager" in frappe.get_roles(user) or "Chamber Manager" in frappe.get_roles(user)


def _visible_matters(user):
	"""Matters this user may access under row-level permissions.

	Managers see all. Others see matters they are assigned to (advocate) plus
	everything explicitly shared with them (Frappe shares).
	"""
	if _is_manager(user):
		return None  # no restriction
	names = [
		r["name"]
		for r in frappe.db.get_all("Legal Matter", filters={"assigned_advocate": user}, fields=["name"])
	]
	shared = frappe.db.get_all(
		"DocShare",
		filters={"user": user, "share_doctype": "Legal Matter", "read": 1},
		fields=["share_name"],
	)
	names += [s["share_name"] for s in shared]
	return list({n for n in names if n})


def get_permission_query_conditions(user=None):
	"""Scope Legal Matter list/read queries when matter-level permissions are on."""
	if not _enforce_matter_level():
		return ""
	user = user or frappe.session.user
	if _is_manager(user):
		return ""
	names = _visible_matters(user)
	if not names:
		return "(1 = 0)"
	escaped = ", ".join(f"'{frappe.db.escape(n)}'" for n in names)
	return f"`tabLegal Matter`.name in ({escaped})"


def has_permission(doc=None, ptype="read", user=None):
	"""Row-level has_permission for Legal Matter."""
	if not _enforce_matter_level():
		return True
	user = user or frappe.session.user
	if _is_manager(user) or not doc:
		return True
	return doc.name in _visible_matters(user)


# ---------------------------------------------------------------- archive / hold
@frappe.whitelist()
def archive_matter(name, reason=None):
	"""Set archive / legal-hold state on a matter and record it on the timeline."""
	from frappe.utils import getdate, now_datetime

	doc = frappe.get_doc("Legal Matter", name)
	doc.is_archived = 1
	doc.archive_reason = reason or doc.archive_reason
	doc.archived_on = getdate()
	doc.archived_by = frappe.session.user
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Timeline Entry",
			"legal_matter": name,
			"entry_date": getdate(),
			"event_type": "Milestone",
			"title": "Matter archived",
			"description": reason or "",
			"source": "Manual",
		}
	).insert(ignore_permissions=True)
	return {"is_archived": 1}


@frappe.whitelist()
def unarchive_matter(name):
	doc = frappe.get_doc("Legal Matter", name)
	doc.is_archived = 0
	doc.archive_reason = ""
	doc.archived_on = None
	doc.archived_by = ""
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Timeline Entry",
			"legal_matter": name,
			"entry_date": frappe.utils.getdate(),
			"event_type": "Milestone",
			"title": "Matter unarchived",
			"source": "Manual",
		}
	).insert(ignore_permissions=True)
	return {"is_archived": 0}


@frappe.whitelist()
def set_legal_hold(name, value=1):
	"""Place or lift a legal hold (freeze document destruction/deletion)."""
	doc = frappe.get_doc("Legal Matter", name)
	doc.legal_hold = 1 if value else 0
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Timeline Entry",
			"legal_matter": name,
			"entry_date": frappe.utils.getdate(),
			"event_type": "Milestone",
			"title": f"Legal hold {'placed' if value else 'lifted'}",
			"source": "Manual",
		}
	).insert(ignore_permissions=True)
	return {"legal_hold": doc.legal_hold}
