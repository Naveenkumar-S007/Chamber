frappe.pages["matter-timeline"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Matter Timeline",
		single_column: true,
	});
	wrapper.timeline = new MatterTimeline(page);
};

class MatterTimeline {
	constructor(page) {
		this.page = page;
		this.matter = frappe.utils.get_url_arg("matter") || "";
		this.setup_controls();
		this.load();
	}

	setup_controls() {
		const me = this;
		this.page.set_title("Matter Timeline");
		this.page.add_field({
			fieldname: "matter",
			fieldtype: "Link",
			options: "Legal Matter",
			label: "Legal Matter",
			reqd: 1,
			default: this.matter,
		});
		this.page.add_inner_button("Reload", () => this.load());
		this.page.add_inner_button("Open Matter", () => {
			if (this.page.fields_dict.matter.value) {
				frappe.set_route("Form", "Legal Matter", this.page.fields_dict.matter.value);
			}
		});
		this.page.add_inner_button("Add Event", () => this.add_event_dialog());
	}

	load() {
		const me = this;
		const matter = this.page.fields_dict.matter.value;
		if (!matter) {
			$(this.page.body).html(`<div class="alert alert-warning">Select a Legal Matter to view its timeline.</div>`);
			return;
		}
		frappe.call({
			method: "chamber.api.timeline.get",
			args: { legal_matter: matter },
			callback: (r) => {
				if (r.message) {
					me.render(r.message);
				}
			},
		});
	}

	render(data) {
		this.page.set_title(`${data.matter_title || data.matter}`);
		this.page.add_inner_message(
			`<span class="text-muted">${data.vertical || ""} ${data.matter_type ? "• " + data.matter_type : ""}</span>`
		);
		const $body = $(this.page.body).empty();
		const $card = $(`<div class="frappe-card p-4"></div>`).appendTo($body);
		chamber.timeline.render({ container: $card, data });
	}

	add_event_dialog() {
		const me = this;
		const d = new frappe.ui.Dialog({
			title: __("Add Timeline Event"),
			fields: [
				{ fieldname: "entry_date", fieldtype: "Date", label: "Date", reqd: 1 },
				{
					fieldname: "event_type",
					fieldtype: "Select",
					label: "Event Type",
					options: "\nMilestone\nFiling\nHearing\nNotice\nOrder\nDocument\nTask\nCustody Change\nOther",
					reqd: 1,
				},
				{ fieldname: "title", fieldtype: "Data", label: "Title", reqd: 1 },
				{ fieldname: "milestone", fieldtype: "Data", label: "Milestone" },
				{ fieldname: "description", fieldtype: "Small Text", label: "Description" },
			],
			primary_action_label: __("Add"),
			primary_action(values) {
				frappe.call({
					method: "chamber.api.timeline.add_entry",
					args: Object.assign({ legal_matter: me.page.fields_dict.matter.value }, values),
					callback: () => {
						d.hide();
						me.load();
					},
				});
			},
		});
		d.show();
	}
}
