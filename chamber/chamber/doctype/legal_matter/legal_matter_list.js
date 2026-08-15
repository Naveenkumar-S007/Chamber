frappe.listview_settings["Legal Matter"] = {
	add_fields: ["vertical", "matter_type", "status", "priority", "client"],
	get_indicator(doc) {
		const status_color = {
			"Intake Pending": "blue",
			"Active": "green",
			"On Hold": "orange",
			"Disposed": "grey",
			"Withdrawn": "grey",
			"Closed": "grey",
		};
		return [__(doc.status), status_color[doc.status] || "blue", "status,=," + doc.status];
	},
};
