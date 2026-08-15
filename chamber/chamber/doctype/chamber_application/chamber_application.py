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
		for recipient in recipients:
			try:
				frappe.sendmail(recipients=recipient, subject=subject, message=message)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Chamber hearing reminder")
