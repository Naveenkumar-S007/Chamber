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

		// ── Workflow Visualization ──
		const $wf = $(`<div class="frappe-card p-4 mb-4" style="border-left:4px solid #1a237e;"></div>`).appendTo($body);
		$wf.append(`<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;"><i class="fa fa-sitemap" style="color:#1a237e;font-size:16px;"></i><h5 style="margin:0;color:#1a237e;font-size:14px;">Case Workflow</h5><span style="font-size:11px;color:#7986cb;">— from intake to closure</span></div>`);

		const steps = [
			{icon:"fa-file-text-o",color:"#1565c0",bg:"#e3f2fd",border:"#1565c0",num:1,title:"Intake",desc:"Client submits case"},
			{icon:"fa-briefcase",color:"#f9a825",bg:"#fff8e1",border:"#f9a825",num:2,title:"Registered",desc:"Matter created"},
			{icon:"fa-check-circle",color:"#2e7d32",bg:"#e8f5e9",border:"#2e7d32",num:3,title:"Active",desc:"Team activates"},
			{icon:"fa-gavel",color:"#7b1fa2",bg:"#f3e5f5",border:"#7b1fa2",num:4,title:"Hearings & Docs",desc:"Track & generate"},
			{icon:"fa-refresh",color:"#00897b",bg:"#e0f2f1",border:"#00897b",num:5,title:"eCourts Sync",desc:"Auto-sync status"},
			{icon:"fa-archive",color:"#546e7a",bg:"#eceff1",border:"#546e7a",num:6,title:"Close",desc:"Archived"},
		];
		const $steps = $(`<div style="display:flex;gap:0;align-items:stretch;"></div>`).appendTo($wf);
		steps.forEach((s,i) => {
			$(`<div style="flex:1;text-align:center;padding:0 4px;"><div style="width:44px;height:44px;border-radius:50%;background:${s.bg};border:2px solid ${s.border};display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:${s.color};"><i class="fa ${s.icon}"></i></div><div style="font-weight:700;color:#1a237e;font-size:11px;">${s.num}. ${s.title}</div><div style="color:#78909c;font-size:10px;margin-top:2px;">${s.desc}</div></div>`).appendTo($steps);
			if(i<steps.length-1) $(`<div style="display:flex;align-items:center;padding-top:8px;color:#c5cae9;font-size:14px;flex-shrink:0;"><i class="fa fa-chevron-right"></i></div>`).appendTo($steps);
		});

		// Status flow
		const $sf = $(`<div style="margin-top:14px;padding-top:12px;border-top:1px solid #e8eaf6;display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:center;"></div>`).appendTo($wf);
		$(`<span style="font-size:11px;color:#5c6bc0;font-weight:700;">Status:</span>`).appendTo($sf);
		[{l:"Intake Pending",c:"#1565c0",bg:"#e3f2fd"},{l:"Active",c:"#2e7d32",bg:"#e8f5e9"},{l:"On Hold",c:"#e65100",bg:"#fff3e0"},{l:"Disposed",c:"#455a64",bg:"#eceff1"},{l:"Withdrawn",c:"#455a64",bg:"#eceff1"},{l:"Closed",c:"#455a64",bg:"#eceff1"}].forEach((s,i) => {
			$(`<span style="background:${s.bg};color:${s.c};padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">${s.l}</span>`).appendTo($sf);
			if(i<2) $(`<i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:9px;"></i>`).appendTo($sf);
		});

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
