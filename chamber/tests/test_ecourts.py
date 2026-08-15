import datetime
import unittest
from types import SimpleNamespace

from chamber.tests.stubs import install

install()

from chamber.utils.ecourts_client import FIELD_MAP, apply_status_to_matter, parse_hearing_date


class TestECourtsParsing(unittest.TestCase):
	def test_parse_hearing_date(self):
		self.assertIsNone(parse_hearing_date(None))
		self.assertIsNone(parse_hearing_date(""))
		self.assertEqual(parse_hearing_date("2026-08-20"), datetime.date(2026, 8, 20))

	def test_apply_status_to_matter_basic(self):
		matter = SimpleNamespace(
			case_number=None, case_type=None, case_year=None, case_status=None,
			case_stage=None, next_hearing_date=None, judge=None, cnr_number=None,
		)
		status = {
			"case_type": "C.C.",
			"case_no": "123",
			"case_year": "2026",
			"case_status": "Pending",
			"case_stage": "Evidence",
			"next_hearing_date": "2026-09-01",
			"judge": "Hon'ble Justice A. Sharma",
		}
		changed = apply_status_to_matter(matter, status)
		self.assertIn("case_number", changed)
		self.assertEqual(matter.case_number, "C.C. 123/2026")
		self.assertEqual(matter.case_stage, "Evidence")
		self.assertEqual(matter.judge, "Hon'ble Justice A. Sharma")
		self.assertIn("next_hearing_date", changed)

	def test_apply_status_to_matter_skips_null(self):
		matter = SimpleNamespace(case_stage=None, judge=None)
		status = {"case_stage": "null", "judge": "None"}
		changed = apply_status_to_matter(matter, status)
		self.assertEqual(changed, [])
		self.assertIsNone(matter.case_stage)

	def test_field_map_has_core_keys(self):
		self.assertIn("case_stage", FIELD_MAP)
		self.assertIn("next_hearing_date", FIELD_MAP)
		self.assertIn("cnr_number", FIELD_MAP)


if __name__ == "__main__":
	unittest.main()
