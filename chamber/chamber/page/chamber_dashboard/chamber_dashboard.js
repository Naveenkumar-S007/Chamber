frappe.pages["chamber-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Chamber Dashboard"),
		single_column: true,
	});
	wrapper.chamber_dashboard = new ChamberDashboard(page);
};

class ChamberDashboard {
	constructor(page) {
		this.page = page;
		this.page.set_title(__("Chamber Dashboard"));
		this.page.add_inner_button(__("Refresh"), () => this.load());
		this.load();
	}

	load() {
		const me = this;
		frappe.call({
			method: "chamber.api.dashboard.get_stats",
			callback: (r) => me.render(r.message || {}),
		});
	}

	render(stats) {
		const me = this;
		const $body = $(this.page.body).empty();
		const h = stats.headline || {};
		const fmt = (v) =>
			frappe.format(v || 0, { fieldtype: "Currency", options: "INR" });

		const cards = [
			{ label: __("Active Matters"), value: h.active_matters },
			{ label: __("Total Matters"), value: h.total_matters },
			{ label: __("Hearings (next 30 days)"), value: h.upcoming_hearings },
			{ label: __("Court Fees Paid (INR)"), value: fmt(h.court_fees_paid) },
			{ label: __("Pending Signatures"), value: h.pending_signatures },
			{ label: __("Active Caveats"), value: h.caveats_active },
			{ label: __("Overdue / Flagged Deadlines"), value: h.overdue_deadlines },
		];
		const cardHtml = cards
			.map(
				(c) => `
				<div class="col-sm-6 col-md-3">
					<div class="frappe-card p-3 mb-3">
						<h3 class="mb-1">${c.value == null ? "0" : c.value}</h3>
						<div class="text-muted small">${c.label}</div>
					</div>
				</div>`
			)
			.join("");

		$body.append(`
			<div class="row">${cardHtml}</div>
			<div class="row">
				<div class="col-md-6">
					<div class="frappe-card p-3 mb-3">
						<h6>${__("Matters by Vertical")}</h6>
						<div class="chart-container" id="chart-vertical" style="height: 240px;"></div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="frappe-card p-3 mb-3">
						<h6>${__("Matters by Status")}</h6>
						<div class="chart-container" id="chart-status" style="height: 240px;"></div>
					</div>
				</div>
			</div>
			<div class="row">
				<div class="col-md-12">
					<div class="frappe-card p-3">
						<h6>${__("Hearings in the Next 30 Days")}</h6>
						<div class="chart-container" id="chart-hearings" style="height: 240px;"></div>
					</div>
				</div>
			</div>`);

		const colors = [
			"#5b8ff9", "#5ad8a6", "#f6bd16", "#e8684a", "#6dc8ec",
			"#9270ca", "#ff9d4d", "#269a99", "#ff99c3", "#7d9b3a",
		];
		me.chart("chart-vertical", stats.by_vertical, "bar", colors);
		me.chart("chart-status", stats.by_status, "pie", colors);
		me.chart("chart-hearings", stats.hearings, "line", colors);
	}

	chart(id, rows, type, colors) {
		const el = $(this.page.body).find("#" + id)[0];
		if (!el) return;
		if (!rows || !rows.length) {
			$(el).html(`<p class="text-muted small">${__("No data yet")}</p>`);
			return;
		}
		const data = {
			labels: rows.map((r) => r.label),
			datasets: [{ values: rows.map((r) => r.value) }],
		};
		if (typeof frappe.Chart === "function") {
			new frappe.Chart(el, { data, type, height: 220, colors });
		} else {
			$(el).html("<p>" + JSON.stringify(data) + "</p>");
		}
	}
}
