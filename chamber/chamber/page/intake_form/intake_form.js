/* Intake Form Page — thin wrapper
 * The IntakeFormPage class lives in public/js/intake_form_page.js
 * (loaded via app_include_js so it goes through the asset pipeline
 * and gets cache-busted automatically).
 */
frappe.pages["intake-form"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Conditional Intake Form",
		single_column: true,
	});

	if (chamber && chamber.intake_form && chamber.intake_form.IntakeFormPage) {
		wrapper.intake = new chamber.intake_form.IntakeFormPage(page);
	} else {
		$(page.body).html(
			'<div class="alert alert-warning">Intake form module not loaded. Please run: bench build && bench restart, then hard-refresh (Ctrl+Shift+R).</div>'
		);
	}
};
