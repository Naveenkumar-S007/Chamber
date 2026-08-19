/* ──────────────────────────────────────────────────────────────────────
   Legal Matter – Chamber Workflow Guide

   6-step lifecycle:
     1. Intake          – matter created from portal intake
     2. Registered      – team reviewed, matter_type / vertical filled
     3. Active          – matter fully set up and being worked on
     4. Hearings & Docs – hearings scheduled, docs drafted
     5. eCourts Sync    – portal sync configured / running
     6. Closed          – disposed / settled / withdrawn

   Each step shows a visual progress bar + a contextual "Next Step"
   action button so the team follows the flow without confusion.
   ────────────────────────────────────────────────────────────────── */

const WORKFLOW_STEPS = [
	{ key: "Intake",          icon: "fa-file-text-o",  color: "#2563eb" },
	{ key: "Registered",      icon: "fa-clipboard",     color: "#d97706" },
	{ key: "Active",          icon: "fa-bolt",           color: "#16a34a" },
	{ key: "Hearings & Docs", icon: "fa-gavel",         color: "#7c3aed" },
	{ key: "eCourts Sync",    icon: "fa-cloud-download", color: "#0891b2" },
	{ key: "Closed",          icon: "fa-check-circle",  color: "#475569" },
];

/* Maps a workflow step to the NEXT step label shown on the button */
const NEXT_STEP_LABELS = {
	"Intake":          "Register Matter",
	"Registered":      "Activate Matter",
	"Active":          "Go to Hearings & Docs",
	"Hearings & Docs": "Configure eCourts Sync",
	"eCourts Sync":    "Close Matter",
};

/* ── Render the workflow progress bar inside the form ──────────────── */

function _render_workflow_bar(frm) {
	const current_step = frm.doc.workflow_step || "Intake";
	const current_idx = WORKFLOW_STEPS.findIndex((s) => s.key === current_step);

	/* Build the step pills */
	let steps_html = WORKFLOW_STEPS.map((s, i) => {
		const done = i < current_idx;
		const active = i === current_idx;
		const future = i > current_idx;

		let bg = "#e2e8f0";       // grey default (future)
		let fg = "#94a3b8";       // muted text
		let border = "transparent";
		let icon_color = "#94a3b8";

		if (done) {
			bg = "#dcfce7";
			fg = "#166534";
			border = "#16a34a";
			icon_color = "#16a34a";
		} else if (active) {
			bg = s.color;
			fg = "#fff";
			border = s.color;
			icon_color = "#fff";
		}

		const check = done ? '<i class="fa fa-check" style="margin-right:4px"></i>' : "";
		return `
			<div style="display:flex;flex-direction:column;align-items:center;flex:1;min-width:100px;max-width:160px;">
				<div style="width:40px;height:40px;border-radius:50%;background:${bg};border:2px solid ${border};
					display:flex;align-items:center;justify-content:center;margin-bottom:6px;
					${active ? "box-shadow:0 0 0 3px rgba(37,99,235,0.25);" : ""}">
					<i class="fa ${done ? "fa-check" : s.icon}" style="font-size:14px;color:${icon_color}"></i>
				</div>
				<span style="font-size:11px;font-weight:${active ? 700 : 500};color:${fg};text-align:center;
					line-height:1.2;${active ? "text-decoration:underline;text-underline-offset:2px;" : ""}">${s.key}</span>
			</div>`;
	}).join("");

	/* Arrows between steps */
	let arrow_html = WORKFLOW_STEPS.slice(0, -1)
		.map((_, i) => {
			const done = i < current_idx;
			return `<div style="flex:0 0 auto;width:28px;display:flex;align-items:center;justify-content:center;padding-top:0;margin-top:-18px;">
				<i class="fa fa-chevron-right" style="font-size:11px;color:${done ? "#16a34a" : "#cbd5e1"}"></i>
			</div>`;
		})
		.join("");

	/* Interleave steps and arrows */
	let flow_html = "";
	WORKFLOW_STEPS.forEach((_, i) => {
		flow_html += steps_html.split("</div></div>")[i] + "</div></div>";
		if (i < WORKFLOW_STEPS.length - 1) {
			flow_html += arrow_html.split("</div></div>")[i] + "</div></div>";
		}
	});

	/* Status badge */
	const status_colors = {
		"Intake Pending": "blue",
		Active: "green",
		"On Hold": "orange",
		Disposed: "grey",
		Withdrawn: "red",
		Closed: "grey",
	};
	const status_color = status_colors[frm.doc.status] || "blue";

	const bar_html = `
		<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px 24px;margin-bottom:16px;
			box-shadow:0 1px 3px rgba(0,0,0,0.04);">
			<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
				<span style="font-size:13px;font-weight:600;color:#0f172a;">
					<i class="fa fa-road" style="color:#2563eb;margin-right:6px"></i>
					Workflow Progress
				</span>
				<span class="indicator-pill whitespace-nowrap" style="font-size:12px;">
					<span class="indicator ${status_color}">${frm.doc.status}</span>
				</span>
			</div>
			<div style="display:flex;align-items:flex-start;">
				${flow_html}
			</div>
		</div>`;

	frm.dashboard.add_comment(bar_html, true);
}

