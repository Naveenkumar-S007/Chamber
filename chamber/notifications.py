"""Desk notification config + in-desk notification feed helpers.

The `notification_config` hook points here so Chamber records appear in the
Desk notification bell (in-desk feed), complementing email reminders.
"""

import frappe


def get_notification_config():
	config = {
		"for_module_observers": ["chamber"],
		"Legal Matter": {
			"conditions": None,  # any update is a candidate
		},
		"Chamber Application": {
			"conditions": None,
		},
		"Hearing": {
			"conditions": None,
		},
		"Generated Document": {
			"conditions": None,
		},
		"Signature Request": {
			"conditions": None,
		},
		"Caveat": {
			"conditions": None,
		},
	}
	return config


def notify_users(users, subject, message, doctype=None, docname=None, role=None):
	"""Create in-desk Notification Log entries for a set of users.

	Users are resolved from the explicit list plus (optionally) every user
	holding `role`. Duplicate notifications per (user, subject, doc) are
	avoided within the same day.
	"""
	from frappe.utils import now_datetime

	users = list({u for u in (users or []) if u})
	if role:
		users += [u.name for u in frappe.get_all("User", filters=[["role", "like", f"%{role}%"]])]
	users = list({u for u in users if u})
	if not users:
		return 0

	created = 0
	for user in users:
		exists = frappe.db.exists(
			"Notification Log",
			{
				"for_user": user,
				"subject": subject,
				"document_type": doctype or "",
				"document_name": docname or "",
			},
		)
		if exists:
			continue
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"subject": subject,
				"email_content": message,
				"document_type": doctype or "",
				"document_name": docname or "",
			}
		).insert(ignore_permissions=True)
		created += 1
	frappe.db.commit()
	return created
