"""Sample data for the Chamber workspace.

Creates realistic legal-practice records so the workspace is populated.
Run with:  bench --site <site> execute chamber.setup.sample_data.create_sample_data

Idempotent -- skips records that already exist.
"""
from datetime import date, timedelta
import frappe


def create_sample_data():
    _create_courts()
    _create_parties()
    _create_document_templates()
    _create_matters()
    _create_hearings()
    _create_applications()
    _create_timeline_entries()
    _create_notices()
    _create_caveats()
    _create_mediation_sessions()
    _create_intake_templates()
    frappe.db.commit()
    print("Sample data creation complete.")


def _v(name):
    return frappe.db.get_value("Legal Vertical", {"vertical_name": name}, "name")


def _mt(name, vertical):
    if not vertical:
        return None
    return frappe.db.get_value("Matter Type", {"matter_type": name, "vertical": vertical}, "name")


def _court(name):
    return frappe.db.get_value("Court", {"court_name": name}, "name")


def _party(name):
    return frappe.db.get_value("Legal Party", {"party_name": name}, "name")


def _matter(title):
    return frappe.db.get_value("Legal Matter", {"matter_title": title}, "name")


def _safe_save(doc, label):
    """Save doc with error handling. Returns True on success."""
    try:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  OK: {label}")
        return True
    except Exception as e:
        frappe.db.rollback()
        print(f"  SKIP: {label} -- {e}")
        return False


def _create_courts():
    courts = [
        {"court_name": "Delhi High Court", "court_tier": "High Court",
         "state": "Delhi", "jurisdiction": "Original Side", "ecourts_enabled": 1},
        {"court_name": "Sessions Court, Tis Hazari", "court_tier": "District Court",
         "state": "Delhi", "jurisdiction": "Criminal"},
        {"court_name": "Supreme Court of India", "court_tier": "Supreme Court",
         "state": "Delhi", "jurisdiction": "Constitutional"},
        {"court_name": "Consumer Disputes Commission, Saket",
         "court_tier": "Consumer Forum", "state": "Delhi", "ecourts_enabled": 1},
        {"court_name": "NCLT, New Delhi Bench", "court_tier": "NCLT",
         "state": "Delhi", "jurisdiction": "Corporate Insolvency"},
    ]
    for c in courts:
        if not frappe.db.exists("Court", {"court_name": c["court_name"]}):
            doc = frappe.new_doc("Court")
            doc.update(c)
            _safe_save(doc, f"Court: {c['court_name']}")


def _create_parties():
    parties = [
        {"party_name": "Rajesh Kumar Singh", "party_type": "Individual",
         "role": "Client", "is_client": 1, "contact_number": "+91-9876543210",
         "email": "rajesh.singh@email.com"},
        {"party_name": "Priya Sharma", "party_type": "Individual",
         "role": "Client", "is_client": 1, "contact_number": "+91-9988776655",
         "email": "priya.sharma@email.com"},
        {"party_name": "Metro Builders Pvt Ltd", "party_type": "Company",
         "role": "Client", "is_client": 1, "contact_number": "+91-11-26789012",
         "email": "legal@metrobuilders.in"},
        {"party_name": "Amit Verma", "party_type": "Individual",
         "role": "Accused", "contact_number": "+91-9812345678",
         "email": "amit.verma@email.com"},
        {"party_name": "State of NCT of Delhi", "party_type": "Government",
         "role": "Complainant"},
        {"party_name": "Bharat Finance Ltd", "party_type": "Company",
         "role": "Counterparty", "contact_number": "+91-11-45678901",
         "email": "compliance@bharatfin.in"},
        {"party_name": "Sunita Devi", "party_type": "Individual",
         "role": "Client", "is_client": 1, "contact_number": "+91-9811122233",
         "email": "sunita.devi@email.com"},
    ]
    for p in parties:
        if not frappe.db.exists("Legal Party", {"party_name": p["party_name"]}):
            doc = frappe.new_doc("Legal Party")
            doc.update(p)
            _safe_save(doc, f"Party: {p['party_name']}")


