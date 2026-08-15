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
