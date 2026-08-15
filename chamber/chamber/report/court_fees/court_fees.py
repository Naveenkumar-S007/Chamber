import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": _("Application"), "fieldname": "name", "fieldtype": "Link", "options": "Chamber Application", "width": 180},
		{"label": _("Application Title"), "fieldname": "application_title", "fieldtype": "Data", "width": 220},
		{"label": _("Matter"), "fieldname": "matter", "fieldtype": "Link", "options": "Legal Matter", "width": 160},
		{"label": _("Court"), "fieldname": "court", "fieldtype": "Link", "options": "Court", "width": 160},
		{"label": _("Court Fees Paid (INR)"), "fieldname": "court_fees", "fieldtype": "Currency", "width": 150},
		{"label": _("Receipt Reference"), "fieldname": "fee_receipt_reference", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "current_status", "fieldtype": "Data", "width": 110},
		{"label": _("Filing Date"), "fieldname": "filing_date", "fieldtype": "Date", "width": 110},
	]

	conditions = ["ca.docstatus < 2"]
	params = {}
	if filters.get("from_date"):
		conditions.append("ca.filing_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("ca.filing_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("matter"):
		conditions.append("ca.matter = %(matter)s")
		params["matter"] = filters["matter"]
	if filters.get("status"):
		conditions.append("ca.current_status = %(status)s")
		params["status"] = filters["status"]

	rows = frappe.db.sql(
		f"""
		select
			ca.name, ca.application_title, ca.matter, ca.court,
			ca.court_fees, ca.fee_receipt_reference, ca.current_status, ca.filing_date
		from `tabChamber Application` ca
		where {" and ".join(conditions)}
		order by ca.filing_date desc, ca.name
		""",
		params,
		as_dict=1,
	)
	message = _("Court fees paid across chamber applications.")
	return columns, rows, message