/* ── Add "Next Step" action button ────────────────────────────────── */

function _add_workflow_action(frm) {
	const current_step = frm.doc.workflow_step || "Intake";
	const next_label = NEXT_STEP_LABELS[current_step];
	if (!next_label) return; /* already at "Closed" */

	const next_step = WORKFLOW_STEPS[WORKFLOW_STEPS.findIndex((s) => s.key === current_step) + 1].key;

	/* Step-specific sub-dialogs */
	const sub_dialogs = {
		"Register": _register_dialog,
		"Active": _activate_dialog,
		"Hearings & Docs": _hearing_dialog,
		"eCourts Sync": _ecourts_dialog,
		"Closed": _close_dialog,
	};

	const btn = frm.add_custom_button(
		__(next_label),
		() => {
			const dialog_fn = sub_dialogs[next_step];
			if (dialog_fn) {
				dialog_fn(frm, next_step);
			} else {
				_advance(frm, next_step);
			}
		},
		__("Workflow")
	);
	btn.addClass("btn-primary-dark");
	btn.find(".btn").css({
		"background": "#1e40af",
		color: "#fff",
		"border-color": "#1e40af",
		"font-weight": "600",
	});
}

/* ── Sub-dialogs for each step transition ──────────────────────────── */

function _register_dialog(frm, target) {
	const fields = [];
	if (!frm.doc.matter_type) {
		fields.push({
			fieldname: "matter_type",
			fieldtype: "Link",
			label: __("Matter Type"),
			options: "Matter Type",
			reqd: 1,
			filters: frm.doc.vertical ? { vertical: frm.doc.vertical } : {},
		});
	}
	if (!frm.doc.assigned_advocate) {
		fields.push({
			fieldname: "assigned_advocate",
			fieldtype: "Link",
			label: __("Assigned Advocate"),
			options: "User",
			reqd: 1,
		});
	}
	fields.push({
		fieldname: "priority",
		fieldtype: "Select",
		label: __("Priority"),
		options: "\nLow\nMedium\nHigh\nUrgent",
		default: frm.doc.priority || "Medium",
	});

	const d = new frappe.ui.Dialog({
		title: __("Register Matter — Fill Required Fields"),
		fields: fields,
		primary_action_label: __("Register & Continue"),
		primary_action(values) {
			const updates = {};
			if (values.matter_type) updates.matter_type = values.matter_type;
			if (values.assigned_advocate) updates.assigned_advocate = values.assigned_advocate;
			if (values.priority) updates.priority = values.priority;

			frm.save().then(() => {
				/* Apply any extra fields then advance */
				const promises = Object.entries(updates).map(([k, v]) =>
					frm.set_value(k, v)
				);
				frm.save().then(() => _advance(frm, target));
			});
			d.hide();
		},
	});
	d.show();
}

