/* Chamber — Litigation Timeline View
 * Chronological, filterable timeline with milestone markers and
 * statutory/limitation deadline countdown bands.
 * Exposed globally as window.chamber.timeline
 */
frappe.provide("chamber.timeline");

(function () {
	const EVENT_COLORS = {
		Milestone: "blue",
		Filing: "purple",
		Hearing: "orange",
		Notice: "yellow",
		Order: "green",
		Document: "cyan",
		Task: "grey",
		"Custody Change": "red",
		Other: "grey",
	};

	function band_class(band) {
		if (band.status === "expired") return "danger";
		if (band.status === "critical") return "warning";
		if (band.status === "warning") return "orange";
		return "green";
	}

	function render_bands(bands, container) {
		if (!bands || !bands.length) return;
		const $bands = $(`<div class="chamber-deadline-bands"></div>`).appendTo(container);
		$bands.append(`<h6>Deadlines</h6>`);
		bands.forEach((band) => {
			const days = band.days_left;
			const label =
				days < 0
					? `Expired ${Math.abs(days)} day(s) ago`
					: days === 0
					? "Due today"
					: `${days} day(s) left`;
			$bands.append(`
				<div class="chamber-band chamber-band-${band_class(band)}">
					<div class="d-flex justify-content-between">
						<strong>${frappe.utils.escape_html(band.label)}</strong>
						<span class="badge">${label}</span>
					</div>
					<div class="text-muted small">${frappe.utils.escape_html(band.note || "")}</div>
					<div class="chamber-band-bar">
						<div class="chamber-band-fill" style="width: 100%"></div>
					</div>
				</div>`);
		});
	}

	function render_milestones(milestones, container) {
		if (!milestones || !milestones.length) return;
		const $m = $(`<div class="chamber-milestones"></div>`).appendTo(container);
		$m.append(`<h6>Milestone Path</h6>`);
		const chips = milestones
			.map((ms) => `<span class="chamber-milestone-chip">${frappe.utils.escape_html(ms)}</span>`)
			.join("");
		$m.append(`<div class="d-flex flex-wrap" style="gap: 6px;">${chips}</div>`);
	}

	function render_events(events, container) {
		const $e = $(`<div class="chamber-events"></div>`).appendTo(container);
		$e.append(`<h6>Case Timeline</h6>`);
		if (!events.length) {
			$e.append(`<div class="text-muted">No timeline events yet. Add hearings, documents or entries to build the timeline.</div>`);
			return;
		}
		const $list = $(`<div class="chamber-event-list"></div>`).appendTo($e);
		events.forEach((ev) => {
			const color = EVENT_COLORS[ev.event_type] || "grey";
			const milestone = ev.milestone
				? `<span class="label label-default">${frappe.utils.escape_html(ev.milestone)}</span>`
				: "";
			$list.append(`
				<div class="chamber-event" data-event-type="${frappe.utils.escape_html(ev.event_type)}">
					<div class="chamber-event-marker ${color}"></div>
					<div class="chamber-event-body">
						<div class="d-flex justify-content-between">
							<strong>${frappe.utils.escape_html(ev.title)}</strong>
							<span class="text-muted small">${frappe.utils.escape_html(ev.date || "")}</span>
						</div>
						${milestone}
						<div class="text-muted small">${frappe.utils.escape_html(ev.description || "")}</div>
						<div class="text-muted small">
							<span class="label label-${color}">${frappe.utils.escape_html(ev.event_type)}</span>
							${ev.source ? `<span class="text-muted"> • ${frappe.utils.escape_html(ev.source)}</span>` : ""}
						</div>
					</div>
				</div>`);
		});
	}

	chamber.timeline.render = function (opts) {
		/* opts: { container, data: {events, milestones, deadline_bands}, filters: true } */
		const container = opts.container;
		const data = opts.data || {};
		container.empty();
		const $wrap = $(`<div class="chamber-timeline"></div>`).appendTo(container);

		render_bands(data.deadline_bands, $wrap);
		render_milestones(data.milestones, $wrap);
		render_events(data.events, $wrap);

		if (opts.filters !== false && data.events && data.events.length) {
			const types = ["All"].concat([...new Set(data.events.map((e) => e.event_type))]);
			const $filter = $(`<div class="chamber-filter" style="margin-bottom: 1rem;"></div>`).prependTo($wrap);
			$filter.append(`<span class="text-muted small mr-2">Filter:</span>`);
			types.forEach((t) => {
				const $btn = $(`<button class="btn btn-xs ${t === "All" ? "btn-primary" : "btn-default"}">${t}</button>`);
				$btn.on("click", () => {
					$filter.find(".btn").removeClass("btn-primary").addClass("btn-default");
					$btn.addClass("btn-primary").removeClass("btn-default");
					container.find(".chamber-event").each(function () {
						const show = t === "All" || $(this).data("event-type") === t;
						$(this).toggle(show);
					});
				});
				$filter.append($btn);
			});
		}
	};
})();
