"""Chamber — Intake Form API

Whitelisted methods called by the intake_form page JS to fetch
a form template's field list and to submit intake responses.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_form(template=None, legal_matter=None):
    """Return the intake form template (fields + metadata) for the client renderer.

    Resolution order:
    1. If *template* is supplied by name, return that exact template.
    2. If *legal_matter* is supplied, try to match a Published template
       for the matter's vertical (and optionally matter_type).
    3. Fall back to the first active Published template overall.
    Returns None (not an error) when no template exists at all.
    """
    # 1. Explicit template name
    if template:
        try:
            doc = frappe.get_doc("Intake Form Template", template)
            return _template_payload(doc)
        except frappe.DoesNotExistError:
            frappe.throw(_("Intake Form Template '{0}' does not exist.").format(template))

    # 2. Auto-select by matter vertical
    if legal_matter:
        try:
            matter = frappe.get_doc("Legal Matter", legal_matter)
        except frappe.DoesNotExistError:
            frappe.throw(_("Legal Matter '{0}' does not exist.").format(legal_matter))

        # Try vertical + matter_type match first, then vertical-only
        filters_list = []
        if matter.vertical and matter.matter_type:
            filters_list.append(
                {
                    "status": "Published",
                    "active": 1,
                    "vertical": matter.vertical,
                    "matter_type": matter.matter_type,
                }
            )
        if matter.vertical:
            filters_list.append(
                {
                    "status": "Published",
                    "active": 1,
                    "vertical": matter.vertical,
                }
            )

        for f in filters_list:
            tpl_name = frappe.db.get_value("Intake Form Template", f, "name")
            if tpl_name:
                doc = frappe.get_doc("Intake Form Template", tpl_name)
                return _template_payload(doc)

    # 3. First available published template
    tpl_name = frappe.db.get_value(
        "Intake Form Template", {"status": "Published", "active": 1}, "name"
    )
    if tpl_name:
        doc = frappe.get_doc("Intake Form Template", tpl_name)
        return _template_payload(doc)

    # No template at all — return None (not an error)
    return None


def _template_payload(doc):
    """Build a JSON-safe dict from the template for the client renderer."""
    return {
        "name": doc.name,
        "template_name": doc.template_name,
        "vertical": doc.vertical,
        "matter_type": doc.matter_type,
        "description": doc.description,
        "fields": doc.get_fields_dict(),
    }


@frappe.whitelist()
def submit(legal_matter, intake_form_template, responses=None):
    """Create an Intake Submission and apply matching responses to the matter.

    *responses* is a JSON dict  {fieldname: value, ...}  sent by the client.
    """
    if not legal_matter:
        frappe.throw(_("Legal Matter is required."))
    if not frappe.db.exists("Legal Matter", legal_matter):
        frappe.throw(_("Legal Matter {0} does not exist.").format(legal_matter))
    if not intake_form_template:
        frappe.throw(_("Intake Form Template is required."))
    if not frappe.db.exists("Intake Form Template", intake_form_template):
        frappe.throw(
            _("Intake Form Template {0} does not exist.").format(intake_form_template)
        )

    # Parse responses — may come as a JSON string from the frontend
    if isinstance(responses, str):
        import json

        try:
            responses = json.loads(responses) if responses else {}
        except (json.JSONDecodeError, TypeError):
            responses = {}

    # Fetch the template so we can label each response row
    tpl = frappe.get_doc("Intake Form Template", intake_form_template)
    field_labels = {f.fieldname: f.label for f in tpl.fields}

    # Build response rows
    response_rows = []
    for fieldname, value in (responses or {}).items():
        if value is None or value == "":
            continue
        response_rows.append(
            {
                "fieldname": fieldname,
                "label": field_labels.get(fieldname, fieldname),
                "value": str(value),
            }
        )

    submission = frappe.get_doc(
        {
            "doctype": "Intake Submission",
            "legal_matter": legal_matter,
            "intake_form_template": intake_form_template,
            "vertical": tpl.vertical,
            "submission_date": frappe.utils.today(),
            "status": "Submitted",
            "responses": response_rows,
        }
    )
    submission.insert(ignore_permissions=True)
    submission.submit()

    # Apply matching field values onto the Legal Matter
    submission.apply_to_matter()

    return {"name": submission.name, "status": submission.status}
