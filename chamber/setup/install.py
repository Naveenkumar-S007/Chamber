import json

import frappe
from frappe import _


def before_install():
	pass


def after_install():
	create_roles()
	create_role_profiles()
	seed_master_data()
	setup_default_settings()
	ensure_chamber_workspace()


def ensure_chamber_workspace():
	"""Create the Chamber workspace if it doesn't exist yet.

	Workspace JSON sync can be unreliable in Frappe v15 (the file is found
	but the doc is never inserted).  Building it programmatically guarantees
	the sidebar entry and page exist after every install / migrate.
	"""
	if frappe.db.exists("Workspace", "Chamber"):
		return

	content_blocks = [
		{"id": "hdr1", "type": "header", "data": {"text": "<span class=\"h4\"><b>Shortcuts</b></span>", "col": 12}},
		{"id": "sc1", "type": "shortcut", "data": {"shortcut_name": "New Legal Matter", "col": 3}},
		{"id": "sc2", "type": "shortcut", "data": {"shortcut_name": "New Chamber Application", "col": 3}},
		{"id": "sc3", "type": "shortcut", "data": {"shortcut_name": "Chamber Settings", "col": 3}},
		{"id": "sp1", "type": "spacer", "data": {"col": 12}},
		{"id": "hdr2", "type": "header", "data": {"text": "<span class=\"h4\"><b>Reports & Masters</b></span>", "col": 12}},
		{"id": "card1", "type": "card", "data": {"card_name": "Matters", "col": 4}},
		{"id": "card2", "type": "card", "data": {"card_name": "Masters", "col": 4}},
		{"id": "card3", "type": "card", "data": {"card_name": "Intake & Forms", "col": 4}},
		{"id": "sp2", "type": "spacer", "data": {"col": 12}},
		{"id": "hdr3", "type": "header", "data": {"text": "<span class=\"h4\"><b>Documents & eCourts</b></span>", "col": 12}},
		{"id": "card4", "type": "card", "data": {"card_name": "Documents", "col": 4}},
		{"id": "card5", "type": "card", "data": {"card_name": "eCourts & AI", "col": 4}},
	]

	links = [
		# ── Matters ──
		{"label": "Matters", "type": "Card Break", "hidden": 0, "onboard": 0, "link_count": 0, "link_type": "DocType"},
		{"label": "Legal Matter", "type": "Link", "link_to": "Legal Matter", "link_type": "DocType", "onboard": 1, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Hearing", "type": "Link", "link_to": "Hearing", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Chamber Application", "type": "Link", "link_to": "Chamber Application", "link_type": "DocType", "onboard": 1, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Timeline Entry", "type": "Link", "link_to": "Timeline Entry", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Matter Timeline (Page)", "type": "Link", "link_to": "matter-timeline", "link_type": "Page", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		# ── Masters ──
		{"label": "Masters", "type": "Card Break", "hidden": 0, "onboard": 0, "link_count": 0, "link_type": "DocType"},
		{"label": "Legal Vertical", "type": "Link", "link_to": "Legal Vertical", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Matter Type", "type": "Link", "link_to": "Matter Type", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Legal Party", "type": "Link", "link_to": "Legal Party", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Court", "type": "Link", "link_to": "Court", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Clause Library", "type": "Link", "link_to": "Clause Library", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		# ── Intake & Forms ──
		{"label": "Intake & Forms", "type": "Card Break", "hidden": 0, "onboard": 0, "link_count": 0, "link_type": "DocType"},
		{"label": "Intake Form Template", "type": "Link", "link_to": "Intake Form Template", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Intake Submission", "type": "Link", "link_to": "Intake Submission", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Intake Form (Page)", "type": "Link", "link_to": "intake-form", "link_type": "Page", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		# ── Documents ──
		{"label": "Documents", "type": "Card Break", "hidden": 0, "onboard": 0, "link_count": 0, "link_type": "DocType"},
		{"label": "Document Template", "type": "Link", "link_to": "Document Template", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Generated Document", "type": "Link", "link_to": "Generated Document", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		# ── eCourts & AI ──
		{"label": "eCourts & AI", "type": "Card Break", "hidden": 0, "onboard": 0, "link_count": 0, "link_type": "DocType"},
		{"label": "eCourts Sync Log", "type": "Link", "link_to": "eCourts Sync Log", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Caveat", "type": "Link", "link_to": "Caveat", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Notice", "type": "Link", "link_to": "Notice", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Mediation Session", "type": "Link", "link_to": "Mediation Session", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Signature Request", "type": "Link", "link_to": "Signature Request", "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Deadline Tracker (Page)", "type": "Link", "link_to": "deadline-tracker", "link_type": "Page", "onboard": 0, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		{"label": "Chamber Dashboard (Page)", "type": "Link", "link_to": "chamber-dashboard", "link_type": "Page", "onboard": 1, "hidden": 0, "is_query_report": 0, "dependencies": ""},
		# ── Reports ──
		{"label": "Upcoming Hearings (Report)", "type": "Link", "link_to": "Upcoming Hearings", "link_type": "Report", "onboard": 0, "hidden": 0, "is_query_report": 1, "dependencies": ""},
		{"label": "Court Fees (Report)", "type": "Link", "link_to": "Court Fees", "link_type": "Report", "onboard": 0, "hidden": 0, "is_query_report": 1, "dependencies": ""},
		{"label": "Matter Status (Report)", "type": "Link", "link_to": "Matter Status", "link_type": "Report", "onboard": 0, "hidden": 0, "is_query_report": 1, "dependencies": ""},
		{"label": "Deadline Watch (Report)", "type": "Link", "link_to": "Deadline Watch", "link_type": "Report", "onboard": 0, "hidden": 0, "is_query_report": 1, "dependencies": ""},
		# ── Settings ──
		{"label": "Chamber Settings", "type": "Link", "link_to": "Chamber Settings", "link_type": "DocType", "onboard": 1, "hidden": 0, "is_query_report": 0, "dependencies": ""},
	]

	shortcuts = [
		{"label": "New Legal Matter", "link_to": "Legal Matter", "type": "DocType", "color": "Grey", "doc_view": "List"},
		{"label": "New Chamber Application", "link_to": "Chamber Application", "type": "DocType", "color": "Grey", "doc_view": "List"},
		{"label": "Chamber Settings", "link_to": "Chamber Settings", "type": "DocType", "color": "Grey", "doc_view": "List"},
	]

	doc = frappe.new_doc("Workspace")
	doc.title = "Chamber"
	doc.label = "Chamber"
	doc.name = "Chamber"
	doc.module = "chamber"
	doc.icon = "octicon-briefcase"
	doc.public = 1
	doc.is_hidden = 0
	doc.hide_custom = 0
	doc.category = "Modules"
	doc.for_user = ""
	doc.parent_page = ""
	doc.restrict_to_domain = ""
	doc.indicator_color = ""
	doc.sequence_id = 1
	doc.content = json.dumps(content_blocks)

	for link in links:
		doc.append("links", link)

	for shortcut in shortcuts:
		doc.append("shortcuts", shortcut)

	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()


def after_migrate():
	"""Ensure Chamber workspace exists after every migrate.

	Fixes the case where JSON sync silently skips workspace creation in
	Frappe v15 (frappe/frappe#40154). Safe to call repeatedly — skips
	if the workspace already exists.
	"""
	ensure_chamber_workspace()


def create_roles():
	"""Chamber roles created once; grant them in Desk > Role Profile."""
	for role in ("Chamber Manager", "Advocate", "Filing Clerk"):
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.desk_access = 1
			doc.save(ignore_permissions=True)


def create_role_profiles():
	"""Preconfigured Role Profiles so firms can assign a single profile per
	team member instead of juggling individual roles."""
	profiles = {
		"Chamber Manager": ["Chamber Manager", "Advocate", "Filing Clerk"],
		"Advocate": ["Advocate"],
		"Filing Clerk": ["Filing Clerk"],
	}
	for profile_name, roles in profiles.items():
		if frappe.db.exists("Role Profile", profile_name):
			continue
		doc = frappe.new_doc("Role Profile")
		doc.role_profile = profile_name
		for role in roles:
			doc.append("roles", {"role": role})
		try:
			doc.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Role Profile {profile_name} creation")


def seed_master_data():
	"""Seed the 7 legal verticals with milestone sequences and template lists."""
	from chamber.setup.seed import seed_verticals

	seed_verticals()


def setup_default_settings():
	settings = frappe.get_single("Chamber Settings")
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_permissions = True
	settings.ecourts_api_url = "https://services.ecourts.gov.in/ecourtindia_v6/api/casestatus_particularscnrp.php"
	settings.default_reminder_days = 3
	settings.ai_max_tokens = 2000
	settings.save(ignore_permissions=True)
