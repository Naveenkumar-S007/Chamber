"""iCalendar (.ics) invite generation for hearing reminders."""

import hashlib


def build_ics(summary, start_dt, end_dt=None, description="", location="", organizer="Chamber", uid=None):
	"""Build a minimal, widely-supported VCALENDAR 2.0 payload.

	Args:
	    summary: event title
	    start_dt / end_dt: naive datetime objects (local time, DTSTART uses
	        floating local time which is fine for court hearing reminders)
	    description, location: optional free text
	    organizer: display name for the ORGANIZER property
	    uid: stable event id (defaults to a hash of summary + start)
	"""
	from datetime import datetime, timedelta

	if end_dt is None:
		end_dt = start_dt + timedelta(hours=1)
	if uid is None:
		uid = hashlib.sha1(f"{summary}|{start_dt.isoformat()}".encode("utf-8")).hexdigest()[:16] + "@chamber"

	def fmt(dt):
		return dt.strftime("%Y%m%dT%H%M%S")

	lines = [
		"BEGIN:VCALENDAR",
		"VERSION:2.0",
		"PRODID:-//Chamber//Hearing Reminder//EN",
		"CALSCALE:GREGORIAN",
		"METHOD:PUBLISH",
		"BEGIN:VEVENT",
		f"UID:{uid}",
		f"DTSTAMP:{fmt(datetime.now())}",
		f"DTSTART:{fmt(start_dt)}",
		f"DTEND:{fmt(end_dt)}",
		f"SUMMARY:{summary}",
	]
	if description:
		lines.append("DESCRIPTION:" + description.replace("\n", "\\n"))
	if location:
		lines.append("LOCATION:" + location.replace("\n", "\\n"))
	lines += ["ORGANIZER;CN=" + organizer + ":mailto:noreply@chamber.local", "END:VEVENT", "END:VCALENDAR"]
	return "\r\n".join(lines) + "\r\n"
