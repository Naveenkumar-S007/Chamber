/* Chamber — Conditional Intake Form Renderer
 * Renders an admin-configured field set (Intake Form Template) with
 * conditional show/hide logic (depends_on) and section grouping.
 * Exposed globally as window.chamber.intake
 */
frappe.provide("chamber.intake");

(function () {
	const CONDITION_HELP = {
		equals: "==",
		not_equals: "!=",
		in: "in",
		not_in: "not in",
		not_empty: "is filled",
		is_empty: "is empty",
		contains: "contains",
	};

	function parse_condition(depends_on, values) {
		if (!depends_on) return true;
		const raw = depends_on.trim();
		let cond = null;

		// JSON form: {"fieldname": "role", "equals": "Accused"} / {"in": [...]}
		if (raw.startsWith("{")) {
			try {
				cond = JSON.parse(raw);
			} catch (e) {
				return true;
			}
		} else {
			// Shorthand: "role=Accused", "role!=Complainant"
			const m = raw.match(/^([\w_]+)\s*(==|!=|=)\s*(.+)$/);
			if (m) {
				cond = {
					fieldname: m[1],
					equals: m[3].trim(),
				};
				if (m[2] === "!=") {
					delete cond.equals;
					cond.not_equals = m[3].trim();
				}
			} else {
				return true; // unparseable -> always show
			}
		}

		const fieldname = cond.fieldname;
		const value = values[fieldname];
		if (cond.equals !== undefined) return String(value || "") === String(cond.equals);
		if (cond.not_equals !== undefined) return String(value || "") !== String(cond.not_equals);
		if (cond.not_empty) return !!(value !== undefined && value !== null && String(value).trim() !== "");
		if (cond.is_empty) return !(value !== undefined && value !== null && String(value).trim() !== "");
		if (cond.in) return (cond.in || []).includes(String(value || ""));
		if (cond.not_in) return !(cond.not_in || []).includes(String(value || ""));
		if (cond.contains) return String(value || "").indexOf(cond.contains) !== -1;
		return true;
	}

	function build_input(field, values, onChange) {
		const $wrapper = $(`<div class="chamber-field" data-fieldname="${field.fieldname}"></div>`);
		const label = field.label;
		const reqd = field.reqd ? '<span class="text-danger"> *</span>' : "";
		const desc = field.description ? `<div class="text-muted small">${frappe.utils.escape_html(field.description)}</div>` : "";

		switch (field.fieldtype) {
			case "Heading":
				$wrapper.html(`<h5>${label}${desc}</h5>`);
				return $wrapper;
			case "Section Break":
				$wrapper.html(`<div class="chamber-section-title">${label}</div>${desc}`);
				return $wrapper;
			case "Column Break":
				$wrapper.html(`<div class="row chamber-column"></div>`);
				return $wrapper;
			case "Check":
				$wrapper.html(`
					<div class="form-group chamber-check">
						<div class="checkbox">
							<label>
								<input type="checkbox" data-fieldname="${field.fieldname}" ${values[field.fieldname] ? "checked" : ""}>
								${label}${reqd}
							</label>
						</div>
						${desc}
					</div>`);
				break;
			case "Select": {
				const options = (field.options || "")
					.split("\n")
					.map((o) => o.trim())
					.filter(Boolean)
					.map(
						(o) =>
							`<option value="${frappe.utils.escape_html(o)}" ${
								String(values[field.fieldname] || "") === o ? "selected" : ""
							}>${frappe.utils.escape_html(o)}</option>`
					)
					.join("");
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<select class="form-control chamber-input" data-fieldname="${field.fieldname}">
							<option value="">— Select —</option>${options}
						</select>
						${desc}
					</div>`);
				break;
			}
			case "Date":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="date" class="form-control chamber-input" data-fieldname="${field.fieldname}" value="${values[field.fieldname] || ""}">
						${desc}
					</div>`);
				break;
			case "Text":
			case "Small Text":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<textarea rows="3" class="form-control chamber-input" data-fieldname="${field.fieldname}">${values[field.fieldname] || ""}</textarea>
						${desc}
					</div>`);
				break;
			case "Int":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="number" step="1" class="form-control chamber-input" data-fieldname="${field.fieldname}" value="${values[field.fieldname] || ""}">
						${desc}
					</div>`);
				break;
			case "Currency":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="number" step="0.01" class="form-control chamber-input" data-fieldname="${field.fieldname}" value="${values[field.fieldname] || ""}">
						${desc}
					</div>`);
				break;
			case "Link":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="text" class="form-control chamber-link-input" data-fieldname="${field.fieldname}" data-link-doctype="${frappe.utils.escape_html(field.options || "")}" value="${values[field.fieldname] || ""}" placeholder="Type to search ${field.options || ""}...">
						${desc}
					</div>`);
				break;
			case "Attach":
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="file" class="form-control-file chamber-file-input" data-fieldname="${field.fieldname}">
						${desc}
					</div>`);
				break;
			default:
				// Data
				$wrapper.html(`
					<div class="form-group">
						<label>${label}${reqd}</label>
						<input type="text" class="form-control chamber-input" data-fieldname="${field.fieldname}" value="${values[field.fieldname] || ""}">
						${desc}
					</div>`);
		}

		$wrapper.on("input change", ".chamber-input, .chamber-check input, .chamber-link-input", function () {
			onChange(field.fieldname, $(this).val(), this.type === "checkbox" ? this.checked : undefined);
		});
		return $wrapper;
	}

	chamber.intake.render = function (opts) {
		/* opts: { fields: [...], container: $el, values: {}, onSubmit(values, $btn), vertical: '' } */
		const fields = opts.fields || [];
		const container = opts.container;
		const values = Object.assign({}, opts.values || {});
		container.empty();

		const $form = $(`<form class="chamber-intake-form"></form>`);
		const rendered = {};

		function applyVisibility() {
			Object.keys(rendered).forEach((key) => {
				const field = rendered[key].field;
				const visible = parse_condition(field.depends_on, values);
				rendered[key].$el.toggle(visible);
				if (!visible) delete values[field.fieldname];
			});
		}

		function handleChange(fieldname, rawValue, isChecked) {
			let value = rawValue;
			if (isChecked !== undefined) value = isChecked ? 1 : 0;
			values[fieldname] = value;
			applyVisibility();
		}

		fields.forEach((field) => {
			const $el = build_input(field, values, handleChange);
			$form.append($el);
			rendered[field.fieldname] = { field, $el };
		});
		applyVisibility();

		const $actions = $(`
			<div class="chamber-intake-actions" style="margin-top: 1.5rem;">
				<button type="button" class="btn btn-primary chamber-submit-btn">Submit Intake</button>
				<button type="button" class="btn btn-default chamber-reset-btn">Reset</button>
			</div>`);
		$form.append($actions);

		$actions.find(".chamber-submit-btn").on("click", () => {
			const missing = [];
			fields.forEach((f) => {
				if (f.reqd && f.fieldtype !== "Section Break" && f.fieldtype !== "Column Break" && f.fieldtype !== "Heading") {
					const v = values[f.fieldname];
					if (v === undefined || v === null || String(v).trim() === "") missing.push(f.label);
				}
			});
			if (missing.length) {
				frappe.msgprint(__("Please fill the mandatory fields: {0}", [missing.join(", ")]));
				return;
			}
			if (opts.onSubmit) opts.onSubmit(values, $actions.find(".chamber-submit-btn"));
		});
		$actions.find(".chamber-reset-btn").on("click", () => {
			Object.keys(values).forEach((k) => delete values[k]);
			chamber.intake.render(opts);
		});

		return { getValues: () => values };
	};

	chamber.intake.condition_help = CONDITION_HELP;
})();
