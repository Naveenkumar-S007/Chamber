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
	},
});
