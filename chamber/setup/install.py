import frappe
from frappe import _


def before_install():
	pass


def after_install():
	create_roles()
	create_role_profiles()
	seed_master_data()
	setup_default_settings()


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
