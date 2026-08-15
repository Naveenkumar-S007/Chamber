import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": _("Hearing Date"), "fieldname": "hearing_date", "fieldtype": "Date", "width": 110},
		{"label": _("Days Left"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
		{"label": _("Matter"), "fieldname": "matter", "fieldtype": "Link", "options": "Legal Matter", "width": 160},
		{"label": _("Matter Title"), "fieldname": "matter_title", "fieldtype": "Data", "width": 260},
		{"label": _("Purpose"), "fieldname": "purpose", "fieldtype": "Data", "width": 180},
		{"label": _("Court"), "fieldname": "court", "fieldtype": "Data", "width": 160},
		{"label": _("Source"), "fieldname": "source", "fieldtype": "Data", "width": 90},
		{"label": _("Matter Status"), "fieldname": "matter_status", "fieldtype": "Data", "width": 110},
	]

	query_filters = {"hearing_date": (">=", filters.get("from_date") or getdate())}
	if filters.get("vertical"):
		query_filters["legal_matter"] = ["in", get_matters_for_vertical(filters["vertical"])]
	if filters.get("source"):
		query_filters["source"] = filters["source"]

	hearings = frappe.db.get_all(
		"Hearing",
		filters=query_filters,
		fields=["name", "legal_matter", "hearing_date", "purpose", "court", "source"],
		order_by="hearing_date asc",
		limit=500,
	)
	matter_titles = {
		m.name: (m.matter_title, m.status)
		for m in frappe.db.get_all(
			"Legal Matter",
			filters={"name": ["in", [h.legal_matter for h in hearings]]},
			fields=["name", "matter_title", "status"],
		)
	}
	courts = {c.name: c.court_name for c in frappe.db.get_all("Court", fields=["name", "court_name"])}

	data = []
	for h in hearings:
		title, status = matter_titles.get(h.legal_matter, ("", ""))
		data.append(
			{
				"hearing_date": h.hearing_date,
				"days_left": date_diff(h.hearing_date, getdate()),
				"matter": h.legal_matter,
				"matter_title": title,
				"purpose": h.purpose,
				"court": courts.get(h.court) or h.court,
				"source": h.source,
				"matter_status": status,
			}
		)
	data.sort(key=lambda r: r["days_left"])
	return columns, data


def get_matters_for_vertical(vertical):
	return [m.name for m in frappe.db.get_all("Legal Matter", filters={"vertical": vertical}, fields=["name"])]
