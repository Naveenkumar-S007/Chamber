frappe.pages["deadline-tracker"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Deadline Tracker",
		single_column: true,
	});
	wrapper.deadline_tracker = new DeadlineTracker(page);
};

class DeadlineTracker {
	constructor(page) {
		this.page = page;
		this.setup_controls();
		this.load();
	}

	setup_controls() {
		const me = this;
		this.page.set_title("Deadline Tracker");
		this.page.add_field({
			fieldname: "vertical",
			fieldtype: "Link",
			options: "Legal Vertical",
			label: "Vertical",
		});
		this.page.add_field({
			fieldname: "deadline_type",
			fieldtype: "Select",
			label: "Type",
			options: "\nStatutory\nLimitation\nIP Renewal\nCaveat",
		});
		this.page.add_field({
			fieldname: "horizon_days",
			fieldtype: "Int",
			label: "Horizon (days)",
			default: 90,
		});
		this.page.add_inner_button("Refresh", () => this.load());
	}

	load() {
		const me = this;
		frappe.call({
			method: "chamber.api.deadlines.get_upcoming",
			args: {
				vertical: this.page.fields_dict.vertical.value || undefined,
				deadline_type: this.page.fields_dict.deadline_type.value || undefined,
				horizon_days: this.page.fields_dict.horizon_days.value || 90,
			},
			callback: (r) => {
				if (r.message) me.render(r.message);
			},
		});
	}

	render(data) {
		const $body = $(this.page.body).empty();
		const counts = data.counts || {};
		$body.append(`
			<div class="d-flex mb-3" style="gap: 8px;">
				<span class="label label-default">Statutory: ${counts.Statutory || 0}</span>
				<span class="label label-orange">Limitation: ${counts.Limitation || 0}</span>
				<span class="label label-purple">IP Renewal: ${counts["IP Renewal"] || 0}</span>
				<span class="label label-blue">Caveat: ${counts.Caveat || 0}</span>
			</div>`);

		const deadlines = data.deadlines || [];
		if (!deadlines.length) {
			$body.append(`<div class="frappe-card p-4 text-muted">No upcoming deadlines in this horizon.</div>`);
			return;
		}

		const badge = { expired: "danger", critical: "warning", warning: "orange", ok: "green" };
		const rows = deadlines
			.map(
				(d) => {
					const days =
						d.days_left < 0
							? `Expired ${Math.abs(d.days_left)}d ago`
							: d.days_left === 0
							? "Due today"
							: `${d.days_left}d left`;
					return `
					<tr class="clickable-row" data-matter="${frappe.utils.escape_html(d.matter)}">
						<td><span class="label label-${badge[d.band_status] || "grey"}">${days}</span></td>
						<td>${frappe.utils.escape_html(d.label)}</td>
						<td>${frappe.utils.escape_html(d.deadline_type)}</td>
						<td><strong>${frappe.utils.escape_html(d.matter_title)}</strong></td>
						<td>${frappe.utils.escape_html(d.vertical || "")}</td>
						<td>${frappe.utils.escape_html(d.date)}</td>
						<td>${frappe.utils.escape_html(d.court || "")} ${d.cnr_number ? "• " + frappe.utils.escape_html(d.cnr_number) : ""}</td>
					</tr>`;
				}
			)
			.join("");

		$body.append(`
			<div class="frappe-card p-4">
				<table class="table table-hover table-sm">
					<thead><tr><th>Countdown</th><th>Deadline</th><th>Type</th><th>Matter</th><th>Vertical</th><th>Due Date</th><th>Court / CNR</th></tr></thead>
					<tbody>${rows}</tbody>
				</table>
			</div>`);
		$body.find(".clickable-row").on("click", function () {
			frappe.set_route("Form", "Legal Matter", $(this).data("matter"));
		});
	}
}
