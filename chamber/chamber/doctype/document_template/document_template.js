frappe.ui.form.on("Document Template", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Re-scan Merge Tags"), () => {
				frm.save();
			});
			frm.add_custom_button(__("Import from File"), () => {
				if (!frm.doc.source_file) {
					frappe.msgprint(__("Upload a template file (.docx / .txt / .md / .pdf) in the 'Self-Serve Import' section first."));
					return;
				}
				frappe.call({
					method: "chamber.chamber.doctype.document_template.document_template.import_from_file",
					args: { doc: frm.doc },
					callback: (r) => {
						frappe.msgprint({
							title: __("Template imported"),
							message: __("Body and merge tags extracted. Review the template body and map tags in the Merge Tags table."),
							indicator: "green",
						});
						frm.refresh();
					},
				});
			});
		}
	},
});
