import unittest

from chamber.tests.stubs import install

install()

from chamber.utils.timeline_engine import band_status


class TestBandStatus(unittest.TestCase):
	def test_expired(self):
		self.assertEqual(band_status(-1), "expired")
		self.assertEqual(band_status(-30), "expired")

	def test_critical(self):
		self.assertEqual(band_status(0), "critical")
		self.assertEqual(band_status(15), "critical")

	def test_warning(self):
		self.assertEqual(band_status(16), "warning")
		self.assertEqual(band_status(60), "warning")

	def test_ok(self):
		self.assertEqual(band_status(61), "ok")
		self.assertEqual(band_status(365), "ok")


if __name__ == "__main__":
	unittest.main()
