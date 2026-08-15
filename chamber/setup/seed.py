"""Vertical-wise seed configuration for Chamber.

Builds the 7 priority legal verticals with their matter types, milestone
sequences, conditional intake field sets and starter document templates —
all as data, so firms can extend or edit without an engineering release.
"""
import json

import frappe

# --------------------------------------------------------------------------- verticals
VERTICALS = [
	{
		"vertical_name": "Criminal Defense",
		"code": "CRIM",
		"priority": 1,
		"color": "Red",
		"description": "High case volume, heavy hearing-date dependency — plays directly to eCourts CNR sync strength.",
		"milestone_sequence": [
			"FIR Registered",
			"Bail Application Filed",
			"Bail Order",
			"Charge Framed",
			"Evidence Stage",
			"Arguments",
			"Judgment",
		],
		"template_documents": [
			"Bail Application (regular)",
			"Anticipatory Bail Application",
			"Quashing Petition (Sec. 482 CrPC / BNS)",
			"Vakalatnama (criminal)",
			"Application for Certified Copies",
			"Discharge Application",
			"Appeal Memorandum",
			"Revision Petition",
			"Cross-Examination Question Checklist",
		],
		"matter_types": [
			{"matter_type": "Regular Offence", "is_sub_type": 0, "code": "REG"},
			{"matter_type": "Anticipatory Bail (Pre-Arrest)", "is_sub_type": 1, "code": "ANT-BAIL",
				"milestone_sequence": ["Apprehension of Arrest", "Anticipatory Bail Filed", "Order (Granted/Rejected)"]},
			{"matter_type": "Quashing Petition", "is_sub_type": 1, "code": "QUASH",
				"milestone_sequence": ["Petition Filed", "Notice to State", "Hearing", "Order"]},
			{"matter_type": "Cyber Crime", "is_sub_type": 1, "code": "CYBER"},
			{"matter_type": "NDPS (Narcotics)", "is_sub_type": 1, "code": "NDPS"},
			{"matter_type": "POCSO", "is_sub_type": 1, "code": "POCSO"},
			{"matter_type": "Economic Offence", "is_sub_type": 1, "code": "ECO"},
			{"matter_type": "Appeal", "is_sub_type": 1, "code": "APPEAL",
				"milestone_sequence": ["Trial Court Judgment", "Appeal Filed", "Admission", "Final Hearing", "Appellate Judgment"]},
			{"matter_type": "Revision", "is_sub_type": 1, "code": "REV"},
		],
	},
	{
		"vertical_name": "Cheque Bounce / NI Act 138",
		"code": "NI138",
		"priority": 2,
		"color": "Orange",
		"description": "Extremely high volume in Indian courts, highly standardized process — best ROI for template automation.",
		"milestone_sequence": [
			"Cheque Dishonoured",
			"Demand Notice Sent",
			"15-Day Statutory Window",
			"Complaint Filed",
			"Summons",
			"Trial Stages",
			"Settlement / Compounding",
		],
		"template_documents": [
			"Legal Demand Notice (Sec. 138)",
			"Complaint under Sec. 138 / 200 CrPC",
			"Vakalatnama",
			"Settlement / Compounding Application",
		],
		"matter_types": [
			{"matter_type": "Standard 138 Complaint", "is_sub_type": 0, "code": "138"},
			{"matter_type": "Settlement / Compounding", "is_sub_type": 1, "code": "COMP"},
		],
	},
	{
		"vertical_name": "Civil Litigation",
		"code": "CIV",
		"priority": 3,
		"color": "Blue",
		"description": "Broad, litigation-heavy; benefits directly from caveat tracking and limitation-period automation.",
		"milestone_sequence": [
			"Cause of Action",
			"Legal Notice",
			"Suit Filed",
			"Written Statement",
			"Issues Framed",
			"Evidence",
			"Arguments",
			"Judgment",
		],
		"template_documents": [
			"Plaint (Recovery Suit)",
			"Legal Notice (pre-litigation)",
			"Written Statement",
			"Interim Application (Injunction / Stay)",
			"Eviction Notice / Eviction Petition",
			"Consumer Complaint (District/State/National)",
			"MACT Claim Petition",
			"Vakalatnama (civil)",
		],
		"matter_types": [
			{"matter_type": "Recovery Suit", "is_sub_type": 0, "code": "REC"},
			{"matter_type": "Injunction", "is_sub_type": 1, "code": "INJ"},
			{"matter_type": "Declaration", "is_sub_type": 1, "code": "DECL"},
			{"matter_type": "Specific Performance", "is_sub_type": 1, "code": "SP"},
			{"matter_type": "Eviction / Tenancy", "is_sub_type": 1, "code": "EVICT",
				"milestone_sequence": ["Notice to Vacate", "Statutory Notice Period", "Petition Filed", "Order"]},
			{"matter_type": "Arbitration Reference", "is_sub_type": 1, "code": "ARB"},
			{"matter_type": "Consumer Complaint", "is_sub_type": 1, "code": "CONSUMER"},
			{"matter_type": "Motor Accident Claim (MACT)", "is_sub_type": 1, "code": "MACT",
				"milestone_sequence": ["Accident Date", "Claim Filed", "Insurer Response", "Compensation Order"]},
			{"matter_type": "Torts / Damages", "is_sub_type": 1, "code": "TORT"},
		],
	},
	{
		"vertical_name": "Family Law",
		"code": "FAM",
		"priority": 4,
		"color": "Purple",
		"description": "High emotional/retention value, recurring hearing pattern (mediation, custody). Sensitive matters require mandatory lawyer review.",
		"milestone_sequence": [
			"Petition Filed",
			"Respondent's Reply",
			"Mediation",
			"Evidence",
			"Arguments",
			"Decree / Order",
		],
		"template_documents": [
			"Divorce Petition — Mutual Consent",
			"Divorce Petition — Contested",
			"Judicial Separation Petition",
			"Restitution of Conjugal Rights Petition",
			"Maintenance Application (Sec. 125 CrPC / HAMA)",
			"Custody Petition",
			"Guardianship Application",
			"Domestic Violence Complaint (PWDVA)",
			"Adoption Deed / Application",
			"Annulment Petition",
			"Section 498A Complaint Draft",
			"Affidavit of Assets and Liabilities",
			"Memorandum of Settlement",
		],
		"sensitive": 1,
		"matter_types": [
			{"matter_type": "Divorce (Mutual Consent)", "is_sub_type": 1, "code": "DMC",
				"milestone_sequence": ["Joint Petition Filed", "First Motion", "6-Month Cooling-Off", "Second Motion", "Decree"]},
			{"matter_type": "Divorce (Contested)", "is_sub_type": 1, "code": "DC",
				"milestone_sequence": ["Petition Filed", "Respondent's Reply", "Mediation", "Evidence", "Arguments", "Decree"]},
			{"matter_type": "Judicial Separation", "is_sub_type": 1, "code": "JS"},
			{"matter_type": "Restitution of Conjugal Rights", "is_sub_type": 1, "code": "RCR"},
			{"matter_type": "Maintenance", "is_sub_type": 1, "code": "MAINT",
				"milestone_sequence": ["Application Filed", "Interim Order", "Final Order"]},
			{"matter_type": "Custody / Guardianship", "is_sub_type": 1, "code": "CUST",
				"milestone_sequence": ["Petition Filed", "Mediation Sessions", "Interim Custody Order", "Final Order"]},
			{"matter_type": "Domestic Violence (PWDVA)", "is_sub_type": 1, "code": "DV",
				"milestone_sequence": ["Complaint Filed", "Protection Officer Report", "Interim Protection Order", "Final Order"]},
			{"matter_type": "Adoption", "is_sub_type": 1, "code": "ADOPT",
				"milestone_sequence": ["Application Filed", "Home Study / Verification", "Court Order", "Registration"]},
			{"matter_type": "Marriage Validity / Annulment", "is_sub_type": 1, "code": "ANNUL"},
			{"matter_type": "Dowry Harassment (498A)", "is_sub_type": 1, "code": "498A"},
			{"matter_type": "Succession / Inheritance", "is_sub_type": 1, "code": "SUCC"},
			{"matter_type": "Live-in / Paternity Disputes", "is_sub_type": 1, "code": "LIVEIN"},
		],
	},
	{
		"vertical_name": "Property / Real Estate Disputes",
		"code": "PROP",
		"priority": 5,
		"color": "Green",
		"description": "Long-duration matters, document-heavy — best fit for the template engine and document-status track.",
		"milestone_sequence": [
			"Notice Sent",
			"Suit Filed",
			"Site Inspection / Survey",
			"Evidence",
			"Judgment",
		],
		"template_documents": [
			"Legal Notice (Property Dispute)",
			"Partition Suit Draft",
			"Title Verification Report Template",
			"Sale Agreement Review Checklist",
			"RERA Complaint Draft",
			"Eviction Petition (Property)",
			"Land Acquisition Compensation Objection / Appeal",
		],
		"matter_types": [
			{"matter_type": "Title Dispute", "is_sub_type": 0, "code": "TITLE"},
			{"matter_type": "Partition", "is_sub_type": 1, "code": "PART"},
			{"matter_type": "Encroachment", "is_sub_type": 1, "code": "ENC"},
			{"matter_type": "Tenancy / Eviction", "is_sub_type": 1, "code": "TEN"},
			{"matter_type": "Sale Agreement Breach", "is_sub_type": 1, "code": "SALE"},
			{"matter_type": "RERA Complaint", "is_sub_type": 1, "code": "RERA",
				"milestone_sequence": ["Complaint Filed", "Builder Response", "Hearing", "Order"]},
			{"matter_type": "Land Acquisition", "is_sub_type": 1, "code": "LA"},
			{"matter_type": "Mortgage / Foreclosure", "is_sub_type": 1, "code": "MORT"},
			{"matter_type": "Easement Rights", "is_sub_type": 1, "code": "EASE"},
			{"matter_type": "Boundary Dispute", "is_sub_type": 1, "code": "BOUND"},
		],
	},
	{
		"vertical_name": "Corporate / Commercial",
		"code": "CORP",
		"priority": 6,
		"color": "Grey",
		"description": "Lower litigation intensity, more contract/compliance-driven — deadline/compliance tracking rather than hearing sync.",
		"milestone_sequence": [
			"Instruction / Engagement",
			"Draft Circulated",
			"Review / Comments",
			"Execution",
		],
		"template_documents": [
			"NDA",
			"Service Agreement",
			"Employment Agreement",
			"Termination Letter",
			"Compliance Checklist (by entity type)",
			"Board Resolution Templates",
			"Shareholders' Agreement",
			"Legal Notice (Commercial Dispute)",
			"IBC Application Draft",
		],
		"matter_types": [
			{"matter_type": "Contract Drafting", "is_sub_type": 0, "code": "CONTRACT"},
			{"matter_type": "Regulatory Compliance", "is_sub_type": 1, "code": "COMPLIANCE"},
			{"matter_type": "Commercial Dispute", "is_sub_type": 1, "code": "DISPUTE"},
			{"matter_type": "M&A", "is_sub_type": 1, "code": "MA"},
			{"matter_type": "Employment / Labour Dispute", "is_sub_type": 1, "code": "EMPLOY"},
			{"matter_type": "IPR Licensing", "is_sub_type": 1, "code": "IPR"},
			{"matter_type": "Insolvency (IBC)", "is_sub_type": 1, "code": "IBC"},
			{"matter_type": "Tax / GST Litigation", "is_sub_type": 1, "code": "TAX"},
			{"matter_type": "Shareholder / Director Dispute", "is_sub_type": 1, "code": "SHARE"},
			{"matter_type": "Regulatory Filing (ROC/SEBI/RBI)", "is_sub_type": 1, "code": "FILING"},
		],
	},
	{
		"vertical_name": "IP Law",
		"code": "IP",
		"priority": 7,
		"color": "Yellow",
		"description": "Deadline-driven but not litigation-driven — renewal/deadline tracking rather than hearing sync.",
		"milestone_sequence": [
			"Application Filed",
			"Objection Period",
			"Renewal Due Date",
			"Compliance Deadlines",
		],
		"template_documents": [
			"Trademark Objection Reply",
			"Renewal Reminder Letter",
			"Cease-and-Desist Notice",
			"Licensing Agreement",
			"Infringement Suit Draft",
		],
		"matter_types": [
			{"matter_type": "Trademark", "is_sub_type": 0, "code": "TM"},
			{"matter_type": "Patent", "is_sub_type": 1, "code": "PAT"},
			{"matter_type": "Copyright", "is_sub_type": 1, "code": "CR"},
			{"matter_type": "Design", "is_sub_type": 1, "code": "DSGN"},
			{"matter_type": "Geographical Indication", "is_sub_type": 1, "code": "GI"},
			{"matter_type": "Licensing", "is_sub_type": 1, "code": "LIC"},
			{"matter_type": "Infringement Litigation", "is_sub_type": 1, "code": "INFRINGE"},
		],
	},
]

