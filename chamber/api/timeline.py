import frappe
from frappe import _
from frappe.utils import getdate

from chamber.utils import timeline_engine


@frappe.whitelist()
def get(legal_matter):
	"""Full timeline payload: events + milestone sequence + deadline bands."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	return {
		"matter": matter.name,
		"matter_title": matter.matter_title,
		"vertical": matter.vertical,
		"matter_type": matter.matter_type,
		"milestones": timeline_engine.get_milestone_sequence(legal_matter),
		"events": timeline_engine.get_events(legal_matter),
		"deadline_bands": timeline_engine.get_deadline_bands(legal_matter),
	}


@frappe.whitelist()
def add_entry(legal_matter, entry_date, event_type, title, description=None, milestone=None, source="Manual"):
	doc = frappe.new_doc("Timeline Entry")
	doc.update(
		{
			"legal_matter": legal_matter,
			"entry_date": getdate(entry_date),
			"event_type": event_type,
			"title": title,
			"description": description,
			"milestone": milestone,
			"source": source,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}
