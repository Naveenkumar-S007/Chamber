import unittest

from chamber.tests.stubs import install

install()

from chamber.chamber.doctype.legal_matter.legal_matter import LegalMatter


class TestAutoRoute(unittest.TestCase):
	def make_matter(self, **kwargs):
		doc = LegalMatter()
		doc.portal = ""
		doc.routing_tier = ""
		doc.matter_type = ""
		doc.vertical = None
		for k, v in kwargs.items():
			setattr(doc, k, v)
		return doc

	def test_dv_routes_to_magistrate(self):
		doc = self.make_matter(matter_type="Domestic Violence (PWDVA) 498A")
		doc.auto_route()
		self.assertEqual(doc.routing_tier, "Magistrate Court")

	def test_anticipatory_bail_routes_to_high_court(self):
		doc = self.make_matter(matter_type="Anticipatory Bail")
		doc.auto_route()
		self.assertEqual(doc.routing_tier, "High Court")

	def test_consumer_routes_to_consumer_forum(self):
		doc = self.make_matter(matter_type="Consumer Complaint")
		doc.auto_route()
		self.assertEqual(doc.routing_tier, "Consumer Forum")

	def test_mact_routes_to_tribunal(self):
		doc = self.make_matter(matter_type="MACT Claim")
		doc.auto_route()
		self.assertEqual(doc.routing_tier, "MACT Tribunal")

	def test_ip_matter_gets_ip_portal(self):
		doc = self.make_matter(matter_type="Trademark Infringement")
		doc.auto_route()
		self.assertEqual(doc.portal, "IP India")

	def test_ibc_matter_gets_nclt_portal(self):
		doc = self.make_matter(matter_type="IBC Insolvency Petition")
		doc.auto_route()
		self.assertEqual(doc.portal, "NCLT / NCLAT")

	def test_rera_matter_gets_rera_portal(self):
		doc = self.make_matter(matter_type="RERA Complaint")
		doc.auto_route()
		self.assertEqual(doc.portal, "State RERA")

	def test_existing_portal_not_overridden(self):
		doc = self.make_matter(matter_type="Trademark Infringement", portal="eCourts")
		doc.auto_route()
		self.assertEqual(doc.portal, "eCourts")


if __name__ == "__main__":
	unittest.main()
