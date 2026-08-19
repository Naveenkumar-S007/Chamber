/**
 * Chamber Workflow Visualization
 * Injects a clean workflow diagram at the top of the Chamber Dashboard page.
 */
frappe.ready(function () {
	// Only run on the Chamber Dashboard page
	if (
		frappe.get_route()[0] !== "app" ||
		frappe.get_route()[1] !== "chamber" ||
		!window.location.hash.includes("chamber-dashboard")
	) {
		return;
	}

	// Wait for the dashboard to render
	const check = setInterval(function () {
		const $body = $(`.page-body`);
		if ($body.length && $body.find(`.frappe-card`).length > 0) {
			clearInterval(check);
			inject_workflow($body);
		}
	}, 500);

	// Also try on hash change
	$(window).on("hashchange", function () {
		setTimeout(function () {
			if (window.location.hash.includes("chamber-dashboard")) {
				const $body = $(`.page-body`);
				if ($body.length && !$body.find(`.chamber-workflow-viz`).length) {
					inject_workflow($body);
				}
			}
		}, 1000);
	});
});

function inject_workflow($body) {
	// Don't inject twice
	if ($body.find(`.chamber-workflow-viz`).length) return;

	const html = `
	<div class="frappe-card p-4 mb-4 chamber-workflow-viz" style="border-left:4px solid #1a237e;">
		<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
			<i class="fa fa-sitemap" style="color:#1a237e;font-size:16px;"></i>
			<h5 style="margin:0;color:#1a237e;font-size:14px;">Case Workflow</h5>
			<span style="font-size:11px;color:#7986cb;">— from intake to closure</span>
		</div>
		<div style="display:flex;gap:0;align-items:stretch;" id="wf-steps"></div>
		<div style="margin-top:14px;padding-top:12px;border-top:1px solid #e8eaf6;display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:center;" id="wf-status"></div>
	</div>`;

	$body.prepend(html);

	// Render steps
	const steps = [
		{ icon: "fa-file-text-o", color: "#1565c0", bg: "#e3f2fd", border: "#1565c0", num: 1, title: "Intake", desc: "Client submits case" },
		{ icon: "fa-briefcase", color: "#f9a825", bg: "#fff8e1", border: "#f9a825", num: 2, title: "Registered", desc: "Matter created" },
		{ icon: "fa-check-circle", color: "#2e7d32", bg: "#e8f5e9", border: "#2e7d32", num: 3, title: "Active", desc: "Team activates" },
		{ icon: "fa-gavel", color: "#7b1fa2", bg: "#f3e5f5", border: "#7b1fa2", num: 4, title: "Hearings & Docs", desc: "Track & generate" },
		{ icon: "fa-refresh", color: "#00897b", bg: "#e0f2f1", border: "#00897b", num: 5, title: "eCourts Sync", desc: "Auto-sync status" },
		{ icon: "fa-archive", color: "#546e7a", bg: "#eceff1", border: "#546e7a", num: 6, title: "Close", desc: "Archived" },
	];

	const $steps = $("#wf-steps");
	steps.forEach(function (s, i) {
		$steps.append(
			`<div style="flex:1;text-align:center;padding:0 4px;">
				<div style="width:44px;height:44px;border-radius:50%;background:${s.bg};border:2px solid ${s.border};display:flex;align-items:center;justify-content:center;margin:0 auto 6px;font-size:17px;color:${s.color};">
					<i class="fa ${s.icon}"></i>
				</div>
				<div style="font-weight:700;color:#1a237e;font-size:11px;">${s.num}. ${s.title}</div>
				<div style="color:#78909c;font-size:10px;margin-top:2px;">${s.desc}</div>
			</div>`
		);
		if (i < steps.length - 1) {
			$steps.append(`<div style="display:flex;align-items:center;padding-top:8px;color:#c5cae9;font-size:14px;flex-shrink:0;"><i class="fa fa-chevron-right"></i></div>`);
		}
	});

	// Render status flow
	const $sf = $("#wf-status");
	$sf.append(`<span style="font-size:11px;color:#5c6bc0;font-weight:700;">Status:</span>`);
	[
		{ l: "Intake Pending", c: "#1565c0", bg: "#e3f2fd" },
		{ l: "Active", c: "#2e7d32", bg: "#e8f5e9" },
		{ l: "On Hold", c: "#e65100", bg: "#fff3e0" },
		{ l: "Disposed", c: "#455a64", bg: "#eceff1" },
		{ l: "Withdrawn", c: "#455a64", bg: "#eceff1" },
		{ l: "Closed", c: "#455a64", bg: "#eceff1" },
	].forEach(function (s, i) {
		$sf.append(`<span style="background:${s.bg};color:${s.c};padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;">${s.l}</span>`);
		if (i < 2) $sf.append(`<i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:9px;"></i>`);
	});
}
