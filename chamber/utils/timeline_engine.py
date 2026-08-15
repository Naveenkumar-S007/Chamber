import json

import frappe
from frappe.utils import add_days, date_diff, getdate, today


def get_milestone_sequence(legal_matter):
	"""Vertical or matter-type milestone sequence (JSON config), parsed safely."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	raw = None
	if matter.matter_type:
		raw = frappe.db.get_value("Matter Type", matter.matter_type, "milestone_sequence")
	if not raw and matter.vertical:
		raw = frappe.db.get_value("Legal Vertical", matter.vertical, "milestone_sequence")
	if not raw:
		return []
	try:
		seq = json.loads(raw)
		return seq if isinstance(seq, list) else []
	except (ValueError, TypeError):
		return []


def get_events(legal_matter):
	"""Chronological events for the matter, pulled from Timeline Entry records
	(which in turn capture hearings, documents and chamber applications)."""
	rows = frappe.db.get_all(
		"Timeline Entry",
		filters={"legal_matter": legal_matter},
		fields=[
			"name",
			"entry_date",
			"event_type",
			"milestone",
			"title",
			"description",
			"source",
			"reference_doctype",
			"reference_name",
		],
		order_by="entry_date asc, creation asc",
	)
	return [
		{
			"name": r.name,
			"date": r.entry_date,
			"event_type": r.event_type,
			"milestone": r.milestone,
			"title": r.title,
			"description": r.description,
			"source": r.source,
			"reference_doctype": r.reference_doctype,
			"reference_name": r.reference_name,
		}
		for r in rows
	]


def get_deadline_bands(legal_matter):
	"""Statutory / limitation countdown bands rendered on the timeline.

	Bands are computed from matter fields + vertical-specific rules, all on a
	reusable 'deadline countdown band' component (spec §4.2).
	"""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	bands = []
	now = getdate()

	# 1. Statutory deadline (appeal filing deadline, 138 complaint deadline, etc.)
	if matter.statutory_deadline_date:
		bands.append(
			{
				"key": "statutory_deadline",
				"label": matter.statutory_deadline_note or "Statutory Deadline",
				"start_date": today(),
				"end_date": str(matter.statutory_deadline_date),
				"days_left": date_diff(matter.statutory_deadline_date, now),
				"status": band_status(date_diff(matter.statutory_deadline_date, now)),
				"note": matter.statutory_deadline_note or "File before the statutory window closes.",
			}
		)

	# 2. Limitation period (cause of action -> expiry)
	if matter.cause_of_action_date and matter.limitation_years:
		from frappe.utils import add_years

		expiry = add_years(getdate(matter.cause_of_action_date), int(matter.limitation_years))
		bands.append(
			{
				"key": "limitation",
				"label": "Limitation Period",
				"start_date": str(matter.cause_of_action_date),
				"end_date": str(expiry),
				"days_left": date_diff(expiry, now),
				"status": band_status(date_diff(expiry, now)),
				"note": f"Suit must be filed within {matter.limitation_years} year(s) of the cause of action (Limitation Act, 1963).",
			}
		)

	# 3. Cheque bounce statutory window (15 days from demand notice) — vertical-specific
	if matter.vertical and frappe.db.get_value("Legal Vertical", matter.vertical, "vertical_name") == "Cheque Bounce / NI Act 138":
		notice_date = matter.get("demand_notice_date") or get_intake_value(matter.name, "demand_notice_date")
		if notice_date:
			window_end = add_days(getdate(notice_date), 15)
			bands.append(
				{
					"key": "ni138_window",
					"label": "Sec. 138 — 15-day statutory window",
					"start_date": str(notice_date),
					"end_date": str(window_end),
					"days_left": date_diff(window_end, now),
					"status": band_status(date_diff(window_end, now)),
					"note": "Complaint must be filed within 15 days of notice expiry (30 days where notice period extended).",
				}
			)

	return bands


def get_intake_value(legal_matter, fieldname):
	"""Look up a field value from the latest intake responses for a matter."""
	submissions = frappe.db.get_all(
		"Intake Submission",
		filters={"legal_matter": legal_matter, "status": "Submitted"},
		fields=["name"],
		order_by="modified desc",
	)
	if not submissions:
		return None
	return frappe.db.get_value(
		"Intake Response",
		{"parenttype": "Intake Submission", "parent": submissions[0].name, "fieldname": fieldname},
		"value",
	)


def band_status(days_left):
	if days_left < 0:
		return "expired"
	if days_left <= 15:
		return "critical"
	if days_left <= 60:
		return "warning"
	return "ok"
