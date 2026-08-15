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
def sync_extended(legal_matter):
	"""Sync the extended eCourts bundle explicitly: order sheets, cause list
	and digitized judgment copies (each is a best-effort configurable hook).

	Runs the extended fetchers even when the core CNR status call is skipped,
	so firms with the extra endpoints configured can pull everything in one go.
	"""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	tried = []
	results = {}
	if not matter.cnr_number:
		frappe.throw(_("Matter has no CNR number."))

	if frappe.db.get_single_value("Chamber Settings", "ecourts_ordersheet_url"):
		tried.append("order-sheets")
		ecourts_client.fetch_ordersheet_entries(matter)
		results["order_sheets"] = "fetched"
	else:
		results["order_sheets"] = "not configured"

	if frappe.db.get_single_value("Chamber Settings", "ecourts_causelist_url"):
		tried.append("cause-list")
		ecourts_client.fetch_causelist_entries(matter)
		results["cause_list"] = "fetched"
	else:
		results["cause_list"] = "not configured"

	if frappe.db.get_single_value("Chamber Settings", "ecourts_judgments_url"):
		tried.append("judgments")
		ecourts_client.fetch_judgment_copies(matter)
		results["judgments"] = "fetched"
	else:
		results["judgments"] = "not configured"

	frappe.db.commit()
	message = _("Extended sync ran. {0}").format(
		"; ".join(f"{k}: {v}" for k, v in results.items())
	)
	if not tried:
		message = _("No extended endpoints configured. Set Order Sheet / Cause List / Judgments URLs in Chamber Settings, then run again.")
	return {"tried": tried, "results": results, "message": message}


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
