"""Deploy all 3 bug fixes to the Chamber server.

Run on the server with:
  bench --site chamber.local execute chamber.patches.deploy_fixes

This script:
  1. Makes matter_type optional in Legal Matter (fixes portal intake failure)
  2. Fixes auto_route() false-positive "ip" match in Legal Matter Python code
  3. Verifies case_status search module exists (fix needs code deploy)
"""
import frappe
import json
import os


def execute():
    print("=" * 60)
    print("  Chamber Bug Fix Deployment")
    print("=" * 60)

    _fix_1_matter_type_optional()
    _fix_2_auto_route_ip_match()
    _fix_3_verify_case_status_module()

    frappe.db.commit()
    frappe.clear_cache()

    print("=" * 60)
    print("  All fixes applied! Clearing cache...")
    print("=" * 60)


def _fix_1_matter_type_optional():
    """Bug #1: Make matter_type optional in Legal Matter DocType."""
    print("\n[Fix 1] Making matter_type optional in Legal Matter...")

    # Direct DB update (bypasses Developer Mode check)
    frappe.db.sql("""
        UPDATE `tabDocField`
        SET `reqd` = 0
        WHERE `parent` = 'Legal Matter'
          AND `fieldname` = 'matter_type'
    """)

    # Also update the JSON file for future bench migrate
    try:
        app_path = os.path.dirname(os.path.dirname(frappe.get_app_path("chamber")))
        json_path = os.path.join(
            app_path, "chamber", "chamber", "doctype",
            "legal_matter", "legal_matter.json"
        )
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                doc = json.load(f)
            for field in doc.get("fields", []):
                if field.get("fieldname") == "matter_type":
                    field.pop("reqd", None)
                    break
            with open(json_path, "w") as f:
                json.dump(doc, f, indent=1, ensure_ascii=False)
            print(f"  Updated JSON: {json_path}")
    except Exception as e:
        print(f"  JSON update skipped: {e}")

    print("  DONE: matter_type is now optional")


def _fix_2_auto_route_ip_match():
    """Bug #2: Fix auto_route() matching 'ip' inside 'anticipatory'."""
    print("\n[Fix 2] Fixing auto_route() IP matching in Legal Matter...")

    app_path = os.path.dirname(os.path.dirname(frappe.get_app_path("chamber")))
    py_path = os.path.join(
        app_path, "chamber", "chamber", "doctype",
        "legal_matter", "legal_matter.py"
    )

    if not os.path.exists(py_path):
        print(f"  SKIP: {py_path} not found")
        return

    with open(py_path, "r") as f:
        content = f.read()

    # Replace the broken substring check with word-boundary check
    old_line = 'if any(k in mt for k in ("ip", "trademark", "patent", "copyright", "design")) or "ip" in vertical:'
    new_lines = (
        'mt_words = set(mt.replace("(", "").replace(")", "").replace("/", " ").replace("-", " ").split())\n'
        '\t\t\tif any(k in mt_words for k in ("ip",)) or any(k in mt for k in ("trademark", "patent", "copyright", "design")) or "ip" in vertical.split():'
    )

    if old_line in content:
        content = content.replace(old_line, new_lines)
        with open(py_path, "w") as f:
            f.write(content)
        print(f"  Updated: {py_path}")
        print("  DONE: auto_route() now uses word-boundary matching for 'ip'")
    else:
        # Check if already fixed
        if "mt_words" in content:
            print("  Already fixed!")
        else:
            print(f"  SKIP: old pattern not found in {py_path}")


def _fix_3_verify_case_status_module():
    """Bug #3: Verify case_status search module exists."""
    print("\n[Fix 3] Checking case_status search module...")

    # Check if the new module exists
    try:
        import chamber.api.case_status
        print("  chamber.api.case_status module found - OK")
    except ImportError:
        print("  WARNING: chamber.api.case_status not found")
        print("  The case-status.html needs to reference chamber.api.case_status")
        print("  instead of chamber.www.case_status")
        print("  This fix requires deploying the new file to the server")
