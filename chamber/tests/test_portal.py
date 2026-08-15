import unittest
from types import SimpleNamespace

from chamber.tests.stubs import install

install()

from chamber.utils.portal_client import DEFAULT_ENDPOINTS, IPIndiaConnector


class TestPortalConnector(unittest.TestCase):
	def make_connector(self):
		matter = SimpleNamespace(name="MATTER-2026-00001", get=lambda k: None)
		settings = SimpleNamespace()
		return IPIndiaConnector(matter, settings=settings)

	def test_parse_json(self):
		conn = self.make_connector()
		out = conn.parse('{"applicationStatus": "Accepted", "details": "Trademark registered"}', "application/json")
		self.assertEqual(out["status"], "Accepted")
		self.assertIn("Trademark registered", out["details"])

	def test_parse_json_list(self):
		conn = self.make_connector()
		out = conn.parse('[{"caseStatus": "Admitted", "remarks": "CIRP initiated"}]', "application/json")
		self.assertEqual(out["status"], "Admitted")

	def test_parse_html_table(self):
		conn = self.make_connector()
		html = "<html><table><tr><td>Objection</td><td>2026-08-01</td></tr></table></html>"
		out = conn.parse(html, "text/html")
		self.assertIn("Objection", out["status"])

	def test_parse_raises_on_empty(self):
		conn = self.make_connector()
		with self.assertRaises(ValueError):
			conn.parse("", "text/plain")

	def test_default_endpoints_present(self):
		self.assertIn("IP India", DEFAULT_ENDPOINTS)
		self.assertIn("NCLT / NCLAT", DEFAULT_ENDPOINTS)
		self.assertIn("State RERA", DEFAULT_ENDPOINTS)


if __name__ == "__main__":
	unittest.main()
