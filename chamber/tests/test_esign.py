import unittest

from chamber.tests.stubs import install

install()

from chamber.api.esign import WEBHOOK_STATUS_MAP


class TestEsignStatusMap(unittest.TestCase):
	def test_known_statuses(self):
		self.assertEqual(WEBHOOK_STATUS_MAP["signed"], "Signed")
		self.assertEqual(WEBHOOK_STATUS_MAP["completed"], "Signed")
		self.assertEqual(WEBHOOK_STATUS_MAP["viewed"], "Viewed")
		self.assertEqual(WEBHOOK_STATUS_MAP["declined"], "Declined")
		self.assertEqual(WEBHOOK_STATUS_MAP["expired"], "Expired")
		self.assertEqual(WEBHOOK_STATUS_MAP["failed"], "Failed")

	def test_unknown_statuses_not_present(self):
		# unknown provider statuses must be ignored, not mapped
		self.assertNotIn("partially_signed", WEBHOOK_STATUS_MAP)
		self.assertNotIn("", WEBHOOK_STATUS_MAP)

	def test_normalization_coverage(self):
		# every status a provider may send has a canonical target
		values = set(WEBHOOK_STATUS_MAP.values())
		self.assertTrue(values.issubset({"Signed", "Sent", "Viewed", "Declined", "Expired", "Failed"}))


if __name__ == "__main__":
	unittest.main()
