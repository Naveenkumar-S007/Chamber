import unittest

from chamber.tests.stubs import install

install()

from chamber.utils import merge_engine


class TestMergeEngine(unittest.TestCase):
	def test_renders_simple_merge_tags(self):
		out = merge_engine.render("Dear {{ client_name }},", {"client_name": "Rajesh Kumar"})
		self.assertEqual(out, "Dear Rajesh Kumar,")

	def test_missing_key_renders_empty(self):
		out = merge_engine.render("{{ unknown_key }} is fine", {})
		self.assertEqual(out, " is fine")

	def test_jinja_control_structures(self):
		out = merge_engine.render(
			"{% for p in parties %}{{ p }}{% if not loop.last %}, {% endif %}{% endfor %}",
			{"parties": ["A", "B"]},
		)
		self.assertEqual(out, "A, B")

	def test_default_filters(self):
		out = merge_engine.render("{{ claim_amount | default('0') }}", {})
		self.assertEqual(out, "0")

	def test_sanitize_merge_data(self):
		ctx = {"claim_amount": 1000, "nested": {"a": 1}, "obj": object()}
		clean = merge_engine.sanitize_merge_data(ctx)
		self.assertEqual(clean["claim_amount"], 1000)
		self.assertEqual(clean["nested"], {"a": 1})
		self.assertIsInstance(clean["obj"], str)  # non-JSON-serializable coerced to str


if __name__ == "__main__":
	unittest.main()