def _create_document_templates():
    v = _v("Criminal Defense")
    templates = []
    if v:
        templates += [
            {"template_name": "Bail Application (Regular)", "vertical": v,
             "status": "Published", "version": 1,
             "description": "Standard bail application",
             "template_body": "<h2>Bail Application</h2><p>Case: {{case_number}}</p><p>Applicant: {{client_name}}</p>"},
            {"template_name": "Vakalatnama (Criminal)", "vertical": v,
             "status": "Published", "version": 1,
             "description": "Standard vakalatnama",
             "template_body": "<h2>Vakalatnama</h2><p>Client: {{client_name}}</p>"},
            {"template_name": "Anticipatory Bail Application", "vertical": v,
             "status": "Draft", "version": 1,
             "description": "Section 438 CrPC application",
             "template_body": "<h2>Anticipatory Bail</h2><p>Applicant: {{client_name}}</p>"},
        ]
    v2 = _v("Cheque Bounce / NI Act 138")
    if v2:
        templates.append(
            {"template_name": "Legal Demand Notice (Sec. 138)", "vertical": v2,
             "status": "Published", "version": 1,
             "description": "Section 138 demand notice",
             "template_body": "<h2>Demand Notice</h2><p>Amount: {{claim_amount}}</p>"})
    for t in templates:
        if not frappe.db.exists("Document Template", {"template_name": t["template_name"]}):
            doc = frappe.new_doc("Document Template")
            doc.update(t)
            _safe_save(doc, f"Template: {t['template_name']}")


def _create_matters():
    v_crim = _v("Criminal Defense")
    v_ni = _v("Cheque Bounce / NI Act 138")
    v_civil = _v("Civil Litigation")
    v_family = _v("Family Law")
    c_tis = _court("Sessions Court, Tis Hazari")
    c_dhc = _court("Delhi High Court")
    c_cons = _court("Consumer Disputes Commission, Saket")
    p_rajesh = _party("Rajesh Kumar Singh")
    p_priya = _party("Priya Sharma")
    p_bharat = _party("Bharat Finance Ltd")
    p_amit = _party("Amit Verma")

    matters = [
        {"matter_title": "State vs Rajesh Kumar Singh - Theft FIR",
         "vertical": v_crim, "matter_type": _mt("Regular Offence", v_crim),
         "status": "Active", "priority": "High", "case_category": "Criminal",
         "court": c_tis, "judge_name": "Sh. Rakesh Kumar",
         "filing_date": date(2026, 3, 15), "client": p_rajesh,
         "opposing_counsel": "Adv. Vikram Mehta",
         "fir_number": "FIR 142/2026", "police_station": "PS Hauz Khas",
         "fir_date": date(2026, 2, 28),
         "sections_charged": "Section 379/34 IPC",
         "bail_status": "Granted", "custody_status": "On Bail",
         "ecourts_auto_sync": 1,
         "description": "Theft at commercial complex. Bail granted."},
        {"matter_title": "Priya Sharma vs Metro Builders - Deficiency",
         "vertical": v_civil, "matter_type": _mt("Money Suit", v_civil),
         "status": "Active", "priority": "Medium", "case_category": "Consumer",
         "court": c_cons, "judge_name": "Smt. Geeta Rani",
         "filing_date": date(2026, 1, 20), "client": p_priya,
         "opposing_counsel": "Adv. Sanjay Gupta", "claim_amount": 1500000,
         "description": "Flat not delivered. Builder delayed 3 years."},
        {"matter_title": "Bharat Finance vs Sunita Devi - Cheque Bounce",
         "vertical": v_ni, "matter_type": _mt("Cheque Bounce (Sec 138)", v_ni),
         "status": "Active", "priority": "Medium", "case_category": "Commercial",
         "court": c_tis, "filing_date": date(2026, 4, 10),
         "client": p_bharat,
         "opposing_counsel": "Adv. Pooja Nair", "claim_amount": 350000,
         "sections_charged": "Section 138 NI Act",
         "description": "Cheque of Rs. 3,50,000 dishonoured."},
        {"matter_title": "State vs Amit Verma - Cyber Crime",
         "vertical": v_crim, "matter_type": _mt("Cyber Crime", v_crim),
         "status": "Intake Pending", "priority": "Urgent",
         "case_category": "Criminal", "court": c_tis,
         "client": p_amit, "opposing_counsel": "Public Prosecutor",
         "fir_number": "FIR 289/2026", "police_station": "PS Cyber Cell",
         "fir_date": date(2026, 7, 5),
         "sections_charged": "Section 66C/66D IT Act",
         "bail_status": "Not Applied", "custody_status": "Not Arrested",
         "ecourts_auto_sync": 1,
         "description": "Phishing attacks on banking customers."},
        {"matter_title": "Priya Sharma - Divorce Petition",
         "vertical": v_family, "matter_type": _mt("Divorce", v_family),
         "status": "Active", "priority": "Medium", "case_category": "Family",
         "court": c_dhc, "judge_name": "Smt. Meera Kapoor",
         "filing_date": date(2026, 2, 5), "client": p_priya,
         "opposing_counsel": "Adv. Rahul Deshpande",
         "description": "Divorce by mutual consent. Counseling in progress."},
        {"matter_title": "Rajesh Singh - Appeal against Conviction",
         "vertical": v_crim, "matter_type": _mt("Appeal", v_crim),
         "status": "Active", "priority": "High", "case_category": "Criminal",
         "court": c_dhc, "judge_name": "Hon'ble Mr. Justice Anil Bhat",
         "filing_date": date(2026, 6, 1), "client": p_rajesh,
         "opposing_counsel": "Learned APP",
         "description": "Appeal against conviction in Sessions Court."},
    ]

    for m in matters:
        title = m["matter_title"]
        if frappe.db.exists("Legal Matter", {"matter_title": title}):
            continue
        # Skip if required dependencies are missing
        if not m.get("vertical"):
            print(f"  SKIP: Matter '{title[:40]}' -- vertical not found")
            continue
        if not m.get("matter_type"):
            print(f"  SKIP: Matter '{title[:40]}' -- matter_type not found")
            continue
        doc = frappe.new_doc("Legal Matter")
        doc.update(m)
        if m.get("client"):
            doc.append("parties", {"party": m["client"]})
        _safe_save(doc, f"Matter: {title[:50]}")


