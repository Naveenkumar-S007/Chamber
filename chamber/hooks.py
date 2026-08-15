import frappe

from . import __version__ as app_version

app_name = "chamber"
app_title = "Chamber"
app_publisher = "Naveenkumar S"
app_description = "Chamber — Legal practice / chamber work management for Frappe v15 & ERPNext v15. Vertical-wise case intake, template-based document generation, litigation timelines, eCourts CNR sync and AI-assisted drafting."
app_email = "naveenkumar.s007@gmail.com"
app_license = "MIT"
app_version = app_version

# Apps that this app is dependent on.
# install_apps = ["erpnext"]

# Includes in <head>
# ------------------
# include js, css files in header of desk.html
app_include_js = [
	"/assets/chamber/js/intake_form_renderer.js",
	"/assets/chamber/js/timeline_view.js",
]
# app_include_css = ["/assets/chamber/css/chamber.css"]

# Include js, css files in header of web template
# web_include_js = ["/assets/chamber/js/chamber.js"]
# web_include_css = ["/assets/chamber/css/chamber.css"]

# Include js in page
# page_js = {"page" : "public/js/file.js"}

# Include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"Legal Matter": "public/js/legal_matter.js",
	"Chamber Application": "public/js/chamber_application.js",
	"Chamber Settings": "chamber_settings.js",
}
doctype_list_js = {
	"Legal Matter": "public/js/legal_matter_list.js",
}

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# Website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------
# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------
# add methods and filters to jinja environment
# jinja = {
# 	"methods": "chamber.utils.jinja_methods",
# 	"filters": "chamber.utils.jinja_filters"
# }

# Installation
# ------------
before_install = "chamber.setup.install.before_install"
after_install = "chamber.setup.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config
# notification_config = "chamber.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways
# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes
# override_doctype_class = {
# 	"Todo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
	"Legal Matter": {
		"on_update": "chamber.chamber.doctype.legal_matter.legal_matter.on_update",
		"validate": "chamber.chamber.doctype.legal_matter.legal_matter.validate",
	},
	"Intake Submission": {
		"validate": "chamber.chamber.doctype.intake_submission.intake_submission.validate",
	},
	"Generated Document": {
		"validate": "chamber.chamber.doctype.generated_document.generated_document.validate",
	},
	"Hearing": {
		"on_update": "chamber.chamber.doctype.hearing.hearing.on_update",
	},
	"Chamber Application": {
		"validate": "chamber.chamber.doctype.chamber_application.chamber_application.validate",
	},
}

# ERPNext coupling: keep Chamber data in step with ERPNext parties.
# The module guard keeps Chamber fully standalone when ERPNext is not installed.
try:
	_installed_apps = frappe.get_installed_apps()
except Exception:
	_installed_apps = []

if "erpnext" in _installed_apps:
	doc_events.update(
		{
			"Customer": {
				"after_insert": "chamber.chamber.doctype.legal_party.legal_party.on_erpnext_customer_after_insert",
			},
			"Contact": {
				"after_insert": "chamber.chamber.doctype.legal_party.legal_party.on_erpnext_contact_after_insert",
			},
		}
	)

# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"chamber.chamber.doctype.chamber_application.chamber_application.send_hearing_reminders",
		"chamber.chamber.doctype.caveat.caveat.expire_overdue_caveats",
	],
	"hourly": [
		"chamber.utils.ecourts_client.poll_auto_sync_matters",
		"chamber.utils.portal_client.poll_portal_matters",
	],
}

# Testing
# -------
# before_tests = "chamber.install.before_tests"

# Overriding Methods
# ------------------------------
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "chamber.event.get_events"
# }
# override_doctype_class = {
# 	"Customer": "chamber.custom.customer.CustomCustomer"
# }

# Linked Documents
# ----------------
# Link Documents that are shown as cards in the document view
doc_links = {
	"Legal Matter": [
		{
			"fieldname": "legal_matter",
			"label": "Hearings",
		},
		{
			"fieldname": "legal_matter",
			"label": "Timeline Entries",
		},
		{
			"fieldname": "legal_matter",
			"label": "Generated Documents",
		},
		{
			"fieldname": "matter",
			"label": "Chamber Applications",
		},
		{
			"fieldname": "legal_matter",
			"label": "Intake Submissions",
		},
		{
			"fieldname": "legal_matter",
			"label": "Notices",
		},
		{
			"fieldname": "legal_matter",
			"label": "Mediation Sessions",
		},
		{
			"fieldname": "legal_matter",
			"label": "Signature Requests",
		},
	],
	"Chamber Application": [
		{
			"fieldname": "chamber_application",
			"label": "Hearing Log",
		},
	],
}

# Custom app fixtures (records installed with the app)
fixtures = []

# Notification triggers (web / email)
# notification_config = "chamber.notifications.get_notification_config"

# Roles created on install (kept in sync with Role doctype fixture)
# created via after_install -> chamber.setup.install.create_roles

# Website
# -------
# website_context = {
# 	"favicon": "theme.assets/images/favicon.ico"
# }

# Cloud
# -----
# Whitelisted calls that can be made from the client
# whitelisted_calls = []

# Build application js & css files
# ---------------------------------
# build_js = ["public/js/intake_form_renderer.js", "public/js/timeline_view.js"]

# Requirements
# ------------
# List all requirements that this app needs
# requirements = []

# Translation
# -----------
# disable_website_translations = False
