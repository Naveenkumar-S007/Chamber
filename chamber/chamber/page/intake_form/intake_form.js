frappe.pages["intake-form"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Conditional Intake Form",
		single_column: true,
	});
	wrapper.intake = new IntakeForm(page);
};

class IntakeForm {
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
		this.page.add_inner_message(
			`<a class="btn btn-default btn-sm" href="/app/legal-matter">← Back to Matters</a>`
		);

		this.page.add_field({
			fieldname: "matter",
			fieldtype: "Link",
			options: "Legal Matter",
			label: "Legal Matter",
			reqd: 1,
			default: this.matter,
		});
		this.page.add_field({
			fieldname: "intake_form_template",
			fieldtype: "Link",
			options: "Intake Form Template",
			label: "Intake Form Template",
			default: this.template,
		});
		this.page.add_inner_button("Reload", () => this.load());
		this.page.add_inner_button("Open Matter", () => {
			if (this.page.fields_dict.matter.value) {
				frappe.set_route("Form", "Legal Matter", this.page.fields_dict.matter.value);
			}
		});
	}

	load() {
		const me = this;
		const matter = this.page.fields_dict.matter.value;
		if (!matter) {
			$(this.page.body).html(
				`<div class="alert alert-warning">Select a Legal Matter to begin intake.</div>`
			);
			return;
		}
		frappe.call({
			method: "chamber.api.intake.get_form",
			args: { template: this.page.fields_dict.intake_form_template.value || undefined },
			callback: (r) => {
				if (!r.message) return;
				me.form = r.message;
				me.render(matter);
			},
		});
	}

	render(matter) {
		const me = this;
		this.page.set_title(this.form.template_name);
		this.page.add_inner_message(
			`<span class="text-muted">${this.form.vertical || ""} ${this.form.matter_type ? "• " + this.form.matter_type : ""}</span>`
		);
		const $body = $(this.page.body).empty();
		const $card = $(`<div class="frappe-card p-4" style="max-width: 860px;"></div>`).appendTo($body);

		if (this.form.description) {
			$card.append(`<p class="text-muted">${frappe.utils.escape_html(this.form.description)}</p>`);
		}

		chamber.intake.render({
			fields: this.form.fields,
			container: $card,
			onSubmit(values, $btn) {
				$btn.prop("disabled", true).text("Saving…");
				frappe.call({
					method: "chamber.api.intake.submit",
					args: {
						legal_matter: matter,
						intake_form_template: me.form.name,
						responses: values,
					},
					callback: (r) => {
						$btn.prop("disabled", false).text("Submit Intake");
						if (r.message) {
							frappe.msgprint({
								title: __("Intake submitted"),
								message: __("Responses saved and applied to the matter."),
								indicator: "green",
							});
							frappe.set_route("Form", "Legal Matter", matter);
						}
					},
					error: () => {
						$btn.prop("disabled", false).text("Submit Intake");
					},
				});
			},
		});
	}
}
