import re

import frappe
from frappe import _
from frappe.model.document import Document

MERGE_TAG_RE = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")


class DocumentTemplate(Document):
	def validate(self):
		self.sync_merge_tags()

	def sync_merge_tags(self):
		"""Auto-discover {{ merge_tags }} used in the template body and keep mappings."""
		if not self.template_body:
			return
		tags = []
		for match in MERGE_TAG_RE.finditer(self.template_body):
			path = match.group(1)
			if path not in tags:
				tags.append(path)
		existing = {row.tag: row for row in self.merge_tags}
		self.merge_tags = []
		for tag in tags:
			prev = existing.get(tag)
			self.append(
				"merge_tags",
				{
					"tag": tag,
					"source": self.resolve_tag_source(tag),
					"mapped_field": (prev.mapped_field if prev and prev.mapped_field else tag),
					"description": (prev.description if prev and prev.description else "Merge tag used in template body"),
				},
			)

	def resolve_tag_source(self, tag):
		"""Best-effort mapping of a merge tag to where the value comes from."""
		known = {
			"client_name": "Legal Matter → Client (Legal Party)",
			"client_phone": "Legal Matter → Client contact",
			"client_email": "Legal Matter → Client email",
			"client_address": "Legal Matter → Client address",
			"matter": "Legal Matter name",
			"matter_title": "Legal Matter → Matter Title",
			"vertical": "Legal Matter → Legal Vertical",
			"matter_type": "Legal Matter → Matter Type",
			"case_number": "Legal Matter → Case Number",
			"cnr_number": "Legal Matter → CNR Number",
			"filing_date": "Legal Matter → Filing Date",
			"cause_of_action_date": "Legal Matter → Cause of Action Date",
			"claim_amount": "Legal Matter → Claim Amount",
			"suit_valuation": "Legal Matter → Suit Valuation",
			"court": "Legal Matter → Court",
			"court_bench": "Legal Matter → Court/Bench",
			"judge_name": "Legal Matter → Judge",
			"assigned_advocate": "Legal Matter → Assigned Advocate",
			"opposing_counsel": "Legal Matter → Opposing Counsel",
			"fir_number": "Legal Matter → FIR Number",
			"police_station": "Legal Matter → Police Station",
			"fir_date": "Legal Matter → Date of FIR",
			"sections_charged": "Legal Matter → Sections Charged",
			"bail_status": "Legal Matter → Bail Status",
			"custody_status": "Legal Matter → Custody Status",
			"investigating_officer": "Legal Matter → Investigating Officer",
			"statutory_deadline_date": "Legal Matter → Statutory Deadline",
			"statutory_deadline_note": "Legal Matter → Deadline Note",
			"next_hearing_date": "Legal Matter → Next Hearing",
			"today": "Today's date",
		}
		if tag in known:
			return known[tag]
		if tag.startswith("party_"):
			return "Legal Matter → Party by role"
		if tag.startswith("intake_"):
			return "Intake Submission response"
		return "Legal Matter merge context / intake responses"

	@frappe.whitelist()
	def import_from_file(self):
		"""Self-serve import: extract text + merge tags from the uploaded template file."""
		if not self.source_file:
			frappe.throw(_("Upload a template file first (source_file)."))
		text = read_template_text(self.source_file)
		if not text.strip():
			frappe.throw(_("No readable text found in the uploaded file."))
		self.template_body = text.strip()
		self.sync_merge_tags()
		self.flags.ignore_permissions = True
		self.save(ignore_permissions=True)
		return {"template_body": self.template_body, "merge_tags": [r.tag for r in self.merge_tags]}


def read_template_text(file_url):
	"""Best-effort text extraction from an uploaded .docx / .txt / .md / .pdf."""
	from frappe.utils.file_manager import get_file

	content = ""
	try:
		_, content = get_file(file_url)
		if isinstance(content, bytes):
			content = content.decode("utf-8", errors="ignore")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Chamber template file read")

	ext = (file_url or "").lower().rsplit(".", 1)[-1] if "." in (file_url or "") else ""
	if ext == "docx":
		try:
			import zipfile
			import re as _re
			import html as _html

			path = file_url
			from frappe.utils.file_manager import get_file_path

			with zipfile.ZipFile(get_file_path(file_url)) as z:
				xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
			xml = _re.sub(r"<w:p [^>]*>|<w:p>", "\n", xml)
			xml = _re.sub(r"<[^>]+>", "", xml)
			content = _html.unescape(xml)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chamber docx extraction")
	elif ext == "pdf":
		try:
			from PyPDF2 import PdfReader

			from frappe.utils.file_manager import get_file_path

			reader = PdfReader(get_file_path(file_url))
			content = "\n".join((page.extract_text() or "") for page in reader.pages)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chamber PDF extraction")
	return content or ""