def _create_hearings():
    today = date.today()
    m1 = _matter("State vs Rajesh Kumar Singh - Theft FIR")
    m2 = _matter("Priya Sharma vs Metro Builders - Deficiency")
    m3 = _matter("Bharat Finance vs Sunita Devi - Cheque Bounce")
    m4 = _matter("State vs Amit Verma - Cyber Crime")
    m5 = _matter("Priya Sharma - Divorce Petition")
    hearings = [
        {"legal_matter": m1, "hearing_date": today + timedelta(days=14),
         "purpose": "Cross-examination", "judge": "Sh. Rakesh Kumar",
         "next_hearing_date": today + timedelta(days=30), "source": "eCourts"},
        {"legal_matter": m1, "hearing_date": today - timedelta(days=21),
         "purpose": "Bail review", "judge": "Sh. Rakesh Kumar",
         "outcome": "Bail confirmed.", "source": "eCourts"},
        {"legal_matter": m2, "hearing_date": today + timedelta(days=21),
         "purpose": "Written arguments", "judge": "Smt. Geeta Rani",
         "next_hearing_date": today + timedelta(days=45), "source": "Manual"},
        {"legal_matter": m3, "hearing_date": today + timedelta(days=7),
         "purpose": "First appearance", "source": "Cause List",
         "next_hearing_date": today + timedelta(days=60)},
        {"legal_matter": m4, "hearing_date": today + timedelta(days=10),
         "purpose": "Charge framing", "next_hearing_date": today + timedelta(days=25),
         "source": "eCourts"},
        {"legal_matter": m5, "hearing_date": today + timedelta(days=35),
         "purpose": "Counseling 3rd session", "next_hearing_date": today + timedelta(days=65),
         "source": "Manual"},
    ]
    for h in hearings:
        if not h["legal_matter"]:
            continue
        if frappe.db.exists("Hearing",
                {"legal_matter": h["legal_matter"], "hearing_date": h["hearing_date"]}):
            continue
        doc = frappe.new_doc("Hearing")
        doc.update(h)
        _safe_save(doc, f"Hearing: {h['purpose'][:40]}")


