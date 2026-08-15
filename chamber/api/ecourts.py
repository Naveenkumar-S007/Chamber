import frappe
from frappe import _

from chamber.utils import ecourts_client


@frappe.whitelist()
def sync(legal_matter):
	"""Manually trigger an eCourts sync for a matter."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	result = ecourts_client.sync_matter(legal_matter)
	return result


@frappe.whitelist()
def check_coverage(legal_matter):
	"""State-coverage transparency: is this matter's court tier covered by live sync?"""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	coverage = {"live": False, "reason": ""}
	if matter.court:
		court = frappe.get_doc("Court", matter.court)
		if court.ecourts_enabled:
			coverage["live"] = True
		else:
			coverage["reason"] = _(
				"Court {0} is flagged as manual-entry fallback (digitization coverage varies by state/tier)."
			).format(court.court_name)
	elif not matter.cnr_number:
		coverage["reason"] = _("Matter has no CNR number — manual entry only.")
	else:
		coverage["reason"] = _("No court linked — assume manual entry fallback.")
	return coverage