# --------------------------------------------------------------------------- intake field sets
def _f(fieldname, label, fieldtype="Data", options="", reqd=0, depends_on="", section="", description=""):
	return {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
		"options": options,
		"reqd": reqd,
		"depends_on": depends_on,
		"section": section,
		"description": description,
	}


INTAKE_FORMS = [
	{
		"template_name": "Criminal Defense Intake",
		"vertical": "Criminal Defense",
		"description": "Conditional intake for criminal matters — branch fields appear based on case sub-type and role.",
		"fields": [
			_f("sub_type", "Case Sub-Type", "Select",
				"Regular Case\nAnticipatory Bail (Pre-Arrest)\nQuashing Petition\nCyber Crime\nNDPS\nPOCSO\nEconomic Offence\nAppeal\nRevision", 1, "", "Case Details"),
			_f("role", "Your Role", "Select",
				"Complainant\nAccused\nWitness\nAppellant\nRespondent", 1, "", "Case Details"),
			_f("fir_number", "FIR Number", "Data", "", 0, "", "Case Details"),
			_f("police_station", "Police Station", "Data", "", 0, "", "Case Details"),
			_f("fir_date", "Date of FIR", "Date", "", 0, "", "Case Details"),
			_f("sections_charged", "Sections / Offences Charged", "Small Text", "", 1, "", "Case Details",
				"IPC / BNS section lookup or free text"),
			_f("bail_status", "Bail Status", "Select",
				"Not Applied\nApplied\nGranted\nRejected\nAnticipatory Bail Filed\nAnticipatory Bail Granted\nAnticipatory Bail Rejected", 1, "", "Bail & Custody"),
			_f("bail_date", "Bail Order Date", "Date", "", 0, "bail_status=Granted", "Bail & Custody"),
			_f("custody_status", "Custody Status", "Select",
				"Not Arrested\nOn Bail\nJudicial Custody\nPolice Custody", 1, "", "Bail & Custody"),
			_f("investigating_officer", "Investigating Officer", "Data", "", 0, "", "Bail & Custody",
				"Name / contact for liaison tracking"),
			_f("prior_case_history", "Prior Case History", "Check", "", 0, "", "Case Details",
				"Repeat offender tracking"),
			_f("trial_judgment_date", "Trial Court Judgment Date", "Date", "", 0, "sub_type=Appeal", "Appeal Details"),
			_f("sentence_details", "Sentence Details", "Small Text", "", 0, "sub_type=Appeal", "Appeal Details"),
			_f("appeal_deadline", "Appeal Filing Deadline", "Date", "", 0, "sub_type=Appeal", "Appeal Details",
				"Auto-calculated from judgment date in most cases"),
		],
	},
	{
		"template_name": "Cheque Bounce / NI Act 138 Intake",
		"vertical": "Cheque Bounce / NI Act 138",
		"description": "Time-bound intake — the statutory 15/30-day demand-notice window is tracked automatically.",
		"fields": [
			_f("cheque_number", "Cheque Number", "Data", "", 1, "", "Cheque Details"),
			_f("cheque_date", "Cheque Date", "Date", "", 1, "", "Cheque Details"),
			_f("cheque_amount", "Cheque Amount", "Currency", "", 1, "", "Cheque Details"),
			_f("drawee_bank", "Drawee Bank", "Data", "", 1, "", "Cheque Details"),
			_f("dishonour_reason", "Reason for Dishonour", "Select",
				"Insufficient Funds\nSignature Mismatch\nAccount Closed\nPayment Stopped\nOther", 1, "", "Dishonour"),
			_f("dishonour_date", "Cheque Dishonour Date", "Date", "", 1, "", "Dishonour"),
			_f("demand_notice_date", "Demand Notice Sent Date", "Date", "", 1, "", "Statutory Window",
				"Critical time-bound field — complaint must follow within the statutory window"),
			_f("payment_status", "Payment / Settlement Status", "Select",
				"Unpaid\nPartially Paid\nPaid\nSettlement Offer Made\nCompounding Agreed", 0, "", "Settlement"),
			_f("compounding_offer", "Compounding / Settlement Offer", "Small Text", "", 0, "payment_status=Settlement Offer Made", "Settlement"),
		],
	},
	{
		"template_name": "Civil Litigation Intake",
		"vertical": "Civil Litigation",
		"description": "Limitation period is auto-flagged from the cause-of-action date + suit type.",
		"fields": [
			_f("nature_of_suit", "Nature of Suit", "Select",
				"Recovery\nInjunction\nDeclaration\nSpecific Performance\nEviction / Tenancy\nArbitration Reference\nConsumer Complaint\nMotor Accident Claim (MACT)\nTorts / Damages", 1, "", "Suit Details"),
			_f("claim_amount", "Claim Amount", "Currency", "", 0, "", "Suit Details"),
			_f("suit_valuation", "Suit Valuation", "Currency", "", 0, "", "Suit Details"),
			_f("cause_of_action_date", "Cause of Action Date", "Date", "", 1, "", "Suit Details",
				"Limitation period is computed from this date"),
			_f("opposing_party", "Opposing Party", "Data", "", 1, "", "Parties",
				"Multiple parties supported on the matter"),
			_f("tenancy_agreement_date", "Tenancy Agreement Date", "Date", "", 0, "nature_of_suit=Eviction / Tenancy", "Eviction"),
			_f("rent_default_period", "Rent Default Period", "Data", "", 0, "nature_of_suit=Eviction / Tenancy", "Eviction"),
			_f("notice_to_vacate_date", "Notice to Vacate Date", "Date", "", 0, "nature_of_suit=Eviction / Tenancy", "Eviction"),
			_f("accident_date", "Accident Date", "Date", "", 0, "nature_of_suit=Motor Accident Claim (MACT)", "MACT"),
			_f("insurance_company", "Insurance Company", "Data", "", 0, "nature_of_suit=Motor Accident Claim (MACT)", "MACT"),
			_f("product_service", "Product / Service", "Data", "", 0, "nature_of_suit=Consumer Complaint", "Consumer"),
			_f("deficiency_claimed", "Deficiency Claimed", "Small Text", "", 0, "nature_of_suit=Consumer Complaint", "Consumer"),
			_f("consumer_forum", "Forum", "Select",
				"District Commission\nState Commission\nNational Commission", 0, "nature_of_suit=Consumer Complaint", "Consumer"),
		],
	},
	{
		"template_name": "Family Law Intake",
		"vertical": "Family Law",
		"description": "Covers the full range of family matter types, not divorce alone. Sensitive sub-types are flagged for mandatory lawyer review.",
		"fields": [
			_f("matter_type", "Matter Type", "Select",
				"Divorce (Mutual Consent)\nDivorce (Contested)\nJudicial Separation\nRestitution of Conjugal Rights\nMaintenance\nCustody / Guardianship\nDomestic Violence (PWDVA)\nAdoption\nMarriage Validity / Annulment\nDowry Harassment (498A)\nSuccession / Inheritance\nLive-in / Paternity", 1, "", "Matter"),
			_f("marriage_date", "Date of Marriage", "Date", "", 0, "", "Marriage"),
			_f("place_of_marriage", "Place of Marriage", "Data", "", 0, "", "Marriage"),
			_f("marriage_registered", "Marriage Registered", "Check", "", 0, "", "Marriage"),
			_f("personal_law", "Personal Law Applicable", "Select",
				"Hindu Marriage Act\nMuslim Personal Law\nChristian (Divorce Act)\nSpecial Marriage Act\nParsi Law", 1, "", "Marriage",
				"Governs which grounds/procedure apply"),
			_f("children_involved", "Children Involved", "Check", "", 0, "", "Children"),
			_f("children_count", "Number of Children", "Int", "", 0, "children_involved=1", "Children"),
			_f("children_ages", "Children Ages", "Data", "", 0, "children_involved=1", "Children"),
			_f("current_custody", "Current Custody Arrangement", "Small Text", "", 0, "children_involved=1", "Children"),
			_f("mediation_status", "Mediation / Conciliation Status", "Select",
				"Not Started\nOngoing\nConcluded", 0, "", "Mediation"),
			_f("mediation_sessions", "Mediation Session Count", "Int", "", 0, "mediation_status=Ongoing", "Mediation"),
			_f("consent_matter", "Consent vs. Contested", "Select",
				"Consent\nContested", 0, "", "Mediation"),
			_f("relationship_to_respondent", "Relationship to Respondent", "Data", "", 0, "matter_type=Domestic Violence (PWDVA)", "Domestic Violence"),
			_f("incident_details", "Incident Details / Dates", "Small Text", "", 0, "matter_type=Domestic Violence (PWDVA)", "Domestic Violence"),
			_f("protection_order_sought", "Protection Order Sought", "Check", "", 0, "matter_type=Domestic Violence (PWDVA)", "Domestic Violence"),
			_f("residence_order_sought", "Residence Order Sought", "Check", "", 0, "matter_type=Domestic Violence (PWDVA)", "Domestic Violence"),
			_f("applicant_income", "Applicant Income", "Currency", "", 0, "matter_type=Maintenance", "Maintenance"),
			_f("respondent_income", "Respondent Income (if known)", "Currency", "", 0, "matter_type=Maintenance", "Maintenance"),
			_f("interim_maintenance_requested", "Interim Maintenance Requested", "Currency", "", 0, "matter_type=Maintenance", "Maintenance"),
			_f("adoption_type", "Adoption Type", "Select",
				"Hindu Adoption\nJJ Act (CARA)", 0, "matter_type=Adoption", "Adoption"),
			_f("first_motion_date", "First Motion Date", "Date", "", 0, "matter_type=Divorce (Mutual Consent)", "Cooling-Off",
				"Second motion becomes available 6 months after the first motion (Sec. 13B HMA)."),
			_f("second_motion_date", "Second Motion Date", "Date", "", 0, "matter_type=Divorce (Mutual Consent)", "Cooling-Off"),
			_f("deceased_date", "Deceased's Date of Death", "Date", "", 0, "matter_type=Succession / Inheritance", "Succession"),
			_f("will_exists", "Will Exists", "Check", "", 0, "matter_type=Succession / Inheritance", "Succession"),
			_f("assets_in_dispute", "Assets in Dispute", "Small Text", "", 0, "matter_type=Succession / Inheritance", "Succession"),
		],
	},
	{
		"template_name": "Property / Real Estate Intake",
		"vertical": "Property / Real Estate Disputes",
		"description": "Document-heavy vertical — expected document set pre-populates the document request list.",
		"fields": [
			_f("property_type", "Property Type", "Select",
				"Residential\nCommercial\nAgricultural\nLand", 1, "", "Property"),
			_f("dispute_type", "Dispute Type", "Select",
				"Title Dispute\nPartition\nEncroachment\nTenancy / Eviction\nSale Agreement Breach\nRERA Complaint\nLand Acquisition\nMortgage / Foreclosure\nEasement Rights\nBoundary Dispute", 1, "", "Dispute"),
			_f("survey_number", "Property Registration / Survey Number", "Data", "", 0, "", "Property"),
			_f("document_set", "Documents Expected", "Small Text", "", 0, "", "Documents",
				"Sale deed, encumbrance certificate, RTC/khata, mutation records…"),
			_f("rera_project_number", "RERA Project Registration Number", "Data", "", 0, "dispute_type=RERA Complaint", "RERA"),
			_f("builder_name", "Builder / Developer Name", "Data", "", 0, "dispute_type=RERA Complaint", "RERA"),
			_f("possession_delay", "Possession Delay Period", "Data", "", 0, "dispute_type=RERA Complaint", "RERA"),
			_f("co_owners", "Co-Owners", "Small Text", "", 0, "dispute_type=Partition", "Partition"),
			_f("share_claimed", "Share Proportions Claimed", "Data", "", 0, "dispute_type=Partition", "Partition"),
			_f("ancestral_property", "Ancestral vs. Self-Acquired", "Select",
				"Ancestral\nSelf-Acquired", 0, "dispute_type=Partition", "Partition"),
			_f("la_notification_date", "Acquisition Notification Date", "Date", "", 0, "dispute_type=Land Acquisition", "Land Acquisition"),
			_f("compensation_offered", "Compensation Offered", "Currency", "", 0, "dispute_type=Land Acquisition", "Land Acquisition"),
			_f("compensation_claimed", "Compensation Claimed", "Currency", "", 0, "dispute_type=Land Acquisition", "Land Acquisition"),
		],
	},
	{
		"template_name": "Corporate / Commercial Intake",
		"vertical": "Corporate / Commercial",
		"description": "Contract/compliance-driven — entity details, governing law and arbitration clause tracking.",
		"fields": [
			_f("matter_type", "Matter Type", "Select",
				"Contract Drafting\nRegulatory Compliance\nCommercial Dispute\nM&A\nEmployment / Labour Dispute\nIPR Licensing\nInsolvency (IBC)\nTax / GST Litigation\nShareholder / Director Dispute\nRegulatory Filing", 1, "", "Matter"),
			_f("entity_name", "Company / Entity Name", "Data", "", 1, "", "Entity"),
			_f("cin", "CIN / LLPIN", "Data", "", 0, "", "Entity"),
			_f("entity_type", "Entity Type", "Select",
				"Pvt Ltd\nLLP\nPartnership\nProprietorship\nPublic Ltd", 1, "", "Entity"),
			_f("contract_value", "Contract Value / Deal Size", "Currency", "", 0, "", "Deal"),
			_f("governing_law", "Governing Law", "Data", "", 0, "", "Deal"),
			_f("jurisdiction", "Jurisdiction", "Data", "", 0, "", "Deal"),
			_f("arbitration_clause", "Arbitration Clause", "Select",
				"None\nICC\nSIAC\nDomestic (Arbitration Act)", 0, "", "Deal"),
			_f("employee_designation", "Employee Designation", "Data", "", 0, "matter_type=Employment / Labour Dispute", "Employment"),
			_f("termination_date", "Termination / Dispute Date", "Date", "", 0, "matter_type=Employment / Labour Dispute", "Employment"),
			_f("nclt_status", "NCLT Filing Status", "Data", "", 0, "matter_type=Insolvency (IBC)", "Insolvency"),
			_f("resolution_professional", "Resolution Professional", "Data", "", 0, "matter_type=Insolvency (IBC)", "Insolvency"),
			_f("assessment_year", "Assessment Year", "Data", "", 0, "matter_type=Tax / GST Litigation", "Tax"),
			_f("demand_amount", "Demand Amount", "Currency", "", 0, "matter_type=Tax / GST Litigation", "Tax"),
			_f("appellate_level", "Appellate Authority Level", "Select",
				"CIT\nITAT\nHigh Court", 0, "matter_type=Tax / GST Litigation", "Tax"),
		],
	},
	{
		"template_name": "IP Law Intake",
		"vertical": "IP Law",
		"description": "Deadline-driven — renewal due dates feed the deadline tracker.",
		"fields": [
			_f("ip_type", "IP Type", "Select",
				"Trademark\nPatent\nCopyright\nDesign\nGeographical Indication", 1, "", "IP"),
			_f("application_number", "Application / Registration Number", "Data", "", 1, "", "IP"),
			_f("filing_date", "Filing Date", "Date", "", 1, "", "IP"),
			_f("renewal_due_date", "Renewal Due Date", "Date", "", 0, "", "Deadlines",
				"Feeds the deadline tracker (not hearing sync)"),
			_f("tm_class", "Class(es) Filed Under", "Data", "", 0, "ip_type=Trademark", "IP"),
			_f("infringing_party", "Infringing Party Details", "Data", "", 0, "matter_type=Infringement Litigation", "Infringement"),
			_f("cease_desist_sent", "Cease-and-Desist Sent", "Check", "", 0, "", "Infringement"),
			_f("cease_desist_date", "Cease-and-Desist Date", "Date", "", 0, "cease_desist_sent=1", "Infringement"),
			_f("licensee", "Licensee Details", "Data", "", 0, "ip_type=Licensing", "Licensing"),
			_f("royalty_terms", "Royalty Terms", "Small Text", "", 0, "ip_type=Licensing", "Licensing"),
			_f("licence_term", "Licence Term Dates", "Data", "", 0, "ip_type=Licensing", "Licensing"),
		],
	},
]