def _create_applications():
    today = date.today()
    m1 = _matter("State vs Rajesh Kumar Singh - Theft FIR")
    m2 = _matter("Priya Sharma vs Metro Builders - Deficiency")
    m4 = _matter("State vs Amit Verma - Cyber Crime")
    c_tis = _court("Sessions Court, Tis Hazari")
    apps = [
        {"application_title": "Bail Application for Rajesh Singh",
         "matter": m1, "application_type": "Bail",
         "current_status": "Order Passed", "filing_date": date(2026, 3, 20),
         "order_date": date(2026, 3, 25),
         "court": c_tis, "judge_name": "Sh. Rakesh Kumar",
         "urgency_level": "Urgent",
         "order_summary": "Bail granted on surety of Rs. 25,000."},
        {"application_title": "Interim Injunction vs Metro Builders",
         "matter": m2, "application_type": "Interim Injunction / Stay",
         "current_status": "Listed", "filing_date": today - timedelta(days=10),
         "next_hearing_date": today + timedelta(days=15),
         "urgency_level": "Normal",
         "remarks": "Seeking stay on sale of remaining flats."},
        {"application_title": "Anticipatory Bail for Amit Verma",
         "matter": m4, "application_type": "Bail",
         "current_status": "Draft", "urgency_level": "Ex-parte",
         "remarks": "Preparing 438 CrPC application."},
    ]
    for a in apps:
        if not a["matter"]:
            continue
        if frappe.db.exists("Chamber Application",
                {"application_title": a["application_title"]}):
            continue
        doc = frappe.new_doc("Chamber Application")
        doc.update(a)
        _safe_save(doc, f"Application: {a['application_title'][:40]}")


def _create_timeline_entries():
    today = date.today()
    m1 = _matter("State vs Rajesh Kumar Singh - Theft FIR")
    if not m1:
        return
    entries = [
        {"legal_matter": m1, "entry_date": date(2026, 2, 28),
         "event_type": "Milestone", "title": "FIR Registered",
         "description": "FIR 142/2026 registered at PS Hauz Khas.",
         "source": "Manual"},
        {"legal_matter": m1, "entry_date": date(2026, 3, 1),
         "event_type": "Filing", "title": "Client Consultation",
         "description": "Initial consultation. Retainer signed.",
         "source": "Manual"},
        {"legal_matter": m1, "entry_date": date(2026, 3, 15),
         "event_type": "Filing", "title": "Bail Application Filed",
         "description": "Bail application filed before Sessions Court.",
         "source": "Manual"},
        {"legal_matter": m1, "entry_date": date(2026, 3, 25),
         "event_type": "Order", "title": "Bail Granted",
         "description": "Bail granted on Rs. 25,000 surety.",
         "source": "eCourts"},
        {"legal_matter": m1, "entry_date": today - timedelta(days=7),
         "event_type": "Hearing", "title": "Cross-exam scheduled",
         "description": "Next hearing for cross-examination of PW1.",
         "source": "eCourts"},
        {"legal_matter": m1, "entry_date": today,
         "event_type": "Document", "title": "Charge sheet received",
         "description": "Complete charge sheet received.",
         "source": "Manual"},
    ]
    for e in entries:
        if frappe.db.exists("Timeline Entry",
                {"legal_matter": e["legal_matter"], "title": e["title"]}):
            continue
        doc = frappe.new_doc("Timeline Entry")
        doc.update(e)
        _safe_save(doc, f"Timeline: {e['title'][:40]}")


def _create_notices():
    m2 = _matter("Priya Sharma vs Metro Builders - Deficiency")
    m3 = _matter("Bharat Finance vs Sunita Devi - Cheque Bounce")
    today = date.today()
    notices = [
        {"legal_matter": m2, "notice_type": "Legal Notice",
         "title": "Legal Notice to Metro Builders",
         "issued_date": today - timedelta(days=60),
         "recipient": "Metro Builders Pvt Ltd",
         "served_date": today - timedelta(days=55),
         "status": "Served",
         "notes": "Notice sent via registered post."},
        {"legal_matter": m3, "notice_type": "Demand Notice",
         "title": "Statutory Demand Notice Sec 138",
         "issued_date": today - timedelta(days=45),
         "recipient": "Sunita Devi",
         "served_date": today - timedelta(days=40),
         "status": "Served",
         "notes": "Demand for Rs. 3,50,000."},
    ]
    for n in notices:
        if not n["legal_matter"]:
            continue
        if frappe.db.exists("Notice",
                {"legal_matter": n["legal_matter"], "title": n["title"]}):
            continue
        doc = frappe.new_doc("Notice")
        doc.update(n)
        _safe_save(doc, f"Notice: {n['title'][:40]}")


