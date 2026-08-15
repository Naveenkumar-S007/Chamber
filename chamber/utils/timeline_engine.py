import json

import frappe
from frappe.utils import add_days, add_months, date_diff, getdate, today


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
	(which in turn capture hearings, documents, chamber applications, caveats)."""
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


def get_document_track(legal_matter):
	"""Parallel document-collection track (property matters are document-blocked)."""
	rows = frappe.db.get_all(
		"Document Collection",
		filters={"parenttype": "Legal Matter", "parent": legal_matter},
		fields=["document_name", "category", "status", "requested_date", "received_date", "remarks"],
		order_by="idx",
	)
	return [
		{
			"document": r.document_name,
			"category": r.category,
			"status": r.status,
			"requested_date": r.requested_date,
			"received_date": r.received_date,
			"remarks": r.remarks,
		}
		for r in rows
	]


def get_caveats(legal_matter):
	"""Caveats linked to this matter (or its client/court where relevant)."""
	filters = {"status": "Active"}
	matter = frappe.get_doc("Legal Matter", legal_matter)
	if matter.client:
		filters["client"] = matter.client
	rows = frappe.db.get_all(
		"Caveat",
		filters=filters,
		fields=["name", "caveat_number", "legal_matter", "court", "filed_date", "valid_until", "status"],
		order_by="valid_until asc",
	)
	return [
		{
			"name": r.name,
			"caveat_number": r.caveat_number,
			"legal_matter": r.legal_matter,
			"court": r.court,
			"filed_date": r.filed_date,
			"valid_until": r.valid_until,
			"status": r.status,
		}
		for r in rows
		if r.legal_matter == legal_matter
	]


def get_deadline_bands(legal_matter):
	"""Statutory / limitation / caveat / cooling-off countdown bands.

	All bands are computed on the reusable 'deadline countdown band'
	component (spec §4.2); vertical-specific rules are configuration.
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

	vertical_name = (
		frappe.db.get_value("Legal Vertical", matter.vertical, "vertical_name") if matter.vertical else ""
	)

	# 3. Cheque bounce statutory window (15 days from demand notice) — vertical-specific
	if vertical_name == "Cheque Bounce / NI Act 138":
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

	# 4. Family — statutory 6-month cooling-off between first and second motion
	if vertical_name == "Family Law" and matter.matter_type and "Mutual Consent" in matter.matter_type:
		first_motion = get_intake_value(matter.name, "first_motion_date") or matter.get("first_motion_date")
		if first_motion:
			second_motion = add_months(getdate(first_motion), 6)
			bands.append(
				{
					"key": "cooling_off",
					"label": "Statutory 6-month cooling-off period",
					"start_date": str(first_motion),
					"end_date": str(second_motion),
					"days_left": date_diff(second_motion, now),
					"status": band_status(date_diff(second_motion, now)),
					"note": "Second motion under Sec. 13B HMA cannot be moved before 6 months from the first motion.",
				}
			)

	# 5. Caveat validity (Section 148A CPC — 90 days)
	for caveat in get_caveats(matter.name):
		if caveat["valid_until"]:
			bands.append(
				{
					"key": "caveat_" + frappe.scrub(caveat["caveat_number"]),
					"label": f"Caveat {caveat['caveat_number']} validity",
					"start_date": str(caveat["filed_date"]),
					"end_date": str(caveat["valid_until"]),
					"days_left": date_diff(caveat["valid_until"], now),
					"status": band_status(date_diff(caveat["valid_until"], now)),
					"note": "Renew the caveat before it lapses to keep protection against ex-parte orders.",
				}
			)

	# 6. IP renewals (deadline-driven, from intake)
	if vertical_name == "IP Law":
		renewal = get_intake_value(matter.name, "renewal_due_date")
		if renewal:
			bands.append(
				{
					"key": "ip_renewal",
					"label": "IP Renewal Due",
					"start_date": today(),
					"end_date": str(renewal),
					"days_left": date_diff(renewal, now),
					"status": band_status(date_diff(renewal, now)),
					"note": "Renewal deadline — prosecute before expiry to avoid lapsed registration.",
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
