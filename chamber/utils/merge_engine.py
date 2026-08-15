import json

import frappe
from frappe.utils.jinja import render_template


def render(template_body, merge_context, throw_on_missing=False):
	"""Render a Jinja/merge-tag template with the given merge context.

	The context is enriched with frappe-standard helpers so templates can use
	filters like {{ claim_amount | frappe.utils.fmt_money }}.
	"""
	context = dict(merge_context or {})
	if throw_on_missing:
		# re-raise undefined variables instead of rendering them empty
		from jinja2 import StrictUndefined

		context["__jinja_undefined"] = StrictUndefined
	try:
		return render_template(template_body, context)
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			"Chamber document template render failed",
		)
		raise


def build_matter_context(legal_matter):
	"""Full merge context for a matter (fields + parties + hearings + intake)."""
	matter = frappe.get_doc("Legal Matter", legal_matter)
	return matter.get_merge_context()


def sanitize_merge_data(merge_context):
	"""JSON-safe copy of merge context for the Generated Document record."""
	out = {}
	for key, value in (merge_context or {}).items():
		try:
			json.dumps(value)
			out[key] = value
		except (TypeError, ValueError):
			out[key] = str(value)
	return out
