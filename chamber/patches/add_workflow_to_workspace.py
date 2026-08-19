"""Add a clean workflow visualization to the Chamber workspace.

Adds a horizontal workflow diagram above the shortcuts section so users
can see the full case lifecycle at a glance.

Run on the server:
  bench --site chamber.local execute chamber.patches.add_workflow_to_workspace
"""
import json
import frappe


# ── Workflow HTML ──────────────────────────────────────────────────────────
WORKFLOW_HTML = """<div class="chamber-workflow" style="padding:20px 24px;margin-bottom:16px;background:linear-gradient(135deg,#f8f9fa 0%,#e8eaf6 100%);border-radius:10px;border:1px solid #c5cae9;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
    <i class="fa fa-sitemap" style="color:#1a237e;font-size:16px;"></i>
    <h4 style="margin:0;color:#1a237e;font-size:15px;font-weight:700;">Case Workflow</h4>
    <span style="font-size:11px;color:#7986cb;margin-left:4px;">— How a case moves through your chamber</span>
  </div>

  <div style="display:flex;align-items:flex-start;gap:0;overflow-x:auto;padding-bottom:8px;">

    <!-- Step 1: Intake -->
    <div style="flex:1;min-width:110px;text-align:center;position:relative;">
      <div style="width:44px;height:44px;border-radius:50%;background:#e3f2fd;border:2px solid #1565c0;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#1565c0;">
        <i class="fa fa-file-text-o"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">1. Intake</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Client submits case<br>via portal or desk</div>
      <div style="position:absolute;right:-12px;top:16px;color:#90a4ae;font-size:14px;z-index:1;">
        <i class="fa fa-chevron-right"></i>
      </div>
    </div>

    <!-- Step 2: Matter Registered -->
    <div style="flex:1;min-width:110px;text-align:center;position:relative;">
      <div style="width:44px;height:44px;border-radius:50%;background:#fff8e1;border:2px solid #f9a825;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#f9a825;">
        <i class="fa fa-briefcase"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">2. Registered</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Legal Matter created<br>timeline entry auto-added</div>
      <div style="position:absolute;right:-12px;top:16px;color:#90a4ae;font-size:14px;z-index:1;">
        <i class="fa fa-chevron-right"></i>
      </div>
    </div>

    <!-- Step 3: Active -->
    <div style="flex:1;min-width:110px;text-align:center;position:relative;">
      <div style="width:44px;height:44px;border-radius:50%;background:#e8f5e9;border:2px solid #2e7d32;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#2e7d32;">
        <i class="fa fa-check-circle"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">3. Active</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Team reviews &amp; sets<br>matter type, court, judge</div>
      <div style="position:absolute;right:-12px;top:16px;color:#90a4ae;font-size:14px;z-index:1;">
        <i class="fa fa-chevron-right"></i>
      </div>
    </div>

    <!-- Step 4: Hearings & Docs -->
    <div style="flex:1;min-width:110px;text-align:center;position:relative;">
      <div style="width:44px;height:44px;border-radius:50%;background:#f3e5f5;border:2px solid #7b1fa2;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#7b1fa2;">
        <i class="fa fa-gavel"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">4. Hearings &amp; Docs</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Track hearings, generate<br>&amp; approve documents</div>
      <div style="position:absolute;right:-12px;top:16px;color:#90a4ae;font-size:14px;z-index:1;">
        <i class="fa fa-chevron-right"></i>
      </div>
    </div>

    <!-- Step 5: eCourts Sync -->
    <div style="flex:1;min-width:110px;text-align:center;position:relative;">
      <div style="width:44px;height:44px;border-radius:50%;background:#e0f2f1;border:2px solid #00897b;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#00897b;">
        <i class="fa fa-refresh"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">5. eCourts Sync</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Auto-sync status,<br>orders &amp; cause lists</div>
      <div style="position:absolute;right:-12px;top:16px;color:#90a4ae;font-size:14px;z-index:1;">
        <i class="fa fa-chevron-right"></i>
      </div>
    </div>

    <!-- Step 6: Close -->
    <div style="flex:1;min-width:110px;text-align:center;">
      <div style="width:44px;height:44px;border-radius:50%;background:#eceff1;border:2px solid #546e7a;display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:#546e7a;">
        <i class="fa fa-archive"></i>
      </div>
      <div style="font-weight:700;color:#1a237e;font-size:12px;">6. Close</div>
      <div style="color:#546e7a;font-size:10px;margin-top:2px;line-height:1.3;">Matter disposed,<br>archived or withdrawn</div>
    </div>

  </div>

  <!-- Status Flow Bar -->
  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #c5cae9;">
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:center;">
      <span style="font-size:11px;color:#5c6bc0;font-weight:700;margin-right:2px;">Status:</span>
      <span style="background:#e3f2fd;color:#1565c0;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">Intake Pending</span>
      <i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:10px;"></i>
      <span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">Active</span>
      <i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:10px;"></i>
      <span style="background:#fff3e0;color:#e65100;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">On Hold</span>
      <i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:10px;"></i>
      <span style="background:#eceff1;color:#455a64;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">Disposed</span>
      <span style="background:#eceff1;color:#455a64;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">Withdrawn</span>
      <span style="background:#eceff1;color:#455a64;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">Closed</span>
    </div>
  </div>

  <!-- Key Features -->
  <div style="margin-top:12px;display:flex;gap:16px;flex-wrap:wrap;justify-content:center;">
    <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#546e7a;">
      <i class="fa fa-clock-o" style="color:#ef5350;"></i>
      <span>Auto Timeline</span>
    </div>
    <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#546e7a;">
      <i class="fa fa-plug" style="color:#42a5f5;"></i>
      <span>eCourts Integration</span>
    </div>
    <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#546e7a;">
      <i class="fa fa-magic" style="color:#ab47bc;"></i>
      <span>AI Drafting</span>
    </div>
    <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#546e7a;">
      <i class="fa fa-bell" style="color:#ff9800;"></i>
      <span>Hearing Reminders</span>
    </div>
    <div style="display:flex;align-items:center;gap:4px;font-size:10px;color:#546e7a;">
      <i class="fa fa-shield" style="color:#66bb6a;"></i>
      <span>Matter-Level Permissions</span>
    </div>
  </div>
</div>"""


def execute():
    """Add workflow visualization block to the Chamber workspace."""
    print("Adding workflow visualization to Chamber workspace...")

    # Fetch the workspace
    ws = frappe.get_doc("Workspace", "Chamber")

    # Parse existing content
    content = json.loads(ws.content) if ws.content else []

    # Check if workflow block already exists
    has_workflow = any(
        b.get("type") == "custom_html"
        and "chamber-workflow" in (b.get("data", {}).get("html") or "")
        for b in content
    )
    if has_workflow:
        print("  Workflow block already exists — skipping.")
        return

    # Build the new block list: workflow first, then everything else
    workflow_block = {
        "id": "workflow_viz",
        "type": "custom_html",
        "data": {
            "html": WORKFLOW_HTML,
            "col": 12,
        },
    }

    new_content = [workflow_block] + content

    # Save
    ws.content = json.dumps(new_content, ensure_ascii=False)
    ws.save(ignore_permissions=True)
    frappe.db.commit()

    print("  DONE — workflow visualization added above shortcuts.")
    print("  Clear cache and refresh /app/chamber to see it.")