function _activate_dialog(frm, target) {
	const missing = [];
	if (!frm.doc.court) missing.push("Court");
	if (!frm.doc.filing_date) missing.push("Filing Date");
	if (!frm.doc.case_number) missing.push("Case Number");

	if (missing.length) {
		frappe.confirm(
			__("The following fields are empty: <b>{0}</b>. Do you want to proceed anyway?", [missing.join(", ")]),
			() => _advance(frm, target)
		);
	} else {
		_advance(frm, target);
	}
}

function _hearing_dialog(frm, target) {
	/* Open the Hearing creation form pre-filled with this matter */
	frappe.new_doc("Hearing", {
		legal_matter: frm.doc.name,
		hearing_date: frappe.datetime.add_days(frappe.datetime.get_today(), 7),
	});
	frappe.show_alert({
		message: __("Hearing form opened. After saving, come back here and click 'Configure eCourts Sync'."),
		indicator: "blue",
	});
}

function _ecourts_dialog(frm, target) {
	const fields = [
		{
			fieldname: "cnr_number",
			fieldtype: "Data",
			label: __("CNR Number"),
			default: frm.doc.cnr_number || "",
			placeholder: "e.g. KA01-000123-2024",
		},
		{
			fieldname: "ecourts_auto_sync",
			fieldtype: "Check",
			label: __("Enable Auto-Sync from eCourts"),
			default: frm.doc.ecourts_auto_sync || 0,
		},
		{
			fieldname: "portal",
			fieldtype: "Select",
			label: __("Portal"),
			options: "\neCourts\nIP India\nNCLT / NCLAT\nState RERA",
			default: frm.doc.portal || "eCourts",
		},
	];
	const d = new frappe.ui.Dialog({
		title: __("Configure eCourts / Portal Sync"),
		fields: fields,
		primary_action_label: __("Save & Continue"),
		primary_action(values) {
			if (values.cnr_number) frm.set_value("cnr_number", values.cnr_number);
			frm.set_value("ecourts_auto_sync", values.ecourts_auto_sync ? 1 : 0);
			if (values.portal) frm.set_value("portal", values.portal);
			frm.save().then(() => {
				d.hide();
				_advance(frm, target);
			});
		},
	});
	d.show();
}

function _close_dialog(frm, target) {
	const d = new frappe.ui.Dialog({
		title: __("Close Matter"),
		fields: [
			{
				fieldname: "close_status",
				fieldtype: "Select",
				label: __("Close As"),
				options: "\nDisposed\nWithdrawn\nClosed",
				reqd: 1,
				default: "Disposed",
			},
			{
				fieldname: "close_note",
				fieldtype: "Small Text",
				label: __("Closing Note"),
			},
		],
		primary_action_label: __("Close Matter"),
		primary_action(values) {
			frm.set_value("status", values.close_status);
			if (values.close_note) {
				frm.set_value("notes", (frm.doc.notes || "") + "\n\n[Close] " + values.close_note);
			}
			frm.save().then(() => {
				d.hide();
				_advance(frm, target);
			});
		},
	});
	d.show();
}

/* ── Core advance helper ───────────────────────────────────────────── */

function _advance(frm, target_step) {
	frappe.call({
		method: "advance_workflow",
		doc: frm.doc,
		args: { target_step: target_step },
		freeze: true,
		freeze_message: __("Advancing workflow to {0}…", [target_step]),
		callback() {
			frappe.show_alert({
				message: __("Workflow advanced to {0}", [target_step]),
				indicator: "green",
			});
			frm.reload_doc();
		},
	});
}

/* ──────────────────────────────────────────────────────────────────────
   Frappe form hooks
   ────────────────────────────────────────────────────────────────────── */

