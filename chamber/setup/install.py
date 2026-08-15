import frappe
from frappe import _


def before_install():
	pass


def after_install():
	create_roles()
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
