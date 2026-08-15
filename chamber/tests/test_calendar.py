import unittest
from datetime import datetime

from chamber.utils.calendar import build_ics


class TestBuildICS(unittest.TestCase):
	def test_contains_required_properties(self):
		ics = build_ics(
			summary="Hearing Reminder: Bail application on 2026-09-01",
			start_dt=datetime(2026, 9, 1, 10, 0),
		)
		for token in ("BEGIN:VCALENDAR", "END:VCALENDAR", "BEGIN:VEVENT", "END:VEVENT", "VERSION:2.0"):
			self.assertIn(token, ics)
		self.assertIn("DTSTART:20260901T100000", ics)
		self.assertIn("DTEND:20260901T110000", ics)  # default 1h duration
		self.assertIn("SUMMARY:Hearing Reminder", ics)

	def test_stable_uid(self):
		a = build_ics("Ev", datetime(2026, 1, 1), uid="fixed-uid")
		b = build_ics("Ev", datetime(2026, 1, 1), uid="fixed-uid")
		self.assertEqual(a, b)

	def test_line_ending(self):
		ics = build_ics("X", datetime(2026, 1, 1))
		self.assertTrue(ics.endswith("\r\n"))
		self.assertNotIn("\n\n", ics)


if __name__ == "__main__":
	unittest.main()
