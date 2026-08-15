const WORKFLOW_NEXT = {
	"": "Draft",
	"Draft": "Internal Review",
	"Internal Review": "Client Review",
	"Client Review": "Finalized",
	"Finalized": "Executed",
	"Executed": null,
};

frappe.ui.form.on("Generated Document", {
	refresh(frm) {
		if (frm.doc.legal_matter && !frm.is_new()) {
			frm.add_custom_button(__("Open Matter"), () => {
				frappe.set_route("Form", "Legal Matter", frm.doc.legal_matter);
			});
			frm.add_custom_button(__("Download PDF"), () => {
				frappe.call({
					method: "chamber.api.documents.generate_pdf",
					args: { name: frm.doc.name },
					callback: (r) => {
						if (r.message && r.message.file_url) {
							window.open(r.message.file_url, "_blank");
						}
					},
				});
			});
		}
		// ---- approval workflow controls
		if (!frm.is_new()) {
			const next = WORKFLOW_NEXT[frm.doc.workflow_state || ""];
			if (next) {
				frm.add_custom_button(__("Workflow → " + next), () => {
					frappe.call({
						method: "advance_workflow",
						doc: frm.doc,
						args: { target: next },
						callback: () => frm.reload_doc(),
					});
				});
			}
			frm.add_custom_button(__("Suggest Clauses"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Suggested Clauses from Library"),
					fields: [
						{
							fieldname: "clauses",
							fieldtype: "Table",
							label: __("Clauses"),
							cannot_add_rows: true,
							cannot_delete_rows: false,
							data: [],
							fields: [
								{ fieldname: "name", fieldtype: "Data", label: __("Clause") },
								{ fieldname: "clause_text", fieldtype: "Text", label: __("Text") },
							],
						},
					],
					primary_action_label: __("Copy selected into content"),
					primary_action(values) {
						const selected = (values.clauses || []).filter((r) => r.name && r.__checked);
						if (selected.length) {
							const content = frm.doc.content || "";
							const append = selected.map((c) => `<p>${c.clause_text}</p>`).join("\n");
							frm.set_value("content", content + (content ? "\n" : "") + append);
						}
						d.hide();
					},
				});
				d.fields_dict.clauses.df.data = [];
				frappe.call({
					method: "suggest_clauses",
					doc: frm.doc,
					callback: (r) => {
						const rows = (r.message || []).map((c) => ({
							name: c.name,
							clause_text: c.clause_text,
							__checked: 0,
						}));
						d.fields_dict.clauses.df.data = rows;
						d.fields_dict.clauses.grid.refresh();
					},
				});
				d.show();
			});
		}
		if (!["Approved", "Sent", "Signed"].includes(frm.doc.status) && !frm.is_new()) {
			frm.add_custom_button(__("Send for Review"), () => {
				frappe.call({
					method: "chamber.api.documents.send_for_review",
					args: { name: frm.doc.name },
					callback: () => frm.reload_doc(),
				});
			});
		}
		if (["Approved", "Ready for Review"].includes(frm.doc.status) && !frm.is_new()) {
			frm.add_custom_button(__("Send for Signature"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Send for Signature"),
					fields: [
						{ fieldname: "signer_name", fieldtype: "Data", label: __("Signer Name"), reqd: 1 },
						{ fieldname: "signer_email", fieldtype: "Data", label: __("Signer Email"), options: "Email", reqd: 1 },
						{
							fieldname: "provider",
							fieldtype: "Select",
							label: __("Provider"),
							options: "\nDocuSign\nDropbox Sign\nSignDesk\neMudhra\nGeneric REST\nManual",
						},
					],
					primary_action_label: __("Send"),
					primary_action(values) {
						d.hide();
						frappe.call({
							method: "chamber.api.esign.send_for_signature",
							args: {
								legal_matter: frm.doc.legal_matter,
								generated_document: frm.doc.name,
								signer_name: values.signer_name,
								signer_email: values.signer_email,
								provider: values.provider,
							},
							callback: (r) => {
								if (r.message && r.message.signing_url) {
									frappe.msgprint({
										title: __("Sent for signature"),
										message: __("Signing link issued. Share it with the signer."),
										indicator: "green",
									});
								}
								frm.reload_doc();
							},
						});
					},
				});
				d.show();
			});
		}
	},
});
