import frappe
from frappe import _


@frappe.whitelist()
def load():
	"""Load sample/demo data. Guarded — only in developer mode or with the
	site config flag chamber_demo: 1 (see chamber.setup.demo.demo_allowed)."""
	from chamber.setup.demo import demo_allowed, run

	if not demo_allowed():
		frappe.throw(
			_("Demo data requires developer mode or site config 'chamber_demo': 1")
		)
	return run()