frappe.ui.form.on("Legal Matter", {
	setup(frm) {
		frm.set_query("matter_type", () => ({
			filters: { vertical: frm.doc.vertical },
		}));
		frm.set_query("client", () => ({
			filters: { is_client: 1 },
		}));
		frm.set_query("court", () => {
			if (frm.doc.routing_tier) {
				return { filters: { court_tier: frm.doc.routing_tier } };
			}
			if (frm.doc.matter_type && frm.doc.matter_type.includes("Domestic Violence")) {
				return { filters: { court_tier: "Magistrate Court" } };
			}
		});
	},

	vertical(frm) {
		frm.set_value("matter_type", null);
	},

	matter_type(frm) {
		if (frm.doc.matter_type && frm.doc.matter_type.includes("Domestic Violence")) {
			frappe.show_alert({
				message: __("DV (PWDVA) matters run through the Magistrate Court."),
				indicator: "orange",
			});
		}
	},

	refresh(frm) {
		if (frm.is_new()) return;

		/* ── Workflow progress bar ── */
		_render_workflow_bar(frm);

		/* ── Workflow action button ── */
		_add_workflow_action(frm);

		/* ── Secondary action buttons ── */
		const btn_group_secondary =__("Actions");

		frm.add_custom_button(__("View Timeline"), () => {
			frappe.set_route("matter-timeline", { matter: frm.doc.name });
		}, btn_group_secondary);

		frm.add_custom_button(__("Open Intake Form"), () => {
			frappe.set_route("intake-form", { matter: frm.doc.name });
		}, btn_group_secondary);

		frm.add_custom_button(__("Generate Document"), () => {
			chamber.open_document_generator(frm.doc.name);
		}, btn_group_secondary);

		frm.add_custom_button(__("Sync eCourts"), () => {
			frappe.call({
				method: "chamber.chamber.doctype.legal_matter.legal_matter.sync_from_ecourts",
				args: { doc: frm.doc },
				callback: () => frm.reload_doc(),
			});
		}, btn_group_secondary);

		frm.add_custom_button(__("Sync Extended (Orders/Cause List/Judgments)"), () => {
			frappe.call({
				method: "chamber.api.ecourts.sync_extended",
				args: { legal_matter: frm.doc.name },
				callback: (r) => {
					frappe.msgprint({
						title: __("Extended sync"),
						message: (r.message && r.message.message) || __("Done."),
						indicator: "green",
					});
					frm.reload_doc();
				},
			});
		}, btn_group_secondary);

		if (!frm.doc.is_archived) {
			frm.add_custom_button(__("Archive Matter"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Archive Matter"),
					fields: [{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason") }],
					primary_action_label: __("Archive"),
					primary_action(values) {
						frappe.call({
							method: "chamber.chamber.doctype.legal_matter.legal_matter.archive_matter",
							args: { name: frm.doc.name, reason: values.reason },
							callback: () => { d.hide(); frm.reload_doc(); },
						});
					},
				});
				d.show();
			}, btn_group_secondary);
		} else {
			frm.add_custom_button(__("Unarchive"), () => {
				frappe.call({
					method: "chamber.chamber.doctype.legal_matter.legal_matter.unarchive_matter",
					args: { name: frm.doc.name },
					callback: () => frm.reload_doc(),
				});
			}, btn_group_secondary);
		}

		frm.add_custom_button(__("Legal Hold"), () => {
			frappe.call({
				method: "chamber.chamber.doctype.legal_matter.legal_matter.set_legal_hold",
				args: { name: frm.doc.name, value: frm.doc.legal_hold ? 0 : 1 },
				callback: () => frm.reload_doc(),
			});
		}, btn_group_secondary);

		frm.add_custom_button(__("Log Custody Change"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Log Custody Change"),
				fields: [
					{
						fieldname: "custody_status", fieldtype: "Select",
						label: __("Custody Status"),
						options: "\nNot Arrested\nOn Bail\nJudicial Custody\nPolice Custody\nReleased",
						reqd: 1,
					},
					{ fieldname: "note", fieldtype: "Small Text", label: __("Note") },
				],
				primary_action_label: __("Log"),
				primary_action(values) {
					frappe.call({
						method: "chamber.chamber.doctype.legal_matter.legal_matter.log_custody_change",
						args: { doc: frm.doc, custody_status: values.custody_status, note: values.note },
						callback: () => { d.hide(); frm.reload_doc(); },
					});
				},
			});
			d.show();
		}, btn_group_secondary);

		frm.add_custom_button(__("Update Portal Status"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Record Portal Status (Manual)"),
				fields: [
					{ fieldname: "status", fieldtype: "Data", label: __("Status"), reqd: 1 },
					{ fieldname: "status_date", fieldtype: "Date", label: __("Status Date") },
					{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
				],
				primary_action_label: __("Save"),
				primary_action(values) {
					frappe.call({
						method: "chamber.chamber.doctype.legal_matter.legal_matter.update_portal_status",
						args: { doc: frm.doc, status: values.status, status_date: values.status_date, notes: values.notes },
						callback: () => { d.hide(); frm.reload_doc(); },
					});
				},
			});
			d.show();
		}, btn_group_secondary);

		frm.add_custom_button(__("AI Bulk Upload"), () => {
			const d = new frappe.ui.Dialog({
				title: __("AI Bulk Read — Extract Case Fields"),
				fields: [
					{ fieldname: "file", fieldtype: "Attach", label: __("Case File (PDF / text / docx)"), reqd: 1 },
					{ fieldname: "field_hint", fieldtype: "Data", label: __("Expected Fields (optional)"), placeholder: "e.g. fir_number, sections_charged, bail_status" },
				],
				primary_action_label: __("Extract & Apply"),
				primary_action(values) {
					if (!values.file) { frappe.msgprint(__("Attach a file first.")); return; }
					d.get_primary_btn().prop("disabled", true).text(__("Extracting…"));
					frappe.call({
						method: "chamber.api.ai.apply_extraction",
						args: { legal_matter: frm.doc.name, file_url: values.file, field_hint: values.field_hint },
						callback: (r) => {
							d.get_primary_btn().prop("disabled", false).text(__("Extract & Apply"));
							const msg = r.message || {};
							const applied = (msg.applied || []).length ? msg.applied.join(", ") : __("none");
							const skipped = (msg.skipped || []).length ? msg.skipped.join(", ") : __("none");
							frappe.msgprint({
								title: __("Extraction complete"),
								message: __("Applied to matter: {0}<br>Skipped: {1}", [applied, skipped]),
								indicator: "green",
							});
							frm.reload_doc();
						},
						error: () => d.get_primary_btn().prop("disabled", false).text(__("Extract & Apply")),
					});
				},
			});
			d.show();
		}, btn_group_secondary);
	},
});

/* ── Document Generator (shared helper) ────────────────────────────── */

window.chamber = window.chamber || {};

chamber.open_document_generator = function (matter) {
	frappe.call({
		method: "chamber.api.documents.get_available_templates",
		args: { legal_matter: matter },
		callback: (r) => {
			const templates = r.message || [];
			if (!templates.length) {
				frappe.msgprint(__("No Document Templates available for this matter's vertical yet."));
				return;
			}
			const d = new frappe.ui.Dialog({
				title: __("Generate Document"),
				fields: [
					{
						fieldname: "document_template",
						fieldtype: "Select",
						label: __("Document Template"),
						options: templates.map((t) => ({
							label: `${t.template_name} (${t.vertical || ""})`,
							value: t.name,
						})),
						reqd: 1,
					},
				],
				primary_action_label: __("Generate"),
				primary_action(values) {
					d.hide();
					frappe.call({
						method: "chamber.api.documents.render_document",
						args: { legal_matter: matter, document_template: values.document_template },
						callback: (res) => {
							if (res.message && res.message.name) {
								frappe.set_route("Form", "Generated Document", res.message.name);
							}
						},
					});
				},
			});
			d.show();
		},
	});
};
