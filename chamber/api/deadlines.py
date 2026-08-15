import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today

from chamber.utils import timeline_engine


@frappe.whitelist()
def get_upcoming(vertical=None, horizon_days=90, deadline_type=None):
	"""All upcoming deadlines across matters — the deadline tracker view.

	Collects statutory deadlines, limitation expiry, IP renewals and caveat
	expiry into one filterable feed (spec §4.3 — a deadline tracker, not an
	extension of the hearing timeline).
	"""
	horizon = int(horizon_days or 90)
	filters = {}
	if vertical:
		filters["vertical"] = vertical
	matters = frappe.db.get_all(
		"Legal Matter",
		filters=filters,
		fields=[
			"name",
			"matter_title",
			"vertical",
			"matter_type",
			"status",
			"statutory_deadline_date",
			"statutory_deadline_note",
			"cause_of_action_date",
			"limitation_years",
			"limitation_expiry_date",
			"cnr_number",
			"court",
		],
		order_by="modified desc",
	)

	deadlines = []
	for m in matters:
		# Statutory deadline (138 complaint, appeal filing, etc.)
		if m.statutory_deadline_date:
			push_deadline(
				deadlines,
				m,
				deadline_type="Statutory",
				label=m.statutory_deadline_note or "Statutory Deadline",
				date=m.statutory_deadline_date,
				horizon=horizon,
			)
		# Limitation expiry
		if m.limitation_expiry_date:
			push_deadline(
				deadlines,
				m,
				deadline_type="Limitation",
				label="Limitation Expiry",
				date=m.limitation_expiry_date,
				horizon=horizon,
			)
		# IP renewals (deadline-driven verticals)
		if m.vertical and frappe.db.get_value("Legal Vertical", m.vertical, "vertical_name") == "IP Law":
			renewal = timeline_engine.get_intake_value(m.name, "renewal_due_date")
			if renewal:
				push_deadline(
					deadlines,
					m,
					deadline_type="IP Renewal",
					label="IP Renewal Due",
					date=renewal,
					horizon=horizon,
				)
		# Caveat expiry for this matter
		for caveat in timeline_engine.get_caveats(m.name):
			if caveat["valid_until"]:
				push_deadline(
					deadlines,
					m,
					deadline_type="Caveat",
					label=f"Caveat {caveat['caveat_number']} Expiry",
					date=caveat["valid_until"],
					horizon=horizon,
				)

	if deadline_type:
		deadlines = [d for d in deadlines if d["deadline_type"] == deadline_type]

	deadlines.sort(key=lambda d: d["date"])
	return {
		"deadlines": deadlines,
		"counts": {
			t: len([d for d in deadlines if d["deadline_type"] == t])
			for t in ("Statutory", "Limitation", "IP Renewal", "Caveat")
		},
	}


def push_deadline(deadlines, matter, deadline_type, label, date, horizon):
	days_left = date_diff(getdate(date), getdate())
	if days_left > horizon:
		return
	deadlines.append(
		{
			"matter": matter.name,
			"matter_title": matter.matter_title,
			"vertical": matter.vertical,
			"matter_type": matter.matter_type,
			"status": matter.status,
			"cnr_number": matter.cnr_number,
			"court": matter.court,
			"deadline_type": deadline_type,
			"label": label,
			"date": str(date),
			"days_left": days_left,
			"band_status": timeline_engine.band_status(days_left),
		}
	)
