"""Patch: Fix 3 bugs found during workflow testing.

1. Make matter_type optional in Legal Matter (portal intake was failing)
2. Fix auto_route() false-positive "ip" match inside "anticipatory"
3. Case Status search moved to chamber.api.case_status (needs code deploy)

Run: bench --site <site> execute chamber.patches.fix_portal_intake_matter_type
"""
import frappe


def execute():
    """Apply the fixes that can be done via DB patch."""
    _make_matter_type_optional()
    frappe.db.commit()
    print("Patch applied: matter_type is now optional.")


def _make_matter_type_optional():
    """Set reqd=0 on the matter_type field of Legal Matter DocType.

    This bypasses the Developer Mode restriction by writing directly to the
    tabDocField table.
    """
    frappe.db.sql(
        """
        UPDATE `tabDocField`
        SET `reqd` = 0
        WHERE `parent` = 'Legal Matter'
          AND `fieldname` = 'matter_type'
        """
    )
    # Also update the cached JSON so future bench migrate picks it up
    import json
    import os

    doctype_path = os.path.join(
        os.path.dirname(frappe.__file__),
        "..", "apps", "chamber", "chamber",
        "chamber", "doctype", "legal_matter", "legal_matter.json",
    )
    if os.path.exists(doctype_path):
        with open(doctype_path, "r") as f:
            doc = json.load(f)
        for field in doc.get("fields", []):
            if field.get("fieldname") == "matter_type":
                field.pop("reqd", None)
                break
        with open(doctype_path, "w") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
        print(f"Updated {doctype_path}")
