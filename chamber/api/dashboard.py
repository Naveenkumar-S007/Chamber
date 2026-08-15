import frappe
from frappe import _


@frappe.whitelist()
def get_stats():
	"""Aggregate stats for the Chamber Dashboard page.

	Returns chart-ready series plus headline numbers. Respects the
	matter-level permission opt-in when enabled.
	"""
	from chamber.chamber.doctype.legal_matter.legal_matter import _visible_matters

	conditions = ""
	params = []
	names = _visible_matters(frappe.session.user)
	if names is not None:
		if not names:
			return empty_stats()
		escaped = ", ".join(f"'{frappe.db.escape(n)}'" for n in names)
		conditions = f"where name in ({escaped})"

	# matters by vertical
	by_vertical = frappe.db.sql(
		f"""select coalesce(v.vertical_name, m.vertical) as label, count(*) as value
		from `tabLegal Matter` m
		left join `tabLegal Vertical` v on v.name = m.vertical
		{conditions}
		group by label order by value desc limit 10""",
		params,
		as_dict=1,
	)
	# matters by status
	by_status = frappe.db.sql(
		f"""select coalesce(nullif(m.status, ''), 'Unassigned') as label, count(*) as value
		from `tabLegal Matter` m
		{conditions}
		group by label order by value desc limit 12""",
		params,
		as_dict=1,
	)
	# upcoming hearings (next 30 days) — count per date
	hearings = frappe.db.sql(
		f"""select hearing_date as label, count(*) as value
		from `tabHearing`
		where hearing_date between %s and %s
		group by hearing_date order by hearing_date asc limit 30""",
		(frappe.utils.today(), frappe.utils.add_days(frappe.utils.today(), 30)),
		as_dict=1,
	)
	# headline numbers
	headline = {}
	headline["active_matters"] = frappe.db.count(
		"Legal Matter", {"status": "Active"}
	)
	headline["total_matters"] = frappe.db.count("Legal Matter")
	headline["upcoming_hearings"] = sum(h["value"] for h in hearings)
	headline["court_fees_paid"] = frappe.db.sql(
		"""select coalesce(sum(court_fees), 0) from `tabChamber Application` where docstatus < 2"""
	)[0][0]
	headline["pending_signatures"] = frappe.db.count("Signature Request", {"status": ["in", ["Sent", "Viewed"]]})
	headline["caveats_active"] = frappe.db.count("Caveat", {"status": "Active"})
	headline["overdue_deadlines"] = frappe.db.count(
		"Legal Matter", {"limitation_flagged": 1}
	)

	return {
		"by_vertical": by_vertical,
		"by_status": by_status,
		"hearings": hearings,
		"headline": headline,
	}


def empty_stats():
	return {
		"by_vertical": [],
		"by_status": [],
		"hearings": [],
		"headline": {
			"active_matters": 0,
			"total_matters": 0,
			"upcoming_hearings": 0,
			"court_fees_paid": 0,
			"pending_signatures": 0,
			"caveats_active": 0,
			"overdue_deadlines": 0,
		},
	}
