import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class ChamberApplication(Document):
	def validate(self):
		self.update_next_hearing_from_log()
		self.set_defaults_from_matter()

	def update_next_hearing_from_log(self):
		"""Keep the header next-hearing date in step with the hearing log child table."""
		if self.hearing_log:
			latest = max(self.hearing_log, key=lambda h: h.hearing_date or getdate("1900-01-01"))
			if latest.next_date:
				self.next_hearing_date = latest.next_date

	def set_defaults_from_matter(self):
		if self.matter and not self.client:
			self.client = frappe.db.get_value("Legal Matter", self.matter, "client")

	def sync_timeline_entry(self):
		existing = frappe.db.get_value(
			"Timeline Entry",
			{"reference_doctype": "Chamber Application", "reference_name": self.name},
			"name",
		)
		title = f"Chamber Application — {self.application_title}"
		if existing:
			entry = frappe.get_doc("Timeline Entry", existing)
			entry.entry_date = self.filing_date or getdate()
			entry.title = title
			entry.description = self.order_summary or self.remarks
			entry.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Timeline Entry",
					"legal_matter": self.matter,
					"entry_date": self.filing_date or getdate(),
					"event_type": "Filing",
					"title": title,
					"description": self.order_summary or self.remarks,
					"source": "Manual",
					"reference_doctype": "Chamber Application",
					"reference_name": self.name,
				}
			).insert(ignore_permissions=True)


# ---------------------------------------------------------------- permissions
def _enforce_matter_level():
	try:
		return bool(frappe.db.get_single_value("Chamber Settings", "enforce_matter_level_permissions"))
	except Exception:
		return False


def _is_manager(user):
	return "System Manager" in frappe.get_roles(user) or "Chamber Manager" in frappe.get_roles(user)


def _visible_matters(user):
	if _is_manager(user):
		return None
	names = [
		r["name"]
		for r in frappe.db.get_all("Legal Matter", filters={"assigned_advocate": user}, fields=["name"])
	]
	shared = frappe.db.get_all(
		"DocShare",
		filters={"user": user, "share_doctype": "Legal Matter", "read": 1},
		fields=["share_name"],
	)
	names += [s["share_name"] for s in shared]
	return list({n for n in names if n})


def get_permission_query_conditions(user=None):
	"""Scope Chamber Application by the matter-level permission opt-in."""
	if not _enforce_matter_level():
		return ""
	user = user or frappe.session.user
	if _is_manager(user):
		return ""
	names = _visible_matters(user)
	if not names:
		return "(1 = 0)"
	escaped = ", ".join(f"'{frappe.db.escape(n)}'" for n in names)
	return f"`tabChamber Application`.matter in ({escaped})"


def has_permission(doc=None, ptype="read", user=None):
	if not _enforce_matter_level():
		return True
	user = user or frappe.session.user
	if _is_manager(user) or not doc:
		return True
	names = _visible_matters(user)
	return bool(names and doc.matter in names)


# ----------------------------------------------------------------- scheduler
def send_hearing_reminders():
	"""Daily job: notify assigned advocate / client before upcoming chamber hearings."""
	from frappe.utils import today

	settings = frappe.get_single("Chamber Settings")
	if not settings.enable_hearing_reminders:
		return

	reminder_days = settings.default_reminder_days or 3
	upcoming = frappe.db.get_all(
		"Chamber Application",
		filters={
			"next_hearing_date": (
				"between",
				(add_days(today(), 1), add_days(today(), int(reminder_days))),
			),
			"current_status": ["not in", ["Disposed", "Withdrawn"]],
		},
		fields=["name", "application_title", "next_hearing_date", "assigned_advocate", "matter"],
	)
	for app in upcoming:
		recipients = []
		if app.assigned_advocate:
			recipients.append(app.assigned_advocate)
		if settings.reminder_recipient_role:
			recipients += [
				u.name
				for u in frappe.get_all(
					"User",
					filters=[["role", "like", f"%{settings.reminder_recipient_role}%"]],
					fields=["name"],
				)
			]
		recipients = list({r for r in recipients if r})
		if not recipients:
			continue
		subject = _("Hearing Reminder: {0} on {1}").format(
			app.application_title, app.next_hearing_date
		)
		message = _(
			"Chamber Application {0} ({1}) has a hearing on {2}. Please review the file before the date."
		).format(app.name, app.application_title, app.next_hearing_date)

		# In-desk notification feed (complements email)
		try:
			from chamber.notifications import notify_users

			notify_users(
				recipients,
				subject,
				message,
				doctype="Chamber Application",
				docname=app.name,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chamber hearing in-desk notification")

		# Calendar invite (.ics attachment)
		ic_attachment = None
		try:
			from datetime import datetime

			from chamber.utils.calendar import build_ics

			hearing_dt = datetime.combine(app.next_hearing_date, datetime.min.time())
			ics = build_ics(
				summary=subject,
				start_dt=hearing_dt,
				description=message,
				location=frappe.db.get_value("Chamber Application", app.name, "court") or "",
				uid=f"hearing-{app.name}",
			)
			fname = frappe.scrub(f"hearing-{app.name}") + ".ics"
			from frappe.utils.file_manager import save_file

			f = save_file(fname, ics, "Chamber Application", app.name, is_private=1)
			ic_attachment = [{"fname": fname, "fcontent": ics}]
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Chamber hearing .ics build")

		for recipient in recipients:
			try:
				frappe.sendmail(
					recipients=recipient,
					subject=subject,
					message=message,
					attachments=ic_attachment,
				)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Chamber hearing reminder")
