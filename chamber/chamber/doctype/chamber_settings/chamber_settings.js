frappe.ui.form.on("Chamber Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Test Connections"), () => {
			frm.call({
				method: "chamber.api.settings.test_connections",
				callback: (r) => {
					const results = r.message || {};
					const lines = Object.keys(results)
						.map(
							(key) =>
								`<tr><td><strong>${key}</strong></td><td>${frappe.utils.escape_html(results[key].status || "")}${results[key].reachable ? `<br><span class="text-muted small">Reachability: ${results[key].reachable.ok ? "OK (" + results[key].reachable.http + ")" : "unreachable — " + frappe.utils.escape_html(results[key].reachable.error || "")}</span>` : ""}</td></tr>`
						)
						.join("");
					frappe.msgprint({
						title: __("Integration Status"),
						message: `<table class="table table-sm">${lines}</table>`,
						wide: true,
					});
				},
			});
		});

		frm.add_custom_button(__("Test eCourts Lookup (Live)"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Live eCourts Lookup"),
				fields: [
					{ fieldname: "cnr_number", fieldtype: "Data", label: __("CNR Number"), reqd: 1, placeholder: "e.g. KA01-000123-2024" },
				],
				primary_action_label: __("Lookup"),
				primary_action(values) {
					d.get_primary_btn().prop("disabled", true).text(__("Looking up…"));
					frappe.call({
						method: "chamber.api.settings.live_ecourts_check",
						args: { cnr_number: values.cnr_number },
						callback: (r) => {
							d.get_primary_btn().prop("disabled", false).text(__("Lookup"));
							const m = r.message || {};
							if (m.ok) {
								const s = m.status || {};
								frappe.msgprint({
									title: __("eCourts returned a status"),
									message:
										`<b>Case:</b> ${frappe.utils.escape_html(s.case_no || "")} ${frappe.utils.escape_html(s.case_type || "")}/${frappe.utils.escape_html(s.case_year || "")}<br>` +
										`<b>Stage:</b> ${frappe.utils.escape_html(s.case_stage || s.case_status || "—")}<br>` +
										`<b>Next hearing:</b> ${frappe.utils.escape_html(s.next_hearing_date || "—")}<br>` +
										`<b>Judge:</b> ${frappe.utils.escape_html(s.judge || "—")}`,
									indicator: "green",
								});
							} else {
								frappe.msgprint({
									title: __("eCourts lookup failed"),
									message: frappe.utils.escape_html(m.error || ""),
									indicator: "red",
								});
							}
						},
					});
				},
			});
			d.show();
		});

		frm.add_custom_button(__("Test Portal (Dry-run)"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Portal Dry-run (no writes)"),
				fields: [
					{
						fieldname: "portal",
						fieldtype: "Select",
						label: __("Portal"),
						options: "\nIP India\nNCLT / NCLAT\nState RERA",
						reqd: 1,
					},
					{ fieldname: "reference", fieldtype: "Data", label: __("Reference Number"), reqd: 1, placeholder: __("Application / case / project registration number") },
				],
				primary_action_label: __("Dry-run"),
				primary_action(values) {
					d.get_primary_btn().prop("disabled", true).text(__("Testing…"));
					frappe.call({
						method: "chamber.api.settings.dry_run_portal",
						args: { portal: values.portal, reference: values.reference },
						callback: (r) => {
							d.get_primary_btn().prop("disabled", false).text(__("Dry-run"));
							const m = r.message || {};
							if (m.ok) {
								const p = m.parsed || {};
								frappe.msgprint({
									title: __("Portal parsed successfully"),
									message:
										`<b>Status:</b> ${frappe.utils.escape_html(p.status || "")}<br>` +
										`<b>Details:</b> ${frappe.utils.escape_html(p.details || "")}<br>` +
										`<span class="text-muted small">${m.note || ""}</span>`,
									indicator: "green",
								});
							} else {
								frappe.msgprint({
									title: __("Portal dry-run failed"),
									message: `${frappe.utils.escape_html(m.error || "")}<br><span class="text-muted small">${m.note || ""}</span>`,
									indicator: "red",
								});
							}
						},
					});
				},
			});
			d.show();
		});
	},
});