def _create_caveats():
    today = date.today()
    p_rajesh = _party("Rajesh Kumar Singh")
    c_dhc = _court("Delhi High Court")
    c_tis = _court("Sessions Court, Tis Hazari")
    m1 = _matter("State vs Rajesh Kumar Singh - Theft FIR")
    caveats = [
        {"caveat_number": "CAV/2026/DHC/00123", "legal_matter": m1,
         "client": p_rajesh, "court": c_dhc,
         "filed_date": today - timedelta(days=30),
         "valid_until": today + timedelta(days=180),
         "status": "Active",
         "remarks": "Prevent ex-parte proceedings in appeal."},
        {"caveat_number": "CAV/2026/SH/00456", "legal_matter": m1,
         "client": p_rajesh, "court": c_tis,
         "filed_date": today - timedelta(days=15),
         "valid_until": today + timedelta(days=90),
         "status": "Active",
         "remarks": "Prevent surprise bail cancellation."},
    ]
    for c in caveats:
        if frappe.db.exists("Caveat", {"caveat_number": c["caveat_number"]}):
            continue
        doc = frappe.new_doc("Caveat")
        doc.update(c)
        _safe_save(doc, f"Caveat: {c['caveat_number']}")


def _create_mediation_sessions():
    today = date.today()
    m5 = _matter("Priya Sharma - Divorce Petition")
    if not m5:
        return
    sessions = [
        {"legal_matter": m5,
         "session_date": today - timedelta(days=45),
         "purpose": "First mediation - mutual consent divorce",
         "status": "Held",
         "outcome": "Partial agreement on maintenance.",
         "next_session_date": today - timedelta(days=15)},
        {"legal_matter": m5,
         "session_date": today - timedelta(days=15),
         "purpose": "Second mediation - property division",
         "status": "Held",
         "outcome": "Agreed on 60-40 split.",
         "next_session_date": today + timedelta(days=30)},
    ]
    for s in sessions:
        if frappe.db.exists("Mediation Session",
                {"legal_matter": s["legal_matter"],
                 "session_date": s["session_date"]}):
            continue
        doc = frappe.new_doc("Mediation Session")
        doc.update(s)
        _safe_save(doc, "Mediation session")


def _create_intake_templates():
    v_crim = _v("Criminal Defense")
    v_ni = _v("Cheque Bounce / NI Act 138")
    templates = []
    if v_crim:
        templates.append(
            {"template_name": "Criminal Case Intake",
             "vertical": v_crim, "status": "Published", "version": 1,
             "active": 1, "description": "Intake form for criminal matters",
             "fields": [
                 {"fieldname": "client_name", "label": "Client Name",
                  "fieldtype": "Data", "reqd": 1},
                 {"fieldname": "contact_number", "label": "Contact Number",
                  "fieldtype": "Data", "reqd": 1},
                 {"fieldname": "fir_number", "label": "FIR Number",
                  "fieldtype": "Data", "reqd": 1},
                 {"fieldname": "sections_charged", "label": "Sections Charged",
                  "fieldtype": "Small Text", "reqd": 1},
                 {"fieldname": "description", "label": "Description",
                  "fieldtype": "Text", "reqd": 1},
             ]})
    if v_ni:
        templates.append(
            {"template_name": "Cheque Bounce Intake",
             "vertical": v_ni, "status": "Published", "version": 1,
             "active": 1, "description": "Intake form for NI Act 138",
             "fields": [
                 {"fieldname": "client_name", "label": "Client Name",
                  "fieldtype": "Data", "reqd": 1},
                 {"fieldname": "cheque_number", "label": "Cheque Number",
                  "fieldtype": "Data", "reqd": 1},
                 {"fieldname": "cheque_amount", "label": "Amount",
                  "fieldtype": "Currency", "reqd": 1},
                 {"fieldname": "description", "label": "Details",
                  "fieldtype": "Text"},
             ]})
    for t in templates:
        if frappe.db.exists("Intake Form Template",
                {"template_name": t["template_name"]}):
            continue
        doc = frappe.new_doc("Intake Form Template")
        doc.update(t)
        _safe_save(doc, f"Intake: {t['template_name']}")
