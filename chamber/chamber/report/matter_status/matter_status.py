import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": _("Vertical"), "fieldname": "vertical", "fieldtype": "Link", "options": "Legal Vertical", "width": 200},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
		{"label": _("Matter Count"), "fieldname": "count", "fieldtype": "Int", "width": 110},
		{"label": _("Total Claim (INR)"), "fieldname": "total_claim", "fieldtype": "Currency", "width": 150},
		{"label": _("With CNR"), "fieldname": "with_cnr", "fieldtype": "Int", "width": 100},
	]

	vertical_filter = ""
	params = []
	if filters.get("vertical"):
		vertical_filter = "where m.vertical = %s"
		params.append(filters["vertical"])

	rows = frappe.db.sql(
		f"""
		select
			m.vertical,
			coalesce(v.vertical_name, m.vertical) as vertical_name,
			m.status,
			count(*) as `count`,
			sum(coalesce(m.claim_amount, 0)) as total_claim,
			sum(case when m.cnr_number is not null and m.cnr_number != '' then 1 else 0 end) as with_cnr
		from `tabLegal Matter` m
		left join `tabLegal Vertical` v on v.name = m.vertical
		{vertical_filter}
		group by m.vertical, v.vertical_name, m.status
		order by `count` desc
		""",
		params,
		as_dict=1,
	)

	data = [
		{
			"vertical": r["vertical"],
			"status": r["status"],
			"count": r["count"],
			"total_claim": r["total_claim"],
			"with_cnr": r["with_cnr"],
		}
		for r in rows
	]
	message = _("Case load grouped by legal vertical and matter status.")
	return columns, data, message
