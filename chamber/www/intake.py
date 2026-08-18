"""Context provider for the intake form portal page."""
import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Case Intake Form"
    context.verticals = frappe.get_all(
        "Legal Vertical",
        fields=["name", "vertical_name"],
        filters={"enabled": 1},
        order_by="priority asc",
    )


@frappe.whitelist(allow_guest=True)
def submit_intake(**kwargs):
    """Create an Intake Submission from the portal form."""
    try:
        client_name = kwargs.get("client_name", "").strip()
        contact = kwargs.get("contact_number", "").strip()
        vertical = kwargs.get("vertical", "").strip()
        matter_title = kwargs.get("matter_title", "").strip()
        description = kwargs.get("description", "").strip()

        if not all([client_name, contact, vertical, matter_title, description]):
            return {"status": "error", "message": "Please fill all required fields."}

        # Create the Legal Party first
        party_name = None
        if not frappe.db.exists("Legal Party", {"party_name": client_name}):
            party = frappe.new_doc("Legal Party")
            party.party_name = client_name
            party.party_type = "Individual"
            party.role = "Client"
            party.is_client = 1
            party.contact_number = contact
            party.email = kwargs.get("email", "")
            party.address = kwargs.get("city", "")
            party.save(ignore_permissions=True)
            party_name = party.name
        else:
            party_name = frappe.db.get_value("Legal Party", {"party_name": client_name}, "name")

        # Create Legal Matter
        matter = frappe.new_doc("Legal Matter")
        matter.matter_title = matter_title
        matter.vertical = vertical
        matter.matter_type = None  # will be set by team
        matter.status = "Intake Pending"
        matter.priority = kwargs.get("priority", "Medium")
        matter.case_category = kwargs.get("case_category", "")
        matter.description = description
        matter.fir_number = kwargs.get("fir_number", "")
        matter.cnr_number = kwargs.get("cnr_number", "")
        matter.opposing_counsel = kwargs.get("opposing_counsel", "")
        matter.client = party_name
        if party_name:
            matter.append("parties", {"party": party_name})
        matter.save(ignore_permissions=True)

        frappe.db.commit()
        return {"status": "ok", "matter": matter.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Portal Intake Submission")
        return {"status": "error", "message": str(e)}
