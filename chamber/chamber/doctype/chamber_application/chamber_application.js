frappe.ui.form.on("Chamber Application", {
	refresh(frm) {
		if (frm.doc.matter) {
			frm.add_custom_button(__("Open Matter"), () => {
				frappe.set_route("Form", "Legal Matter", frm.doc.matter);
			});
		}
		frm.add_custom_button(__("View Matter Timeline"), () => {
			frappe.set_route("matter-timeline", { matter: frm.doc.matter });
		});
	},
});