# --------------------------------------------------------------------------- starter document templates
DOC_TEMPLATES = [
	{
		"template_name": "Section 138 Legal Demand Notice",
		"vertical": "Cheque Bounce / NI Act 138",
		"drafting_type": "Litigation",
		"description": "Highest-priority, standardized template — statutory demand notice under Section 138, Negotiable Instruments Act, 1881.",
		"template_body": """LEGAL DEMAND NOTICE UNDER SECTION 138, NEGOTIABLE INSTRUMENTS ACT, 1881

TO,
{{ party_respondent or "The Drawer" }}
{{ client_address or "" }}

FROM,
{{ client_name or "The Payee" }}
{{ client_address or "" }}

DATED: {{ today }}

Subject: Demand notice for dishonour of cheque bearing No. {{ intake_cheque_number or "[cheque number]" }} dated {{ intake_cheque_date or "[cheque date]" }} for Rs. {{ intake_cheque_amount or "[amount]" }} drawn on {{ intake_drawee_bank or "[bank]" }}

Dear Sir/Madam,

1. The undersigned is the payee/holder in due course of the cheque described above, drawn by you in favour of the undersigned towards discharge of a legally enforceable debt/liability.

2. The said cheque, when presented for encashment, was returned dishonoured on {{ intake_dishonour_date or "[date]" }} with the remark "{{ intake_dishonour_reason or "[reason]" }}", as intimated by the drawee bank.

3. Consequently, a statutory demand notice was served upon you on {{ intake_demand_notice_date or "[notice date]" }} demanding payment of the said sum within 15 days of receipt of the notice.

4. Despite service of the said notice and expiry of the statutory period, you have failed and/or neglected to make payment of the amount due.

TAKE NOTICE that failure to pay the amount of Rs. {{ intake_cheque_amount or "[amount]" }} within the statutory period renders you liable for prosecution under Section 138 read with Section 142 of the Negotiable Instruments Act, 1881, and this office has instructions to file a complaint before the competent court.

Yours faithfully,
{{ client_name or "[Advocate / Client]" }}
{{ client_address or "" }}""",
	},
	{
		"template_name": "Bail Application (Regular)",
		"vertical": "Criminal Defense",
		"drafting_type": "Litigation",
		"description": "Regular bail application under Section 437 CrPC / 483 BNSS.",
		"template_body": """APPLICATION FOR REGULAR BAIL

IN THE COURT OF {{ court or "[Court Name]" }}
{{ case_number or "Case No. [_____]" }}

{{ party_complainant or "[Complainant / State]" }}
Versus
{{ party_accused or "[Accused Name]" }}

APPLICATION ON BEHALF OF THE ACCUSED FOR GRANT OF BAIL

MOST RESPECTFULLY SHOWETH:

1. That the applicant is the accused in the above case registered at {{ police_station or "[Police Station]" }} as FIR No. {{ fir_number or "[FIR No.]" }} dated {{ fir_date or "[date]" }} for offences punishable under {{ sections_charged or "[sections]" }}.

2. That the applicant has been arrested and is presently in {{ custody_status or "[custody status]" }} in connection with the said case.

3. That the applicant is innocent and has been falsely implicated in the present case.

4. That the applicant undertakes to abide by any conditions that this Hon'ble Court may impose.

PRAYER

In view of the facts and circumstances stated above, it is most respectfully prayed that this Hon'ble Court may be pleased to release the applicant on bail in connection with the above case, in the interest of justice.

AND FOR THIS ACT OF KINDNESS, THE APPLICANT SHALL EVER PRAY.

{{ client_name or "[Applicant]" }}
Through Advocate
{{ client_address or "" }}""",
	},
	{
		"template_name": "Anticipatory Bail Application",
		"vertical": "Criminal Defense",
		"drafting_type": "Litigation",
		"description": "Pre-arrest bail under Section 438 CrPC / 482 BNSS.",
		"template_body": """APPLICATION FOR ANTICIPATORY BAIL

IN THE COURT OF {{ court or "[Court Name]" }}
{{ case_number or "Case No. [_____]" }}

APPLICATION UNDER SECTION 438 CrPC / 482 BNSS FOR ANTICIPATORY BAIL ON BEHALF OF {{ client_name or "[Applicant]" }}

MOST RESPECTFULLY SHOWETH:

1. That the applicant apprehends arrest in connection with FIR No. {{ fir_number or "[FIR No.]" }} dated {{ fir_date or "[date]" }} registered at {{ police_station or "[Police Station]" }} under {{ sections_charged or "[sections]" }}.

2. That the applicant has not been arrested so far and apprehends arrest at the hands of the investigating agency.

3. That the applicant is a law-abiding citizen and undertakes to cooperate with the investigation and appear before the investigating officer as and when required.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to grant anticipatory bail to the applicant in the event of arrest, on such terms and conditions as this Hon'ble Court deems fit.

{{ client_name or "[Applicant]" }}
Through Advocate""",
	},
	{
		"template_name": "Legal Notice (Civil)",
		"vertical": "Civil Litigation",
		"drafting_type": "Litigation",
		"description": "Pre-litigation legal notice for civil recovery / claims.",
		"template_body": """LEGAL NOTICE

TO,
{{ party_respondent or "[Recipient Name]" }}
{{ client_address or "" }}

FROM,
{{ client_name or "[Sender Name]" }}
Through Advocate

DATED: {{ today }}

Subject: Legal notice demanding {{ claim_amount or "[amount]" }} with interest

Dear Sir/Madam,

1. We act on behalf of our client {{ client_name or "[client]" }}, who has approached us with the following grievance.

2. Our client states that you are liable to pay a sum of Rs. {{ claim_amount or "[amount]" }} arising out of a cause of action that occurred on {{ cause_of_action_date or "[date]" }}.

3. Despite repeated requests, you have failed to discharge the said liability.

TAKE NOTICE that unless the aforesaid amount is paid within 15 days from the receipt of this notice, our client shall be constrained to institute appropriate civil proceedings against you, at your entire risk as to costs.

Yours faithfully,
For {{ client_name or "[Client]" }}
Advocate""",
	},
	{
		"template_name": "Plaint (Recovery Suit) — Skeleton",
		"vertical": "Civil Litigation",
		"drafting_type": "Litigation",
		"description": "Structured skeleton for a suit for recovery of money.",
		"template_body": """SUIT FOR RECOVERY OF MONEY

IN THE COURT OF {{ court or "[Court Name]" }}
Suit No. {{ case_number or "[_____]" }}

{{ party_plaintiff or "[Plaintiff]" }}
Versus
{{ party_defendant or "[Defendant]" }}

PLAINT

1. The plaintiff is {{ client_name or "[plaintiff]" }}, residing at {{ client_address or "[address]" }}.

2. The defendant is {{ party_defendant or "[defendant]" }}, residing at {{ client_address or "[address]" }}.

3. The cause of action for the present suit arose on {{ cause_of_action_date or "[date]" }} when the defendant became liable to pay the plaintiff a sum of Rs. {{ claim_amount or "[amount]" }}.

4. The suit is within the period of limitation ({{ limitation_years or "[years]" }} years from the cause of action).

5. The court fee paid is adequate and the suit is properly valued at Rs. {{ suit_valuation or claim_amount or "[valuation]" }}.

PRAYER

It is most respectfully prayed that this Hon'ble Court be pleased to pass a decree in favour of the plaintiff and against the defendant for recovery of Rs. {{ claim_amount or "[amount]" }} with interest and costs, and grant such other relief as this Hon'ble Court deems fit.

{{ client_name or "[Plaintiff]" }}
Through Advocate""",
	},
	{
		"template_name": "NDA (Mutual Non-Disclosure Agreement)",
		"vertical": "Corporate / Commercial",
		"drafting_type": "Transactional",
		"description": "Mutual NDA with standard confidentiality clauses.",
		"template_body": """MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual Non-Disclosure Agreement ("Agreement") is made on {{ today }} between:

{{ client_name or "[Party A]" }}, having its principal place of business at {{ client_address or "[address]" }} ("Party A")

AND

{{ party_respondent or "[Party B]" }} ("Party B")

1. PURPOSE: The parties wish to explore a business relationship and may disclose Confidential Information to each other.

2. CONFIDENTIAL INFORMATION: "Confidential Information" means all non-public information disclosed by one party to the other, whether oral or written, including business plans, financial data, client lists, technical data and trade secrets.

3. OBLIGATIONS: Each party shall (a) hold Confidential Information in strict confidence; (b) use it solely for the purpose of evaluating the business relationship; and (c) not disclose it to third parties without prior written consent.

4. EXCEPTIONS: Confidential Information does not include information that is publicly available, independently developed, or rightfully received from a third party without restriction.

5. TERM: This Agreement shall remain in effect for 2 (two) years from the date of execution, and confidentiality obligations shall survive termination.

6. GOVERNING LAW: This Agreement shall be governed by the laws of India and subject to the exclusive jurisdiction of the courts at {{ jurisdiction or "[city]" }}.

IN WITNESS WHEREOF, the parties have executed this Agreement on the date first above written.

{{ client_name or "[Party A]" }}                        {{ party_respondent or "[Party B]" }}""",
	},
	{
		"template_name": "Divorce Petition — Mutual Consent (Skeleton)",
		"vertical": "Family Law",
		"drafting_type": "Litigation",
		"sensitive": 1,
		"description": "Sensitive template — generated documents require mandatory lawyer review.",
		"template_body": """PETITION FOR DIVORCE BY MUTUAL CONSENT

IN THE COURT OF {{ court or "[Court Name]" }}
Petition No. {{ case_number or "[_____]" }}

{{ party_petitioner or "[Petitioner/Husband]" }}
Versus
{{ party_respondent or "[Respondent/Wife]" }}

PETITION UNDER SECTION 13B OF THE HINDU MARRIAGE ACT, 1955

1. The parties were married on {{ intake_marriage_date or "[marriage date]" }} at {{ intake_place_of_marriage or "[place]" }} as per Hindu rites and customs.

2. The parties have been living separately for a period of more than one year and have not been able to live together.

3. They have mutually agreed that the marriage should be dissolved.

4. There has been no collusion between the parties and no petition has been withdrawn earlier.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to pass a decree of divorce by mutual consent, dissolving the marriage, with costs.

[LAWYER REVIEW REQUIRED: verify grounds, cooling-off waiver, settlement terms before filing]

{{ client_name or "[Petitioner]" }}
Through Advocate""",
	},
	{
		"template_name": "Eviction Notice",
		"vertical": "Property / Real Estate Disputes",
		"drafting_type": "Litigation",
		"description": "Notice to vacate for tenancy / eviction matters.",
		"template_body": """NOTICE TO VACATE

TO,
{{ party_respondent or "[Tenant Name]" }}
{{ client_address or "" }}

FROM,
{{ client_name or "[Landlord Name]" }}

DATED: {{ today }}

Subject: Notice to vacate the premises

Dear Sir/Madam,

1. You are in occupation of the premises situated at {{ client_address or "[premises address]" }} as a tenant.

2. The tenancy stands terminated for the reasons recorded in the tenancy file ({{ intake_rent_default_period or "default in payment of rent" }}).

3. You are hereby called upon to vacate and hand over peaceful possession of the premises within 15 days of receipt of this notice.

TAKE NOTICE that in default, appropriate proceedings for eviction shall be initiated against you at your entire risk as to costs.

Yours faithfully,
{{ client_name or "[Landlord]" }}
Through Advocate""",
	},
	{
		"template_name": "Quashing Petition (Sec. 482 CrPC)",
		"vertical": "Criminal Defense",
		"drafting_type": "Litigation",
		"description": "Petition to quash FIR / proceedings under Section 482 CrPC (BNSS 528).",
		"template_body": """PETITION UNDER SECTION 482 CrPC FOR QUASHING OF FIR / PROCEEDINGS

IN THE HIGH COURT OF {{ court or "[High Court]" }}
Criminal Petition No. {{ case_number or "[_____]" }}

{{ party_petitioner or "[Petitioner]" }}
Versus
State of {{ jurisdiction or "[State]" }} & Anr.

PETITION UNDER SECTION 482 CrPC READ WITH SECTION 528 BNSS

1. The petitioner is the accused in FIR No. {{ fir_number or "[FIR No.]" }} dated {{ fir_date or "[date]" }} registered at {{ police_station or "[Police Station]" }} for offences under {{ sections_charged or "[sections]" }}.

2. The FIR does not disclose the commission of any offence and the allegations are wholly frivolous and an abuse of the process of court.

3. Continuation of the proceedings would cause grave injustice and unnecessary harassment to the petitioner.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to quash the aforesaid FIR and all consequential proceedings, in the interest of justice.

{{ client_name or "[Petitioner]" }}
Through Advocate""",
	},
	{
		"template_name": "Vakalatnama (Criminal)",
		"vertical": "Criminal Defense",
		"drafting_type": "Litigation",
		"description": "Authority to appear for the accused in criminal proceedings.",
		"template_body": """VAKALATNAMA

IN THE COURT OF {{ court or "[Court Name]" }}
{{ case_number or "Case No. [_____]" }}

I, {{ client_name or "[Client]" }}, son/daughter of ________________, residing at {{ client_address or "[address]" }}, do hereby appoint and authorize Shri/Smt. {{ assigned_advocate or "[Advocate Name]" }}, Advocate, to appear and act for me in the above case, and to conduct, prosecute or defend the same on my behalf, to file and withdraw applications, and to do all acts necessary in connection therewith.

I agree to pay the professional fees as agreed and confirm that I have understood the scope of the engagement.

Dated: {{ today }}

Signature of Client
{{ client_name or "[Client]" }}

Accepted:
{{ assigned_advocate or "[Advocate]" }}
Advocate, {{ court or "[Court]" }}""",
	},
	{
		"template_name": "Complaint under Sec. 138 / 200 CrPC",
		"vertical": "Cheque Bounce / NI Act 138",
		"drafting_type": "Litigation",
		"description": "Criminal complaint for cheque dishonour under Section 138 NI Act read with 200 CrPC.",
		"template_body": """COMPLAINT UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 READ WITH SECTION 200 CrPC

IN THE COURT OF {{ court or "[Court Name]" }}
C.C. No. {{ case_number or "[_____]" }}

{{ party_complainant or "[Complainant]" }}
Versus
{{ party_accused or "[Accused]" }}

COMPLAINT

The complainant submits:

1. That the accused issued a cheque bearing No. {{ intake_cheque_number or "[cheque no.]" }} dated {{ intake_cheque_date or "[date]" }} for Rs. {{ intake_cheque_amount or "[amount]" }} drawn on {{ intake_drawee_bank or "[bank]" }} in favour of the complainant towards discharge of a legally enforceable liability.

2. That the said cheque, on presentation, was dishonoured on {{ intake_dishonour_date or "[date]" }} with the remark \"{{ intake_dishonour_reason or "[reason]" }}\".

3. That a statutory demand notice was issued on {{ intake_demand_notice_date or "[notice date]" }} demanding payment within 15 days of receipt.

4. That the accused failed to make payment within the statutory period, thereby committing an offence under Section 138 of the Negotiable Instruments Act, 1881.

5. That the complaint is filed within the period of limitation prescribed under Section 142 of the Act.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to take cognizance of the offence, summon the accused, and proceed in accordance with law.

{{ client_name or "[Complainant]" }}
Through Advocate""",
	},
	{
		"template_name": "Written Statement",
		"vertical": "Civil Litigation",
		"drafting_type": "Litigation",
		"description": "Written statement / defence to a civil suit.",
		"template_body": """WRITTEN STATEMENT

IN THE COURT OF {{ court or "[Court Name]" }}
Suit No. {{ case_number or "[_____]" }}

{{ party_plaintiff or "[Plaintiff]" }}
Versus
{{ party_defendant or "[Defendant]" }}

WRITTEN STATEMENT ON BEHALF OF THE DEFENDANT

The defendant most respectfully submits:

1. PRELIMINARY OBJECTIONS: The suit is not maintainable in law and is barred by limitation; this Hon'ble Court lacks jurisdiction to entertain the suit.

2. ON MERITS: The averments in the plaint are denied. The defendant states that there is no subsisting cause of action against him/her, and the claim of Rs. {{ claim_amount or "[amount]" }} is baseless and denied in its entirety.

3. The defendant denies every allegation not expressly admitted herein, and prays that the suit may be dismissed with costs.

{{ client_name or "[Defendant]" }}
Through Advocate""",
	},
	{
		"template_name": "Consumer Complaint (District Forum)",
		"vertical": "Civil Litigation",
		"drafting_type": "Litigation",
		"description": "Complaint before the District Consumer Disputes Redressal Commission.",
		"template_body": """CONSUMER COMPLAINT

BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION, {{ jurisdiction or "[District]" }}
Consumer Complaint No. {{ case_number or "[_____]" }}

{{ party_complainant or "[Complainant]" }}
Versus
{{ party_respondent or "[Opposite Party]" }}

COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019

The complainant states:

1. That the complainant purchased {{ intake_product_service or "[product/service]" }} from the opposite party for consideration.

2. That the opposite party is deficient in service on account of {{ intake_deficiency_claimed or "[deficiency]" }}.

3. That despite notice, the opposite party has failed to redress the grievance.

PRAYER

It is most respectfully prayed that this Hon'ble Commission may be pleased to direct the opposite party to rectify the deficiency, refund the amount with interest, and award compensation for mental agony and costs.

{{ client_name or "[Complainant]" }}
Through Advocate""",
	},
	{
		"template_name": "MACT Claim Petition",
		"vertical": "Civil Litigation",
		"drafting_type": "Litigation",
		"description": "Motor Accident Claims Tribunal petition for compensation.",
		"template_body": """CLAIM PETITION BEFORE MOTOR ACCIDENT CLAIMS TRIBUNAL

IN THE COURT OF {{ court or "[MACT, District]" }}
M.V.C. No. {{ case_number or "[_____]" }}

{{ party_petitioner or "[Claimant]" }}
Versus
{{ party_respondent or "[Insurer / Owner / Driver]" }}

CLAIM PETITION UNDER SECTION 166 OF THE MOTOR VEHICLES ACT, 1988

The petitioner submits:

1. That on {{ intake_accident_date or "[accident date]" }} the petitioner was involved in a motor vehicle accident resulting in injuries/damage.

2. That the accident occurred due to the rash and negligent driving of the vehicle insured with {{ intake_insurance_company or "[insurance company]" }}.

3. That the petitioner claims compensation as detailed below.

PRAYER

It is most respectfully prayed that this Hon'ble Tribunal may be pleased to award compensation of Rs. {{ claim_amount or "[amount]" }} with interest from the date of the petition, and costs.

{{ client_name or "[Petitioner]" }}
Through Advocate""",
	},
	{
		"template_name": "Maintenance Application (Sec. 125 CrPC)",
		"vertical": "Family Law",
		"drafting_type": "Litigation",
		"sensitive": 1,
		"description": "Application for maintenance under Section 125 CrPC / BNSS 144 — sensitive, lawyer review required.",
		"template_body": """APPLICATION FOR MAINTENANCE UNDER SECTION 125 CrPC / 144 BNSS

IN THE COURT OF {{ court or "[Court Name]" }}
Application No. {{ case_number or "[_____]" }}

{{ party_petitioner or "[Applicant]" }}
Versus
{{ party_respondent or "[Respondent]" }}

APPLICATION FOR MAINTENANCE

The applicant submits:

1. That the applicant is the wife/legally wedded spouse of the respondent, married on {{ intake_marriage_date or "[marriage date]" }}.

2. That the respondent has neglected and refused to maintain the applicant, who is unable to maintain herself.

3. That the respondent is earning and capable of maintaining the applicant.

[LAWYER REVIEW REQUIRED: verify grounds, income proof and quantum of interim maintenance]

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to order the respondent to pay maintenance of Rs. {{ intake_interim_maintenance_requested or "[amount]" }} per month to the applicant.

{{ client_name or "[Applicant]" }}
Through Advocate""",
	},
	{
		"template_name": "Custody Petition",
		"vertical": "Family Law",
		"drafting_type": "Litigation",
		"sensitive": 1,
		"description": "Petition for custody/guardianship of minor children — sensitive, lawyer review required.",
		"template_body": """PETITION FOR CUSTODY / GUARDIANSHIP

IN THE COURT OF {{ court or "[Court Name]" }}
Petition No. {{ case_number or "[_____]" }}

{{ party_petitioner or "[Petitioner]" }}
Versus
{{ party_respondent or "[Respondent]" }}

PETITION FOR CUSTODY OF MINOR CHILDREN

The petitioner submits:

1. That the petitioner is the father/mother of the minor child(ren) born of the marriage solemnized on {{ intake_marriage_date or "[marriage date]" }}.

2. That the minor child(ren) are presently in the custody of the respondent and the petitioner is entitled to custody in the welfare of the child(ren).

3. That the petitioner is capable of providing proper care, education and upbringing.

[LAWYER REVIEW REQUIRED: welfare assessment, current custody arrangement and interim custody terms]

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to grant custody of the minor child(ren) to the petitioner and pass such interim orders as are in the welfare of the child(ren).

{{ client_name or "[Petitioner]" }}
Through Advocate""",
	},
	{
		"template_name": "Section 498A Complaint Draft",
		"vertical": "Family Law",
		"drafting_type": "Litigation",
		"sensitive": 1,
		"description": "Complaint draft for cruelty / dowry harassment under Section 498A IPC — sensitive, lawyer review mandatory.",
		"template_body": """COMPLAINT UNDER SECTION 498A IPC / 85 BNSS (DOWRY HARASSMENT)

IN THE COURT OF {{ court or "[Court Name]" }}
Complaint No. {{ case_number or "[_____]" }}

{{ party_complainant or "[Complainant]" }}
Versus
{{ party_accused or "[Accused]" }}

COMPLAINT FOR CRUELTY AND DOWRY HARASSMENT

The complainant submits:

1. That the complainant was married to the accused on {{ intake_marriage_date or "[marriage date]" }} and was subjected to cruelty and harassment in connection with dowry.

2. That the complainant was driven out of the matrimonial home and the accused persons have demanded additional dowry.

3. That the complainant has approached the jurisdictional police and this complaint is filed for appropriate action.

[LAWYER REVIEW REQUIRED: high-sensitivity matter — verify FIR status, evidence and witness details before any filing]

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to take cognizance and issue process against the accused.

{{ client_name or "[Complainant]" }}
Through Advocate""",
	},
	{
		"template_name": "Partition Suit Draft",
		"vertical": "Property / Real Estate Disputes",
		"drafting_type": "Litigation",
		"description": "Suit for partition and separate possession of ancestral property.",
		"template_body": """SUIT FOR PARTITION AND SEPARATE POSSESSION

IN THE COURT OF {{ court or "[Court Name]" }}
Suit No. {{ case_number or "[_____]" }}

{{ party_plaintiff or "[Plaintiff]" }}
Versus
{{ party_defendant or "[Defendants]" }}

PLAINT FOR PARTITION

1. The plaintiff submits that the suit property situated at {{ client_address or "[property description]" }} bearing survey No. {{ intake_survey_number or "[survey no.]" }} is {{ intake_ancestral_property or "ancestral" }} joint family property.

2. The plaintiff and the defendants are co-owners entitled to their respective shares.

3. The plaintiff is entitled to partition and separate possession of his/her share, and the suit is within limitation.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to decree partition and separate possession of the plaintiff's share, appoint a Commissioner for division if necessary, and award costs.

{{ client_name or "[Plaintiff]" }}
Through Advocate""",
	},
	{
		"template_name": "RERA Complaint Draft",
		"vertical": "Property / Real Estate Disputes",
		"drafting_type": "Litigation",
		"description": "Complaint before the State RERA authority for builder delay / defect.",
		"template_body": """COMPLAINT BEFORE THE RERA AUTHORITY

BEFORE THE {{ jurisdiction or "[State]" }} REAL ESTATE REGULATORY AUTHORITY

Complaint No. {{ case_number or "[_____]" }}

{{ party_complainant or "[Allottee]" }}
Versus
{{ party_respondent or "[Builder/Promoter]" }}

COMPLAINT UNDER SECTION 31 OF THE RERA ACT, 2016

The complainant submits:

1. That the complainant booked a unit in the project registered as {{ intake_rera_project_number or "[RERA registration no.]" }} of {{ intake_builder_name or "[promoter]" }}.

2. That the promoter has delayed possession by {{ intake_possession_delay or "[delay period]" }} and/or has delivered defective construction.

3. That despite representations, the promoter has failed to remedy the same.

PRAYER

It is most respectfully prayed that this Hon'ble Authority may be pleased to direct the promoter to complete/rectify the project, refund the amount with interest, and award compensation and costs.

{{ client_name or "[Complainant]" }}
Through Advocate""",
	},
	{
		"template_name": "Trademark Objection Reply",
		"vertical": "IP Law",
		"drafting_type": "Litigation",
		"description": "Reply to an examination/objection report on a trademark application.",
		"template_body": """REPLY TO EXAMINATION REPORT / OBJECTION

BEFORE THE REGISTRAR OF TRADEMARKS, {{ jurisdiction or "[Office]" }}
Application No. {{ intake_application_number or "[application no.]" }}

In the matter of: {{ client_name or "[Applicant]" }}

REPLY TO OBJECTION

The applicant submits the following reply to the examination report dated {{ intake_filing_date or "[date]" }}:

1. The mark applied for is distinctive and capable of distinguishing the applicant's goods/services.

2. The mark is not deceptively similar to any prior mark and there is no likelihood of confusion.

3. The applicant has bona fide and continuous use of the mark since prior to the application date.

PRAYER

It is respectfully prayed that the objection be withdrawn and the application be proceeded to registration.

For {{ client_name or "[Applicant]" }}
Through Advocate""",
	},
	{
		"template_name": "Renewal Reminder Letter (IP)",
		"vertical": "IP Law",
		"drafting_type": "Transactional",
		"description": "Internal reminder letter for an upcoming IP renewal deadline.",
		"template_body": """RENEWAL REMINDER

TO,
{{ client_name or "[Rights Holder]" }}
{{ client_address or "[address]" }}

FROM,
{{ assigned_advocate or "[Firm Name]" }}

DATED: {{ today }}

Subject: Renewal of {{ intake_ip_type or "[IP right]" }} {{ intake_application_number or "[registration no.]" }}

Dear Sir/Madam,

Please note that the renewal of the above {{ intake_ip_type or "[IP right]" }} falls due on {{ intake_renewal_due_date or "[renewal date]" }}. Kindly provide instructions and the prescribed fee at the earliest so that the renewal can be filed within time and the registration is not allowed to lapse.

Yours faithfully,
{{ assigned_advocate or "[Firm Name]" }}""",
	},
	{
		"template_name": "Infringement Suit Draft",
		"vertical": "IP Law",
		"drafting_type": "Litigation",
		"description": "Suit for infringement of trademark/copyright with interim injunction.",
		"template_body": """SUIT FOR INFRINGEMENT OF {{ intake_ip_type or "[IP right]" }}

IN THE COURT OF {{ court or "[Court Name]" }}
C.S. No. {{ case_number or "[_____]" }}

{{ party_plaintiff or "[Plaintiff]" }}
Versus
{{ party_defendant or "[Defendant]" }}

PLAINT FOR INFRINGEMENT

1. The plaintiff is the proprietor of {{ intake_ip_type or "[IP right]" }} {{ intake_application_number or "[registration no.]" }} filed on {{ intake_filing_date or "[filing date]" }}.

2. The defendant has, without authorization, used a mark/work identical/deceptively similar to the plaintiff's {{ intake_ip_type or "[IP right]" }}, causing confusion and injury.

3. A cease-and-desist notice was served {{ intake_cease_desist_date or "[date]" }}, but the defendant has continued the infringing activity.

PRAYER

It is most respectfully prayed that this Hon'ble Court may be pleased to grant a decree of permanent injunction restraining infringement, damages, rendition of accounts, and costs, with interim relief in the meantime.

{{ client_name or "[Plaintiff]" }}
Through Advocate""",
	},
	{
		"template_name": "Cease and Desist Notice (IP)",
		"vertical": "IP Law",
		"drafting_type": "Litigation",
		"description": "Cease-and-desist for trademark / copyright infringement.",
		"template_body": """CEASE AND DESIST NOTICE

TO,
{{ party_respondent or "[Infringer Name]" }}

FROM,
{{ client_name or "[Rights Holder]" }}
Through Advocate

DATED: {{ today }}

Subject: Cease and desist — infringement of {{ intake_ip_type or "[IP right]" }} {{ intake_application_number or "[registration no.]" }}

Dear Sir/Madam,

1. Our client is the proprietor of the {{ intake_ip_type or "[IP right]" }} bearing registration/application No. {{ intake_application_number or "[number]" }}, filed on {{ intake_filing_date or "[date]" }}.

2. Your use of a mark/work identical/deceptively similar to our client's {{ intake_ip_type or "[IP right]" }} constitutes infringement.

3. You are hereby called upon to cease and desist from such use, and to furnish an undertaking of non-repetition within 15 days.

TAKE NOTICE that failure to comply shall leave our client with no option but to initiate appropriate legal proceedings.

Yours faithfully,
{{ client_name or "[Rights Holder]" }}
Through Advocate""",
	},
]


