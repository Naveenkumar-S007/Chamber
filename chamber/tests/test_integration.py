"""DB integration tests — run inside a bench only.

  bench --site <site> run-tests --app chamber

Locally (no bench) these are skipped automatically.
"""
import unittest

try:
	from frappe.tests.utils import FrappeTestCase
	from frappe.utils import add_days, getdate, today

	HAS_BENCH = True
except Exception:  # pragma: no cover - local dev without frappe
	FrappeTestCase = unittest.TestCase
	HAS_BENCH = False


@unittest.skipUnless(HAS_BENCH, "bench-only integration tests")
class TestMatterIntegration(FrappeTestCase):
	def setUp(self):
		super().setUp()
		import frappe

		from chamber.setup import demo

		self.frappe = frappe
		if not frappe.db.exists("Legal Vertical", "Criminal Defense"):
			demo.run() if demo.demo_allowed() else self.skipTest("demo data not allowed in this environment")

	def make_matter(self, **kwargs):
		import frappe

		values = {
			"matter_title": "ITEST — " + frappe.generate_hash(6),
			"vertical": "Criminal Defense",
			"matter_type": "Criminal Defense-Regular Offence",
			"status": "Active",
			"case_category": "Criminal",
			"cause_of_action_date": add_days(today(), -700),
			"limitation_years": 3,
		}
		values.update(kwargs)
		doc = frappe.new_doc("Legal Matter")
		doc.update(values)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		return doc

	def test_limitation_computed(self):
		from frappe.utils import add_years

		matter = self.make_matter()
		self.assertIsNotNone(matter.limitation_expiry_date)
		self.assertEqual(
			matter.limitation_expiry_date,
			add_years(getdate(matter.cause_of_action_date), 3),
		)

	def test_matter_type_vertical_validation(self):
		import frappe

		with self.assertRaises(frappe.ValidationError):
			self.make_matter(matter_type="Civil Litigation-Recovery Suit")

	def test_merge_context_has_client(self):
		import frappe

		matter = self.make_matter()
		client = frappe.new_doc("Legal Party")
		client.update(
			{
				"party_name": "ITEST Client " + frappe.generate_hash(6),
				"party_type": "Individual",
				"role": "Client",
				"is_client": 1,
				"email": "itest@example.com",
			}
		)
		client.flags.ignore_permissions = True
		client.insert(ignore_permissions=True)
		matter.client = client.name
		matter.flags.ignore_permissions = True
		matter.save(ignore_permissions=True)
		ctx = matter.get_merge_context()
		self.assertEqual(ctx["client_name"], client.party_name)
		self.assertEqual(ctx["client_email"], "itest@example.com")

	def test_hearing_creates_timeline_entry(self):
		import frappe

		matter = self.make_matter()
		hearing = frappe.new_doc("Hearing")
		hearing.update(
			{
				"legal_matter": matter.name,
				"hearing_date": add_days(today(), 5),
				"purpose": "ITEST hearing",
				"source": "Manual",
			}
		)
		hearing.flags.ignore_permissions = True
		hearing.insert(ignore_permissions=True)
		self.assertTrue(
			frappe.db.exists(
				"Timeline Entry",
				{"legal_matter": matter.name, "reference_doctype": "Hearing", "reference_name": hearing.name},
			)
		)

	def test_deadlines_api_shape(self):
		from chamber.api.deadlines import get_upcoming

		result = get_upcoming(horizon_days=365)
		self.assertIn("deadlines", result)
		self.assertIn("counts", result)


if __name__ == "__main__":
	unittest.main()
