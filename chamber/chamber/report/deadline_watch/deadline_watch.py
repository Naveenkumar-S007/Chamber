import frappe
from frappe import _

from chamber.api.deadlines import get_upcoming


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": _("Countdown"), "fieldname": "days_left", "fieldtype": "Int", "width": 90},
		{"label": _("Deadline"), "fieldname": "label", "fieldtype": "Data", "width": 220},
		{"label": _("Type"), "fieldname": "deadline_type", "fieldtype": "Data", "width": 100},
		{"label": _("Matter"), "fieldname": "matter", "fieldtype": "Link", "options": "Legal Matter", "width": 170},
		{"label": _("Matter Title"), "fieldname": "matter_title", "fieldtype": "Data", "width": 260},
		{"label": _("Vertical"), "fieldname": "vertical", "fieldtype": "Data", "width": 140},
		{"label": _("Due Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("CNR"), "fieldname": "cnr_number", "fieldtype": "Data", "width": 150},
	]

	result = get_upcoming(
		vertical=filters.get("vertical") or None,
		horizon_days=filters.get("horizon_days") or 90,
		deadline_type=filters.get("deadline_type") or None,
	)
	data = [
		{
			"days_left": d["days_left"],
			"label": d["label"],
			"deadline_type": d["deadline_type"],
			"matter": d["matter"],
			"matter_title": d["matter_title"],
			"vertical": d["vertical"],
			"date": d["date"],
			"cnr_number": d["cnr_number"],
		}
		for d in result["deadlines"]
	]
	return columns, data