# --------------------------------------------------------------------------- seeding helpers
def _exists(doctype, name):
	return frappe.db.exists(doctype, name)


def seed_verticals():
	"""Create verticals, matter types, intake forms and document templates if missing."""
	for v in VERTICALS:
		create_vertical(v)
		create_intake_form(v)
	for t in DOC_TEMPLATES:
		create_document_template(t)


def create_vertical(v):
	if _exists("Legal Vertical", v["vertical_name"]):
		doc = frappe.get_doc("Legal Vertical", v["vertical_name"])
	else:
		doc = frappe.new_doc("Legal Vertical")
		doc.vertical_name = v["vertical_name"]
	doc.update(
		{
			"code": v.get("code"),
			"priority": v.get("priority"),
			"color": v.get("color"),
			"description": v.get("description"),
			"milestone_sequence": json.dumps(v.get("milestone_sequence", [])),
			"enabled": 1,
		}
	)
	doc.template_documents = []
	for td in v.get("template_documents", []):
		doc.append("template_documents", {"document_name": td})
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	for mt in v.get("matter_types", []):
		name = f"{v['vertical_name']}-{mt['matter_type']}"
		if _exists("Matter Type", name):
			continue
		mt_doc = frappe.new_doc("Matter Type")
		mt_doc.update(
			{
				"matter_type": mt["matter_type"],
				"vertical": v["vertical_name"],
				"code": mt.get("code"),
				"is_sub_type": mt.get("is_sub_type", 0),
				"milestone_sequence": json.dumps(mt.get("milestone_sequence", [])),
				"enabled": 1,
			}
		)
		mt_doc.flags.ignore_permissions = True
		mt_doc.insert(ignore_permissions=True)


def create_intake_form(v):
	template_name = next(
		(f["template_name"] for f in INTAKE_FORMS if f["vertical"] == v["vertical_name"]), None
	)
	if not template_name:
		return
	if _exists("Intake Form Template", template_name):
		return
	data = next(f for f in INTAKE_FORMS if f["vertical"] == v["vertical_name"])
	doc = frappe.new_doc("Intake Form Template")
	doc.update(
		{
			"template_name": template_name,
			"vertical": v["vertical_name"],
			"description": data.get("description"),
			"status": "Published",
			"version": 1,
			"active": 1,
		}
	)
	for f in data["fields"]:
		doc.append("fields", f)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)


def create_document_template(t):
	if _exists("Document Template", t["template_name"]):
		return
	doc = frappe.new_doc("Document Template")
	doc.update(
		{
			"template_name": t["template_name"],
			"vertical": t["vertical"],
			"drafting_type": t.get("drafting_type", "Litigation"),
			"status": "Published",
			"version": 1,
			"sensitive": t.get("sensitive", 0),
			"description": t.get("description", ""),
			"template_body": t["template_body"],
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
