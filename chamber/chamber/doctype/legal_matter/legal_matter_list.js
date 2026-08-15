frappe.listview_settings["Legal Matter"] = {
	add_fields: ["vertical", "matter_type", "status", "priority", "client", "is_archived", "legal_hold"],
	get_indicator(doc) {
		if (doc.is_archived) {
			return [__("Archived"), "grey", "is_archived,=,1"];
		}
		const status_color = {
			"Intake Pending": "blue",
			"Active": "green",
			"On Hold": "orange",
			"Disposed": "grey",
			"Withdrawn": "grey",
			"Closed": "grey",
		};
		const indicator = [__(doc.status), status_color[doc.status] || "blue", "status,=," + doc.status];
		if (doc.legal_hold) {
			indicator[1] = "red";
			indicator[0] = __(doc.status) + " · " + __("Legal Hold");
		}
		return indicator;
	},
};
