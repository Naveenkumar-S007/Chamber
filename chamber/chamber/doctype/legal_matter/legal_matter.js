frappe.ui.form.on("Legal Matter", {
	setup(frm) {
		frm.set_query("matter_type", () => ({
			filters: { vertical: frm.doc.vertical },
		}));
		frm.set_query("client", () => ({
			filters: { is_client: 1 },
		}));
	},
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Open Intake Form"), () => {
				frappe.set_route("intake-form", { matter: frm.doc.name });
			});
			frm.add_custom_button(__("View Timeline"), () => {
				frappe.set_route("matter-timeline", { matter: frm.doc.name });
			});
			frm.add_custom_button(__("Generate Document"), () => {
				chamber.open_document_generator(frm.doc.name);
			});
			frm.add_custom_button(__("Sync eCourts"), () => {
				frappe.call({
					method: "chamber.chamber.doctype.legal_matter.legal_matter.sync_from_ecourts",
					args: { doc: frm.doc },
					callback: (r) => frm.refresh(),
				});
			});
			frm.add_custom_button(__("Log Custody Change"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Log Custody Change"),
					fields: [
						{
							fieldname: "custody_status",
							fieldtype: "Select",
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
							callback: () => {
								d.hide();
								frm.reload_doc();
							},
						});
					},
				});
				d.show();
			});
			frm.add_custom_button(__("Update Portal Status"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Record Portal Status (Manual)"),
					fields: [
						{ fieldname: "status", fieldtype: "Data", label: __("Status"), reqd: 1, placeholder: __("e.g. Objection pending / Admitted / Awaiting hearing") },
						{ fieldname: "status_date", fieldtype: "Date", label: __("Status Date") },
						{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
					],
					primary_action_label: __("Save"),
					primary_action(values) {
						frappe.call({
							method: "chamber.chamber.doctype.legal_matter.legal_matter.update_portal_status",
							args: { doc: frm.doc, status: values.status, status_date: values.status_date, notes: values.notes },
							callback: () => {
								d.hide();
								frm.reload_doc();
							},
						});
					},
				});
				d.show();
			});
			frm.add_custom_button(__("AI Bulk Upload"), () => {
				const d = new frappe.ui.Dialog({
					title: __("AI Bulk Read — Extract Case Fields"),
					fields: [
						{ fieldname: "file", fieldtype: "Attach", label: __("Case File (PDF / text / docx)"), reqd: 1 },
						{ fieldname: "field_hint", fieldtype: "Data", label: __("Expected Fields (optional)"), placeholder: "e.g. fir_number, sections_charged, bail_status" },
					],
					primary_action_label: __("Extract & Apply"),
					primary_action(values) {
						if (!values.file) {
							frappe.msgprint(__("Attach a file first."));
							return;
						}
						d.get_primary_btn().prop("disabled", true).text(__("Extracting…"));
						frappe.call({
							method: "chamber.api.ai.apply_extraction",
							args: {
								legal_matter: frm.doc.name,
								file_url: values.file,
								field_hint: values.field_hint,
							},
							callback: (r) => {
								d.get_primary_btn().prop("disabled", false).text(__("Extract & Apply"));
								const msg = r.message || {};
								const applied = (msg.applied || []).length ? msg.applied.join(", ") : __("none");
								const skipped = (msg.skipped || []).length ? msg.skipped.join(", ") : __("none");
								frappe.msgprint({
									title: __("Extraction complete"),
									message: __("Applied to matter: {0}<br>Skipped (no matching field): {1}", [applied, skipped]),
									indicator: "green",
								});
								frm.reload_doc();
							},
							error: () => d.get_primary_btn().prop("disabled", false).text(__("Extract & Apply")),
						});
					},
				});
				d.show();
			});
		}
	},
});

window.chamber = window.chamber || {};

chamber.open_document_generator = function (matter) {
	frappe.call({
		method: "chamber.api.documents.get_available_templates",
		args: { legal_matter: matter },
		callback: (r) => {
			const templates = r.message || [];
			if (!templates.length) {
				frappe.msgprint(__("No Document Templates available for this matter's vertical yet. Create one under Chamber > Document Template."));
				return;
			}
			const d = new frappe.ui.Dialog({
				title: __("Generate Document"),
				fields: [
					{
						fieldname: "document_template",
						fieldtype: "Select",
						label: __("Document Template"),
						options: templates.map((t) => ({ label: `${t.template_name} (${t.vertical || ""})`, value: t.name })),
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
