"""Sample / demo data for the Chamber app.

Loads a realistic legal practice dataset (courts, parties, matters across all
7 verticals, hearings, chamber applications, caveat, intake submissions and a
generated document) so the app can be demonstrated end-to-end.

Usage:
  bench --site <site> execute chamber.setup.demo.run
  (or in developer mode: Chamber > demo API)

The loader is idempotent — it never overwrites existing records.
"""
import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, today


def run():
	if not demo_allowed():
		frappe.throw(
			_("Demo data can only be loaded in developer mode or with the site config flag 'chamber_demo': 1")
		)
	seed_demo()
	frappe.db.commit()
	return {"status": "Demo data loaded"}


def demo_allowed():
	return frappe.conf.get("developer_mode") or frappe.conf.get("chamber_demo")


def _get(doctype, name):
	return frappe.db.get_value(doctype, name, "name")


def _ensure(doctype, name, values):
	if name and _get(doctype, name):
		return name
	doc = frappe.new_doc(doctype)
	doc.update(values)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_unique(doctype, filters, values):
	"""Idempotent create for transactional records (no stable name)."""
	existing = frappe.db.get_all(doctype, filters=filters, limit=1, pluck="name")
	if existing:
		return existing[0]
	doc = frappe.new_doc(doctype)
	doc.update(values)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


def seed_demo():
	courts()
	parties()
	matters()


def courts():
	rows = [
		("City Civil Court, Bengaluru", "District Court", "Karnataka", "Bengaluru", "Court No. 14"),
		("Sessions Court, Bengaluru", "District Court", "Karnataka", "Bengaluru", "Court No. 3"),
		("Magistrate Court, Bengaluru", "Magistrate Court", "Karnataka", "Bengaluru", "Court No. 7"),
		("Family Court, Bengaluru", "Family Court", "Karnataka", "Bengaluru", "Court No. 2"),
		("MACT Tribunal, Bengaluru", "MACT Tribunal", "Karnataka", "Bengaluru", "Tribunal 1"),
		("High Court of Karnataka", "High Court", "Karnataka", "Bengaluru", "Court Hall 11"),
	]
	for name, tier, state, jurisdiction, bench_no in rows:
		_ensure(
			"Court",
			name,
			{"court_name": name, "court_tier": tier, "state": state, "jurisdiction": jurisdiction, "bench_number": bench_no, "ecourts_enabled": 1},
		)


def parties():
	_ensure(
		"Legal Party",
		"Bizaxl Technologies Pvt. Ltd.",
		{
			"party_name": "Bizaxl Technologies Pvt. Ltd.",
			"party_type": "Company",
			"role": "Client",
			"is_client": 1,
			"contact_number": "+91 98450 12345",
			"email": "legal@bizaxl.in",
			"address": "No. 21, Koramangala, Bengaluru, Karnataka",
		},
	)
	_ensure(
		"Legal Party",
		"Rajesh Kumar",
		{
			"party_name": "Rajesh Kumar",
			"party_type": "Individual",
			"role": "Client",
			"is_client": 1,
			"contact_number": "+91 98860 54321",
			"email": "rajesh.kumar@example.com",
			"address": "Indiranagar, Bengaluru",
		},
	)
	_ensure(
		"Legal Party",
		"Meena Sharma",
		{
			"party_name": "Meena Sharma",
			"party_type": "Individual",
			"role": "Client",
			"is_client": 1,
			"contact_number": "+91 90080 00001",
			"email": "meena.sharma@example.com",
			"address": "Whitefield, Bengaluru",
		},
	)
	_ensure(
		"Legal Party",
		"Acme Traders",
		{
			"party_name": "Acme Traders",
			"party_type": "Company",
			"role": "Counterparty",
			"contact_number": "+91 99000 11111",
		},
	)
	_ensure(
		"Legal Party",
		"State of Karnataka",
		{"party_name": "State of Karnataka", "party_type": "Government", "role": "Other"},
	)


