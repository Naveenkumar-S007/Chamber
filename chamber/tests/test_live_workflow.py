"""Live workflow test against chamber.local server.

Creates a complete sample entry and walks it through the Chamber workflow:
  1. Legal Party → Legal Matter → Timeline Entry
  2. Hearing → Timeline sync
  3. Generated Document → Workflow advance (Draft → Internal Review → Client Review → Finalized)
  4. Case Status portal search
  5. Dashboard stats
"""
import json
import os
import sys
import requests

# Fix Windows console encoding for emoji
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE = "http://chamber.local"
SESSION = requests.Session()


def login():
    r = SESSION.post(f"{BASE}/api/method/login", data={"usr": "Administrator", "pwd": "frappe"})
    data = r.json()
    assert data.get("message") in ("OK", "Logged In"), f"Login failed: {data}"
    print("✅ Logged in as Administrator")


def api_get(method, **params):
    r = SESSION.get(f"{BASE}/api/method/{method}", params=params)
    return r.json()


def api_post(method, payload=None):
    r = SESSION.post(f"{BASE}/api/method/{method}", json=payload or {})
    return r.json()


def api_save(doctype, doc_dict):
    doc_dict["doctype"] = doctype
    # If updating an existing doc, fetch it first to get the modified timestamp
    if doc_dict.get("name"):
        r = SESSION.get(f"{BASE}/api/resource/{doctype}/{doc_dict['name']}")
        existing = r.json().get("data", {})
        # Merge: existing fields as base, overlay with our changes
        merged = {**existing, **doc_dict}
        doc_dict = merged
    r = SESSION.post(f"{BASE}/api/method/frappe.client.save", json={"doc": doc_dict})
    data = r.json()
    if "message" in data and isinstance(data["message"], dict):
        return data["message"]
    print(f"  ⚠️  Save failed: {data}")
    return None


def api_get_list(doctype, filters=None, fields=None, limit=20):
    payload = {"doctype": doctype, "limit_page_length": limit}
    if filters:
        payload["filters"] = filters
    if fields:
        payload["fields"] = fields
    r = SESSION.post(f"{BASE}/api/method/frappe.client.get_list", json=payload)
    data = r.json()
    return data.get("message", [])


def run_doc_method(doctype, name, method, args=None):
    """Call a whitelisted method on a document via run_doc_method."""
    # First fetch the doc to get modified timestamp
    r = SESSION.get(f"{BASE}/api/resource/{doctype}/{name}")
    doc_data = r.json().get("data", {})
    payload = {
        "docs": json.dumps(doc_data),
        "method": method,
        "args": json.dumps(args or {}),
    }
    r = SESSION.post(f"{BASE}/api/method/run_doc_method", json=payload)
    return r.json()


