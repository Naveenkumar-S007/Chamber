frappe.pages["workflow-view"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Case Workflow"),
		single_column: true,
	});
	new CaseWorkflow(page);
};

class CaseWorkflow {
	constructor(page) {
		this.page = page;
		this.render();
	}

	render() {
		const $body = $(this.page.body).empty();

		// ── Main Workflow Card ──
		const $card = $(`<div class="frappe-card p-4 mb-4"></div>`).appendTo($body);

		$card.append(`
			<div style="display:flex;align-items:center;gap:8px;margin-bottom:20px;">
				<i class="fa fa-sitemap" style="color:#1a237e;font-size:18px;"></i>
				<h4 style="margin:0;color:#1a237e;">How a Case Moves Through Your Chamber</h4>
			</div>
		`);

		// ── Steps ──
		const steps = [
			{
				num: 1,
				icon: "fa-file-text-o",
				color: "#1565c0",
				bg: "#e3f2fd",
				border: "#1565c0",
				title: "Intake",
				desc: "Client submits case via portal or desk form",
				detail: "Legal Party + Legal Matter created, status: Intake Pending",
			},
			{
				num: 2,
				icon: "fa-briefcase",
				color: "#f9a825",
				bg: "#fff8e1",
				border: "#f9a825",
				title: "Registered",
				desc: "Matter registered in the system",
				detail: "Auto-routing, timeline entry, limitation computed",
			},
			{
				num: 3,
				icon: "fa-check-circle",
				color: "#2e7d32",
				bg: "#e8f5e9",
				border: "#2e7d32",
				title: "Active",
				desc: "Team reviews and activates the matter",
				detail: "Matter type, court, judge, assigned advocate set",
			},
			{
				num: 4,
				icon: "fa-gavel",
				color: "#7b1fa2",
				bg: "#f3e5f5",
				border: "#7b1fa2",
				title: "Hearings & Documents",
				desc: "Track hearings, generate & approve documents",
				detail: "Draft → Internal Review → Client Review → Finalized",
			},
			{
				num: 5,
				icon: "fa-refresh",
				color: "#00897b",
				bg: "#e0f2f1",
				border: "#00897b",
				title: "eCourts Sync",
				desc: "Auto-sync case status from eCourts",
				detail: "CNR polling, order sheets, cause lists, judgments",
			},
			{
				num: 6,
				icon: "fa-archive",
				color: "#546e7a",
				bg: "#eceff1",
				border: "#546e7a",
				title: "Close",
				desc: "Matter disposed, archived or withdrawn",
				detail: "Final timeline entry, legal hold check, archive",
			},
		];

		const $steps = $(`<div style="display:flex;gap:0;align-items:stretch;"></div>`).appendTo($card);

		steps.forEach((step, i) => {
			const $step = $(`
				<div style="flex:1;text-align:center;padding:0 4px;position:relative;">
					<div style="width:52px;height:52px;border-radius:50%;background:${step.bg};border:2px solid ${step.border};display:flex;align-items:center;justify-content:center;margin:0 auto 10px;font-size:20px;color:${step.color};">
						<i class="fa ${step.icon}"></i>
					</div>
					<div style="font-weight:700;color:#1a237e;font-size:13px;margin-bottom:4px;">${step.num}. ${step.title}</div>
					<div style="color:#546e7a;font-size:11px;line-height:1.4;">${step.desc}</div>
					<div style="color:#90a4ae;font-size:10px;line-height:1.3;margin-top:4px;font-style:italic;">${step.detail}</div>
				</div>
			`).appendTo($steps);

			// Arrow between steps
			if (i < steps.length - 1) {
				$(`<div style="display:flex;align-items:center;padding-top:10px;color:#c5cae9;font-size:16px;flex-shrink:0;"><i class="fa fa-chevron-right"></i></div>`).appendTo($steps);
			}
		});

		// ── Status Flow Bar ──
		const $status = $(`<div class="frappe-card p-3 mb-4"></div>`).appendTo($body);
		$status.append(`<h6 style="color:#1a237e;margin-bottom:10px;"><i class="fa fa-arrows-h" style="margin-right:6px;"></i>Matter Status Flow</h6>`);

		const statuses = [
			{ label: "Intake Pending", color: "#1565c0", bg: "#e3f2fd" },
			{ label: "Active", color: "#2e7d32", bg: "#e8f5e9" },
			{ label: "On Hold", color: "#e65100", bg: "#fff3e0" },
			{ label: "Disposed", color: "#455a64", bg: "#eceff1" },
			{ label: "Withdrawn", color: "#455a64", bg: "#eceff1" },
			{ label: "Closed", color: "#455a64", bg: "#eceff1" },
		];

		const $flow = $(`<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"></div>`).appendTo($status);
		statuses.forEach((s, i) => {
			$(`<span style="background:${s.bg};color:${s.color};padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600;">${s.label}</span>`).appendTo($flow);
			if (i < statuses.length - 1 && i < 2) {
				$(`<i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:11px;"></i>`).appendTo($flow);
			}
		});

		// ── Document Workflow Card ──
		const $doc = $(`<div class="frappe-card p-3 mb-4"></div>`).appendTo($body);
		$doc.append(`<h6 style="color:#1a237e;margin-bottom:10px;"><i class="fa fa-file-text" style="margin-right:6px;"></i>Document Approval Workflow</h6>`);

		const docSteps = ["Draft", "Internal Review", "Client Review", "Finalized", "Executed"];
		const $docFlow = $(`<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;"></div>`).appendTo($doc);
		docSteps.forEach((s, i) => {
			const colors = { "Draft": "#90a4ae", "Internal Review": "#1565c0", "Client Review": "#f9a825", "Finalized": "#2e7d32", "Executed": "#455a64" };
			$(`<span style="background:${colors[s]}15;color:${colors[s]};padding:4px 12px;border-radius:6px;font-size:12px;font-weight:600;border:1px solid ${colors[s]}40;">${s}</span>`).appendTo($docFlow);
			if (i < docSteps.length - 1) {
				$(`<i class="fa fa-long-arrow-right" style="color:#90a4ae;font-size:11px;"></i>`).appendTo($docFlow);
			}
		});
		$doc.append(`<div style="margin-top:8px;color:#90a4ae;font-size:11px;">Sensitive templates (DV, 498A, adoption) require mandatory lawyer review before advancing past Internal Review.</div>`);

		// ── Key Features Card ──
		const $features = $(`<div class="frappe-card p-3"></div>`).appendTo($body);
		$features.append(`<h6 style="color:#1a237e;margin-bottom:10px;"><i class="fa fa-cogs" style="margin-right:6px;"></i>Key Features</h6>`);

		const features = [
			{ icon: "fa-clock-o", color: "#ef5350", text: "Auto Timeline — every event synced to matter timeline" },
			{ icon: "fa-plug", color: "#42a5f5", text: "eCourts Integration — hourly CNR polling, order sheets" },
			{ icon: "fa-magic", color: "#ab47bc", text: "AI Drafting — extract fields, suggest clauses, generate docs" },
			{ icon: "fa-bell", color: "#ff9800", text: "Hearing Reminders — daily email + calendar invite" },
			{ icon: "fa-shield", color: "#66bb6a", text: "Matter-Level Permissions — advocates see only assigned matters" },
			{ icon: "fa-plug", color: "#26a69a", text: "Portal Sync — IP India, NCLT, RERA auto-polling" },
			{ icon: "fa-file-o", color: "#5c6bc0", text: "Template Engine — Jinja merge tags, clause library" },
			{ icon: "fa-pencil", color: "#8d6e63", text: "E-Signature — DocuSign, eMudhra, SignDesk integration" },
		];

		const $featGrid = $(`<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"></div>`).appendTo($features);
		features.forEach((f) => {
			$(`<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#f8f9fa;border-radius:6px;">
				<i class="fa ${f.icon}" style="color:${f.color};font-size:14px;width:18px;text-align:center;"></i>
				<span style="font-size:12px;color:#455a64;">${f.text}</span>
			</div>`).appendTo($featGrid);
		});
	}
}
