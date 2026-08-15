import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, today


class Caveat(Document):
	def validate(self):
		if not self.valid_until and self.filed_date:
			self.valid_until = add_days(getdate(self.filed_date), 90)

	def after_insert(self):
		self.sync_timeline_entry("Caveat filed")

	def sync_timeline_entry(self, title):
		if not self.legal_matter:
			return
		frappe.get_doc(
			{
				"doctype": "Timeline Entry",
				"legal_matter": self.legal_matter,
				"entry_date": self.filed_date or getdate(),
				"event_type": "Filing",
				"title": title,
				"description": f"{self.caveat_number} — valid until {self.valid_until}",
				"source": "Manual",
				"reference_doctype": "Caveat",
				"reference_name": self.name,
			}
		).insert(ignore_permissions=True)

	def expire_if_due(self):
		if self.status == "Active" and self.valid_until and getdate(self.valid_until) < getdate():
			self.status = "Expired"
			self.flags.ignore_permissions = True
			self.save(ignore_permissions=True)
			self.sync_timeline_entry("Caveat expired")


def expire_overdue_caveats():
	"""Daily job: flip expired caveats and email reminders for caveats about to lapse."""
	today_d = getdate()
	from frappe.utils import add_days

	settings = frappe.get_single("Chamber Settings")
	reminder_days = settings.default_reminder_days or 3

	for name in frappe.db.get_all("Caveat", filters={"status": "Active"}, pluck="name"):
		try:
			caveat = frappe.get_doc("Caveat", name)
			if caveat.valid_until and getdate(caveat.valid_until) < today_d:
				caveat.expire_if_due()
				send_expiry_reminder(caveat, expired=True, settings=settings)
			elif caveat.valid_until and getdate(caveat.valid_until) <= add_days(today_d, int(reminder_days)):
				send_expiry_reminder(caveat, expired=False, settings=settings, days_left=date_diff(caveat.valid_until, today_d))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Caveat expiry check")
	frappe.db.commit()


def send_expiry_reminder(caveat, expired=False, settings=None, days_left=0):
	"""Email the assigned advocate / client role before a caveat lapses (deduped per day)."""
	if not settings or not settings.enable_hearing_reminders:
		return
	matter_name = caveat.legal_matter
	if not matter_name:
		return
	marker = f"Caveat expiry reminder {frappe.utils.today()} {caveat.name}"
	if frappe.db.exists("Timeline Entry", {"legal_matter": matter_name, "title": marker}):
		return

	recipients = []
	advocate = frappe.db.get_value("Legal Matter", matter_name, "assigned_advocate")
	if advocate:
		recipients.append(advocate)
	if settings.reminder_recipient_role:
		recipients += [
			u.name
			for u in frappe.get_all(
				"User", filters=[["role", "like", f"%{settings.reminder_recipient_role}%"], ["enabled", "=", 1]], fields=["name"]
			)
		]
	recipients = list({r for r in recipients if r})
	if not recipients:
		return

	if expired:
		subject = frappe._("Caveat {0} has EXPIRED").format(caveat.caveat_number)
		message = frappe._(
			"Caveat {0} (valid until {1}) has expired. Renew immediately to keep protection against ex-parte orders."
		).format(caveat.caveat_number, caveat.valid_until)
	else:
		subject = frappe._("Caveat {0} expiring in {1} day(s)").format(caveat.caveat_number, days_left)
		message = frappe._(
			"Caveat {0} expires on {1} ({2} day(s) left). Renew before it lapses."
		).format(caveat.caveat_number, caveat.valid_until, days_left)
	for recipient in recipients:
		try:
			frappe.sendmail(recipients=recipient, subject=subject, message=message)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Caveat expiry reminder")

	frappe.get_doc(
		{
			"doctype": "Timeline Entry",
			"legal_matter": matter_name,
			"entry_date": getdate(),
			"event_type": "Task",
			"title": marker,
			"description": message,
			"source": "Automated",
		}
	).insert(ignore_permissions=True)
