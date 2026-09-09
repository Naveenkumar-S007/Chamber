/* Chamber — Intake Form Page Controller
 * Loaded globally via app_include_js (asset-pipeline, cache-busted).
 * The page script at chamber/chamber/page/intake_form/intake_form.js
 * just instantiates this class.
 */
frappe.provide("chamber.intake_form");

chamber.intake_form.IntakeFormPage = class IntakeFormPage {
	constructor(page) {
		this.page = page;
		this.matter = frappe.utils.get_url_arg("matter") || "";
		this.template = frappe.utils.get_url_arg("template") || "";
		this.setup_controls();
		this.load();
	}

	setup_controls() {
		const me = this;
		this.page.set_title("Conditional Intake Form");

		this.page.add_inner_button("Back to Matters", function () {
			frappe.set_route("List", "Legal Matter");
		});

		this.page.add_inner_button("Reload", function () {
			me.load();
		});

		this.page.add_inner_button("Open Matter", function () {
			const v = me.get_matter_value();
			if (v) {
				frappe.set_route("Form", "Legal Matter", v);
			}
		});
	}

	get_matter_value() {
		if (this.page.fields_dict && this.page.fields_dict.matter) {
			return this.page.fields_dict.matter.value;
		}
		return this.matter || "";
	}

	load() {
		const me = this;
		const matter = this.get_matter_value();

		if (!matter) {
			me.render_matter_picker();
			return;
		}

		// Fetch the intake form template
		frappe.call({
			method: "chamber.api.intake.get_form",
			args: {
				template: me.template || undefined,
				legal_matter: matter,
			},
			callback: function (r) {
				if (!r.message) {
					frappe.msgprint({
						title: __("No template found"),
						message: __("No published Intake Form Template is available. Create one in Setup > Intake Form Template."),
						indicator: "orange",
					});
					me.render_matter_picker();
					return;
				}
				me.form = r.message;
				me.render_form(matter);
			},
			error: function (err) {
				me.render_matter_picker(
					__("Could not load intake form: {0}", [err.message || "Unknown error"])
				);
			},
		});
	}

	render_matter_picker(error_msg) {
		const me = this;
		const $body = $(this.page.body).empty();
		$body.css("padding", "10px 0");

		if (error_msg) {
			$body.append(
				'<div class="alert alert-danger">' + frappe.utils.escape_html(error_msg) + "</div>"
			);
		}

		// Instructions card
		const $card = $('<div class="frappe-card p-4" style="max-width: 900px;"></div>').appendTo($body);
		$card.append(
			'<p class="text-muted">' +
				__("Select a Legal Matter below to begin intake, or use the Link field in the toolbar above.") +
				"</p>"
		);

		// Fetch matters
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Legal Matter",
				filters: { is_archived: 0 },
				fields: ["name", "matter_title", "status", "vertical", "workflow_step"],
				order_by: "modified desc",
				limit_page_length: 50,
			},
			callback: function (r) {
				if (!r.message || !r.message.length) {
					$card.append(
						'<div class="text-muted" style="margin-top:1rem;">' +
							"<p>" + __("No Legal Matters found.") + "</p>" +
							'<a class="btn btn-primary btn-sm" href="/app/legal-matter/new">' +
								__("Create New Matter") +
							"</a>" +
						"</div>"
					);
					return;
				}

				let html =
					'<h5 style="margin-top:1rem;">' + __("All Legal Matters") + "</h5>" +
					'<table class="table table-hover">' +
					"<thead><tr>" +
					"<th>" + __("ID") + "</th>" +
					"<th>" + __("Title") + "</th>" +
					"<th>" + __("Status") + "</th>" +
					"<th>" + __("Vertical") + "</th>" +
					"<th>" + __("Workflow") + "</th>" +
					"<th></th>" +
					"</tr></thead><tbody>";

				r.message.forEach(function (m) {
					const status_color =
						m.status === "Intake Pending"
							? "orange"
							: m.status === "Active"
							? "green"
							: "grey";
					html +=
						"<tr>" +
						"<td>" + frappe.utils.escape_html(m.name) + "</td>" +
						"<td>" + frappe.utils.escape_html(m.matter_title || "") + "</td>" +
						'<td><span class="indicator-pill ' + status_color + '">' +
							frappe.utils.escape_html(m.status || "") + "</span></td>" +
						"<td>" + frappe.utils.escape_html(m.vertical || "") + "</td>" +
						"<td>" + frappe.utils.escape_html(m.workflow_step || "") + "</td>" +
						'<td><button class="btn btn-xs btn-primary pick-matter" data-name="' +
							frappe.utils.escape_html(m.name) +
							'">' + __("Select") + "</button></td>" +
						"</tr>";
				});

				html += "</tbody></table>";
				$card.append(html);

				// Bind Select buttons
				$card.find(".pick-matter").on("click", function () {
					const name = $(this).data("name");
					me.matter = name;
					me.load();
				});
			},
			error: function () {
				$card.append(
					'<p class="text-muted" style="margin-top:1rem;">' +
						__("Could not load matters. Select one from the Link field above and click Reload.") +
					"</p>"
				);
			},
		});
	}

	render_form(matter) {
		const me = this;
		const $body = $(this.page.body).empty();
		$body.css("padding", "10px 0");

		// Matter info bar
		const $info = $(
			'<div class="frappe-card p-3 mb-3" style="max-width: 900px;">' +
				'<div class="row">' +
				'<div class="col-md-8">' +
					"<strong>" + __("Matter:") + "</strong> " + frappe.utils.escape_html(matter) +
					" &mdash; " + frappe.utils.escape_html(me.form.matter_title || "") +
				"</div>" +
				'<div class="col-md-4 text-right">' +
					'<button class="btn btn-default btn-xs change-matter">' +
						__("Change Matter") +
					"</button>" +
					'<button class="btn btn-default btn-xs open-matter">' +
						__("Open Matter") +
					"</button>" +
				"</div>" +
				"</div>" +
			"</div>"
		).appendTo($body);
		$info.find(".change-matter").on("click", function () {
			me.matter = "";
			me.render_matter_picker();
		});
		$info.find(".open-matter").on("click", function () {
			frappe.set_route("Form", "Legal Matter", matter);
		});

		// Template info
		const $card = $('<div class="frappe-card p-4" style="max-width: 900px;"></div>').appendTo($body);

		$card.append(
			'<h4>' + frappe.utils.escape_html(me.form.template_name || "Intake Form") + "</h4>"
		);

		if (me.form.description) {
			$card.append(
				'<p class="text-muted">' + frappe.utils.escape_html(me.form.description) + "</p>"
			);
		}

		// Render the intake form fields
		if (typeof chamber !== "undefined" && chamber.intake && chamber.intake.render) {
			chamber.intake.render({
				fields: me.form.fields || [],
				container: $card,
				onSubmit: function (values, $btn) {
					$btn.prop("disabled", true).text(__("Saving..."));
					frappe.call({
						method: "chamber.api.intake.submit",
						args: {
							legal_matter: matter,
							intake_form_template: me.form.name,
							responses: values,
						},
						callback: function (r) {
							$btn.prop("disabled", false).text(__("Submit Intake"));
							if (r.message) {
								frappe.msgprint({
									title: __("Intake submitted"),
									message: __("Responses saved and applied to the matter."),
									indicator: "green",
								});
								frappe.set_route("Form", "Legal Matter", matter);
							}
						},
						error: function () {
							$btn.prop("disabled", false).text(__("Submit Intake"));
						},
					});
				},
			});
		} else {
			// Fallback: render a basic form if the intake renderer isn't loaded
			$card.append(
				'<div class="alert alert-warning">' +
					__("Intake form renderer not loaded. Please refresh the page.") +
				"</div>"
			);
		}
	}
};