def matters():
	# 1. Criminal
	criminal = _ensure_unique(
		"Legal Matter",
		{"matter_title": "State vs Rajesh Kumar — Cheating (Sec. 420 IPC)"},
		{
			"matter_title": "State vs Rajesh Kumar — Cheating (Sec. 420 IPC)",
			"vertical": "Criminal Defense",
			"matter_type": "Criminal Defense-Regular Offence",
			"status": "Active",
			"case_category": "Criminal",
			"client": "Rajesh Kumar",
			"court": "Sessions Court, Bengaluru",
			"court_bench": "Court No. 3",
			"case_number": "S.C. 45/2026",
			"cnr_number": "KA01-000045-2026",
			"fir_number": "0123/2026",
			"police_station": "Indiranagar Police Station",
			"fir_date": add_days(today(), -120),
			"sections_charged": "420, 468 IPC",
			"bail_status": "Granted",
			"custody_status": "On Bail",
			"investigating_officer": "Insp. Suresh N.",
			"ecourts_auto_sync": 0,
		},
	)
	if criminal:
		_ensure_unique("Hearing", {"legal_matter": criminal, "hearing_date": add_days(today(), 12)}, {"legal_matter": criminal, "hearing_date": add_days(today(), 12), "purpose": "Evidence stage", "source": "eCourts", "judge": "Hon'ble Justice A. Sharma"})

	# 2. Cheque bounce (statutory window live)
	cheque = _ensure_unique(
		"Legal Matter",
		{"matter_title": "Sec. 138 Complaint — Bizaxl vs Acme Traders"},
		{
			"matter_title": "Sec. 138 Complaint — Bizaxl vs Acme Traders",
			"vertical": "Cheque Bounce / NI Act 138",
			"matter_type": "Cheque Bounce / NI Act 138-Standard 138 Complaint",
			"status": "Active",
			"case_category": "Criminal",
			"client": "Bizaxl Technologies Pvt. Ltd.",
			"court": "Magistrate Court, Bengaluru",
			"case_number": "C.C. 88/2026",
			"claim_amount": 750000,
			"statutory_deadline_date": add_days(today(), 9),
			"statutory_deadline_note": "Sec. 138 complaint window (15 days from notice)",
			"ecourts_auto_sync": 1,
		},
	)
	if cheque:
		intake_responses(cheque, "Cheque Bounce Intake", {
			"cheque_number": "004567",
			"cheque_date": add_days(today(), -60),
			"cheque_amount": "750000",
			"drawee_bank": "HDFC Bank, MG Road",
			"dishonour_reason": "Insufficient Funds",
			"dishonour_date": add_days(today(), -50),
			"demand_notice_date": add_days(today(), -24),
		})
		_ensure_unique("Hearing", {"legal_matter": cheque, "hearing_date": add_days(today(), 6)}, {"legal_matter": cheque, "hearing_date": add_days(today(), 6), "purpose": "Summons", "source": "eCourts"})

	# 3. Civil recovery
	civil = _ensure_unique(
		"Legal Matter",
		{"matter_title": "Recovery Suit — Bizaxl vs Acme Traders (Rs. 5,00,000)"},
		{
			"matter_title": "Recovery Suit — Bizaxl vs Acme Traders (Rs. 5,00,000)",
			"vertical": "Civil Litigation",
			"matter_type": "Civil Litigation-Recovery Suit",
			"status": "Active",
			"case_category": "Civil",
			"client": "Bizaxl Technologies Pvt. Ltd.",
			"court": "City Civil Court, Bengaluru",
			"case_number": "O.S. 120/2026",
			"cnr_number": "KA01-000120-2026",
			"claim_amount": 500000,
			"suit_valuation": 500000,
			"cause_of_action_date": add_days(today(), -700),
			"limitation_years": 3,
			"opposing_counsel": "Adv. Vikram Rao",
			"ecourts_auto_sync": 0,
		},
	)
	if civil:
		_ensure_unique("Hearing", {"legal_matter": civil, "hearing_date": add_days(today(), 18)}, {"legal_matter": civil, "hearing_date": add_days(today(), 18), "purpose": "Written statement", "source": "eCourts"})

	# 4. Family — mutual consent with cooling-off
	family = _ensure_unique(
		"Legal Matter",
		{"matter_title": "Divorce by Mutual Consent — Meena Sharma"},
		{
			"matter_title": "Divorce by Mutual Consent — Meena Sharma",
			"vertical": "Family Law",
			"matter_type": "Family Law-Divorce (Mutual Consent)",
			"status": "Active",
			"case_category": "Family",
			"client": "Meena Sharma",
			"court": "Family Court, Bengaluru",
			"case_number": "M.C. 33/2026",
			"filing_date": add_days(today(), -30),
			"opposing_counsel": "Adv. Priya Menon",
			"ecourts_auto_sync": 0,
		},
	)
	if family:
		intake_responses(family, "Family Law Intake", {
			"marriage_date": add_days(today(), -2000),
			"place_of_marriage": "Bengaluru",
			"personal_law": "Hindu Marriage Act",
			"first_motion_date": add_days(today(), -30),
			"mediation_status": "Concluded",
		})
		_ensure_unique("Mediation Session", {"legal_matter": family, "session_date": add_days(today(), -20)}, {"legal_matter": family, "session_date": add_days(today(), -20), "purpose": "Settlement discussion", "status": "Concluded", "outcome": "Terms agreed; memorandum of settlement prepared."})

	# 5. Property — partition with document track + caveat
	property_m = _ensure_unique(
		"Legal Matter",
		{"matter_title": "Partition Suit — Family Land, Survey 45/2"},
		{
			"matter_title": "Partition Suit — Family Land, Survey 45/2",
			"vertical": "Property / Real Estate Disputes",
			"matter_type": "Property / Real Estate Disputes-Partition",
			"status": "Active",
			"case_category": "Civil",
			"client": "Rajesh Kumar",
			"court": "City Civil Court, Bengaluru",
			"case_number": "O.S. 77/2026",
			"cause_of_action_date": add_days(today(), -100),
			"limitation_years": 12,
			"ecourts_auto_sync": 0,
		},
	)
	if property_m:
		matter = frappe.get_doc("Legal Matter", property_m)
		matter.append("document_collection", {"document_name": "Sale Deed", "category": "Sale Deed", "status": "Collected", "received_date": add_days(today(), -10)})
		matter.append("document_collection", {"document_name": "Encumbrance Certificate", "category": "Encumbrance Certificate", "status": "Requested", "requested_date": add_days(today(), -5)})
		matter.append("document_collection", {"document_name": "RTC / Khata", "category": "RTC / Khata", "status": "Not Started"})
		matter.flags.ignore_permissions = True
		matter.save(ignore_permissions=True)
		caveat = _ensure_unique(
			"Caveat",
			{"caveat_number": "CAV-2026-0001"},
			{
				"caveat_number": "CAV-2026-0001",
				"legal_matter": property_m,
				"client": "Rajesh Kumar",
				"court": "City Civil Court, Bengaluru",
				"filed_date": add_days(today(), -20),
			},
		)
		_ensure_unique("Chamber Application", {"application_title": "Application for Discovery of Documents"}, {
			"application_title": "Application for Discovery of Documents",
			"matter": property_m,
			"client": "Rajesh Kumar",
			"application_type": "Discovery",
			"governing_legal_provision": "Order XI, CPC",
			"court": "City Civil Court, Bengaluru",
			"current_status": "Listed",
			"assigned_advocate": frappe.session.user if frappe.session.user != "Guest" else None,
			"next_hearing_date": add_days(today(), 8),
			"court_fees": 500,
			"fee_receipt_reference": "RCPT-2026-0456",
		})

	# 6. Corporate
	corp = _ensure_unique(
		"Legal Matter",
		{"matter_title": "NDA — Bizaxl with potential partner"},
		{
			"matter_title": "NDA — Bizaxl with potential partner",
			"vertical": "Corporate / Commercial",
			"matter_type": "Corporate / Commercial-Contract Drafting",
			"status": "Active",
			"case_category": "Commercial",
			"client": "Bizaxl Technologies Pvt. Ltd.",
			"opposing_counsel": "Adv. Priya Menon",
			"ecourts_auto_sync": 0,
		},
	)
	if corp:
		intake_responses(corp, "Corporate / Commercial Intake", {
			"entity_name": "Bizaxl Technologies Pvt. Ltd.",
			"entity_type": "Pvt Ltd",
			"contract_value": "1500000",
			"governing_law": "India",
			"jurisdiction": "Bengaluru",
		})
	# chamber application on the criminal matter (bail-related chamber work)
	if criminal:
		_ensure_unique("Chamber Application", {"application_title": "Application for Bail Records"}, {
			"application_title": "Application for Bail Records",
			"matter": criminal,
			"client": "Rajesh Kumar",
			"application_type": "Bail",
			"court": "Sessions Court, Bengaluru",
			"current_status": "Heard",
			"order_summary": "Bail granted on conditions.",
		})

	# 7. IP with renewal
	ip = _ensure_unique(
		"Legal Matter",
		{"matter_title": "Trademark — BIZAXL (Class 9)"},
		{
			"matter_title": "Trademark — BIZAXL (Class 9)",
			"vertical": "IP Law",
			"matter_type": "IP Law-Trademark",
			"status": "Active",
			"case_category": "IP",
			"client": "Bizaxl Technologies Pvt. Ltd.",
			"portal": "IP India",
			"ecourts_auto_sync": 0,
		},
	)
	if ip:
		intake_responses(ip, "IP Law Intake", {
			"ip_type": "Trademark",
			"application_number": "5123456",
			"filing_date": add_days(today(), -300),
			"renewal_due_date": add_days(today(), 45),
			"tm_class": "9",
		})

	# a generated document for the 138 matter (rendered from the seeded template)
	template = frappe.db.get_value("Document Template", {"template_name": "Section 138 Legal Demand Notice"}, "name")
	if template and cheque:
		_ensure_unique(
			"Generated Document",
			{"legal_matter": cheque, "document_template": template},
			{
				"legal_matter": cheque,
				"document_template": template,
				"title": "Section 138 Legal Demand Notice — Bizaxl vs Acme Traders",
				"status": "Ready for Review",
				"requires_lawyer_review": 0,
				"content": "LEGAL DEMAND NOTICE UNDER SECTION 138 NI ACT — (demo record; render from the matter to regenerate content)",
			},
		)


def intake_responses(legal_matter, template_name, values):
	template = frappe.db.get_value("Intake Form Template", {"template_name": template_name}, "name")
	if not template or frappe.db.exists(
		"Intake Submission", {"legal_matter": legal_matter, "intake_form_template": template}
	):
		return
	doc = frappe.new_doc("Intake Submission")
	doc.update(
		{
			"legal_matter": legal_matter,
			"intake_form_template": template,
			"vertical": frappe.db.get_value("Legal Matter", legal_matter, "vertical"),
			"submission_date": getdate(),
			"status": "Submitted",
		}
	)
	for key, value in values.items():
		doc.append("responses", {"fieldname": key, "label": key.replace("_", " ").title(), "value": value})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