def main():
    results = []
    login()

    # ── Step 1: Create Legal Party ──
    print("\n── Step 1: Create Legal Party (Client) ──")
    import time
    ts = int(time.time())
    party_name = f"Workflow Test Client {ts}"
    party = api_save("Legal Party", {
        "party_name": party_name,
        "party_type": "Individual",
        "role": "Client",
        "is_client": 1,
        "contact_number": "+91-9999888877",
        "email": "workflow.test@example.com",
        "address": "Mumbai",
    })
    if party:
        print(f"  ✅ Party created: {party['name']}")
        results.append(("Party Created", True, party["name"]))
    else:
        results.append(("Party Created", False, "save failed"))
        print_results(results)
        return

    # ── Step 2: Create Legal Matter ──
    print("\n── Step 2: Create Legal Matter ──")
    matter = api_save("Legal Matter", {
        "naming_series": "MATTER-.YYYY.-.#####",
        "matter_title": "Anticipatory Bail - Workflow Test 498A",
        "vertical": "Criminal Defense",
        "matter_type": "Criminal Defense-Anticipatory Bail (Pre-Arrest)",
        "status": "Intake Pending",
        "priority": "High",
        "case_category": "Criminal",
        "cnr_number": "MH01-000789-2026",
        "client": party["name"],
        "assigned_advocate": "Administrator",
        "opposing_counsel": "Adv. Test Opposing",
        "fir_number": "FIR 999/2026",
        "police_station": "Andheri Police Station",
        "fir_date": "2026-08-10",
        "sections_charged": "498A IPC, 34 IPC",
        "bail_status": "Anticipatory Bail Filed",
        "custody_status": "Not Arrested",
        "description": "Workflow test: 498A anticipatory bail matter.",
        "parties": [{"party": party["name"], "role": "Client", "is_client": 1}],
    })
    if matter:
        print(f"  ✅ Matter created: {matter['name']}")
        print(f"     Status: {matter['status']}")
        print(f"     Routing tier: {matter.get('routing_tier', 'N/A')}")
        print(f"     Portal: {matter.get('portal', 'N/A')}")
        results.append(("Matter Created", True, matter["name"]))
        results.append(("Status = Intake Pending", matter["status"] == "Intake Pending", matter["status"]))
        results.append(("Routing Tier = High Court", matter.get("routing_tier") == "High Court", matter.get("routing_tier")))
    else:
        results.append(("Matter Created", False, "save failed"))
        print_results(results)
        return

    # ── Step 3: Verify Timeline Entry (auto-created on insert) ──
    print("\n── Step 3: Verify Timeline Entry (auto-created on insert) ──")
    tl_entries = api_get_list("Timeline Entry",
        filters=[["legal_matter", "=", matter["name"]]],
        fields=["name", "event_type", "title", "entry_date", "source"],
    )
    if tl_entries:
        for e in tl_entries:
            print(f"  📌 {e['title']} ({e['event_type']}) on {e['entry_date']} [source: {e['source']}]")
        has_registration = any("registered" in (e.get("title") or "").lower() for e in tl_entries)
        results.append(("Auto Timeline Entry", has_registration, f"{len(tl_entries)} entries"))
    else:
        results.append(("Auto Timeline Entry", False, "none found"))

    # ── Step 4: Transition matter to Active ──
    print("\n── Step 4: Transition Matter Status: Intake Pending → Active ──")
    matter_update = api_save("Legal Matter", {
        "name": matter["name"],
        "status": "Active",
    })
    if matter_update:
        print(f"  ✅ Matter status updated to: {matter_update['status']}")
        results.append(("Status → Active", matter_update["status"] == "Active", matter_update["status"]))
    else:
        results.append(("Status → Active", False, "update failed"))

    # ── Step 5: Create Hearing ──
    print("\n── Step 5: Create Hearing ──")
    hearing = api_save("Hearing", {
        "legal_matter": matter["name"],
        "hearing_date": "2026-09-10",
        "next_hearing_date": "2026-09-25",
        "purpose": "Anticipatory Bail - First Hearing",
        "judge": "Hon'ble Justice Kumar",
        "source": "Manual",
    })
    if hearing:
        print(f"  ✅ Hearing created: {hearing['name']}")
        results.append(("Hearing Created", True, hearing["name"]))
    else:
        results.append(("Hearing Created", False, "save failed"))

    # ── Step 6: Verify Hearing synced to Timeline ──
    print("\n── Step 6: Verify Hearing synced to Timeline ──")
    tl_entries2 = api_get_list("Timeline Entry",
        filters=[["legal_matter", "=", matter["name"]]],
        fields=["name", "event_type", "title", "entry_date", "reference_doctype"],
    )
    hearing_tl = [e for e in tl_entries2 if e.get("event_type") == "Hearing"]
    if hearing_tl:
        for e in hearing_tl:
            print(f"  📌 {e['title']} on {e['entry_date']} (ref: {e['reference_doctype']})")
        results.append(("Hearing → Timeline Sync", True, f"{len(hearing_tl)} hearing entries"))
    else:
        results.append(("Hearing → Timeline Sync", False, "no hearing timeline entries"))

    # ── Step 7: Create Generated Document ──
    print("\n── Step 7: Create Generated Document ──")
    gen_doc = api_save("Generated Document", {
        "legal_matter": matter["name"],
        "document_template": "Anticipatory Bail Application",
        "title": "Anticipatory Bail - FIR 999/2026",
        "workflow_state": "Draft",
        "status": "Draft",
        "requires_lawyer_review": 0,
        "notes": "Auto-generated for workflow test",
    })
    if gen_doc:
        print(f"  ✅ Generated Document: {gen_doc['name']} (workflow: {gen_doc['workflow_state']})")
        results.append(("Document Created", True, gen_doc["name"]))
        results.append(("Workflow = Draft", gen_doc["workflow_state"] == "Draft", gen_doc["workflow_state"]))
    else:
        results.append(("Document Created", False, "save failed"))
        print_results(results)
        return

    # ── Step 8: Advance workflow: Draft → Internal Review ──
    print("\n── Step 8: Advance Workflow: Draft → Internal Review ──")
    r = run_doc_method("Generated Document", gen_doc["name"], "advance_workflow")
    if "message" in r and isinstance(r["message"], dict):
        new_state = r["message"].get("workflow_state")
        print(f"  ✅ Workflow advanced to: {new_state}")
        results.append(("Draft → Internal Review", new_state == "Internal Review", new_state))
    else:
        print(f"  ⚠️  Advance failed: {r.get('exception', r)}")
        results.append(("Draft → Internal Review", False, str(r.get("exception", ""))))

    # ── Step 9: Advance workflow: Internal Review → Client Review ──
    print("\n── Step 9: Advance Workflow: Internal Review → Client Review ──")
    r = run_doc_method("Generated Document", gen_doc["name"], "advance_workflow",
                       {"target": "Client Review"})
    if "message" in r and isinstance(r["message"], dict):
        new_state = r["message"].get("workflow_state")
        print(f"  ✅ Workflow advanced to: {new_state}")
        results.append(("Internal Review → Client Review", new_state == "Client Review", new_state))
    else:
        print(f"  ⚠️  Advance failed: {r.get('exception', r)}")
        results.append(("Internal Review → Client Review", False, str(r.get("exception", ""))))

    # ── Step 10: Advance workflow: Client Review → Finalized ──
    print("\n── Step 10: Advance Workflow: Client Review → Finalized ──")
    r = run_doc_method("Generated Document", gen_doc["name"], "advance_workflow",
                       {"target": "Finalized"})
    if "message" in r and isinstance(r["message"], dict):
        new_state = r["message"].get("workflow_state")
        print(f"  ✅ Workflow advanced to: {new_state}")
        results.append(("Client Review → Finalized", new_state == "Finalized", new_state))
    else:
        print(f"  ⚠️  Advance failed: {r.get('exception', r)}")
        results.append(("Client Review → Finalized", False, str(r.get("exception", ""))))

    # ── Step 11: Verify Document → Timeline sync ──
    print("\n── Step 11: Verify Document → Timeline sync ──")
    tl_entries3 = api_get_list("Timeline Entry",
        filters=[["legal_matter", "=", matter["name"]]],
        fields=["name", "event_type", "title", "entry_date", "reference_doctype"],
    )
    doc_tl = [e for e in tl_entries3 if e.get("event_type") == "Document"]
    if doc_tl:
        for e in doc_tl:
            print(f"  📌 {e['title']} on {e['entry_date']} (ref: {e['reference_doctype']})")
        results.append(("Document → Timeline Sync", True, f"{len(doc_tl)} document entries"))
    else:
        results.append(("Document → Timeline Sync", False, "no document timeline entries"))

    # ── Step 12: Verify Case Status portal search ──
    print("\n── Step 12: Verify Case Status portal search ──")
    # Try the new importable module first, fall back to old www path
    search_result = api_get("chamber.api.case_status.search_matter", query=matter["name"])
    if not search_result.get("message") or not isinstance(search_result.get("message"), dict) or not search_result["message"].get("matter"):
        # Fallback: try old www path (won't work if file has hyphen)
        search_result = api_get("chamber.www.case_status.search_matter", query=matter["name"])
    sm = search_result.get("message", {})
    if sm and sm.get("matter"):
        found = sm["matter"]
        print(f"  ✅ Found: {found.get('matter_title')} (status: {found.get('status')})")
        print(f"     Vertical: {found.get('vertical_name', 'N/A')}")
        print(f"     Court: {found.get('court_name', 'N/A')}")
        print(f"     Judge: {found.get('judge_name', 'N/A')}")
        print(f"     Hearings: {len(sm.get('hearings', []))}")
        print(f"     Timeline entries: {len(sm.get('timeline', []))}")
        results.append(("Case Status Search", True, found.get("matter_title", "")))
        results.append(("Search shows hearings", len(sm.get("hearings", [])) > 0,
                        f"{len(sm.get('hearings', []))} hearings"))
        results.append(("Search shows timeline", len(sm.get("timeline", [])) > 0,
                        f"{len(sm.get('timeline', []))} entries"))
    else:
        print("  ⚠️  Matter not found via search")
        results.append(("Case Status Search", False, "matter not found"))

    # ── Step 13: Dashboard stats ──
    print("\n── Step 13: Dashboard Stats ──")
    dash = api_get("chamber.api.dashboard.get_stats")
    stats = dash.get("message", {})
    headline = stats.get("headline", {})
    if headline:
        print(f"  📊 Active Matters: {headline.get('active_matters', 0)}")
        print(f"  📊 Total Matters: {headline.get('total_matters', 0)}")
        print(f"  📊 Upcoming Hearings: {headline.get('upcoming_hearings', 0)}")
        print(f"  📊 Pending Signatures: {headline.get('pending_signatures', 0)}")
        print(f"  📊 Active Caveats: {headline.get('caveats_active', 0)}")
        print(f"  📊 Overdue Deadlines: {headline.get('overdue_deadlines', 0)}")
        results.append(("Dashboard Loads", True, f"{headline.get('total_matters', 0)} total matters"))
        results.append(("Active Matters > 0", headline.get("active_matters", 0) > 0,
                        str(headline.get("active_matters", 0))))
    else:
        results.append(("Dashboard Loads", False, "no stats"))

    # ── Summary ──
    print_results(results)


def print_results(results):
    print("\n" + "=" * 60)
    print("  WORKFLOW TEST RESULTS")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for label, ok, detail in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {label}: {detail}")
    print("=" * 60)
    print(f"  {passed}/{total} checks passed")
    print("=" * 60)

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
