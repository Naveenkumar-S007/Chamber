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
