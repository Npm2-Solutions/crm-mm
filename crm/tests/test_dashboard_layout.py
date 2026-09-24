# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Periods, grid layouts and widget payloads — pure, no database: runs with plain ``unittest`` too."""

import datetime
import unittest

from crm.dashboard import charts, layout, periods

D = datetime.date


class TestPeriods(unittest.TestCase):
	def test_previous_period_has_the_same_length_and_ends_the_day_before(self):
		self.assertEqual(periods.previous(D(2026, 9, 1), D(2026, 9, 30)), (D(2026, 8, 2), D(2026, 8, 31)))
		# month to date is compared with the same number of days before it, not a full month
		self.assertEqual(periods.previous(D(2026, 9, 1), D(2026, 9, 24)), (D(2026, 8, 8), D(2026, 8, 31)))
		self.assertEqual(periods.previous(D(2026, 9, 24), D(2026, 9, 24)), (D(2026, 9, 23), D(2026, 9, 23)))

	def test_bounds_are_half_open_so_the_last_day_counts_whole(self):
		low, high = periods.bounds(D(2026, 9, 1), D(2026, 9, 30))
		self.assertEqual(low, datetime.datetime(2026, 9, 1))
		self.assertEqual(high, datetime.datetime(2026, 10, 1))

	def test_normalize_fills_missing_ends_and_swaps_reversed_ones(self):
		today = D(2026, 9, 24)
		self.assertEqual(periods.normalize(None, None, today), (D(2026, 9, 1), D(2026, 9, 30)))
		self.assertEqual(periods.normalize("2026-09-30", "2026-09-01", today), (D(2026, 9, 1), D(2026, 9, 30)))
		self.assertEqual(periods.normalize("2026-09-10 10:00:00", "", today), (D(2026, 9, 10), D(2026, 9, 24)))
		self.assertEqual(periods.normalize("not a date", None, today), (D(2026, 9, 1), D(2026, 9, 30)))

	def test_grain_follows_the_length(self):
		self.assertEqual(periods.grain(D(2026, 9, 1), D(2026, 9, 30)), "day")
		self.assertEqual(periods.grain(D(2026, 6, 1), D(2026, 9, 30)), "week")
		self.assertEqual(periods.grain(D(2026, 1, 1), D(2026, 12, 31)), "month")

	def test_buckets_cover_the_period_without_gaps(self):
		weeks = periods.buckets(D(2026, 9, 1), D(2026, 9, 30), "week")
		self.assertEqual(weeks[0], D(2026, 8, 31))  # the Monday of the first week
		self.assertEqual(weeks[-1], D(2026, 9, 28))
		self.assertEqual(len(weeks), 5)
		months = periods.buckets(D(2026, 1, 15), D(2026, 3, 2), "month")
		self.assertEqual(months, [D(2026, 1, 1), D(2026, 2, 1), D(2026, 3, 1)])

	def test_delta_percent_needs_something_to_compare_with(self):
		self.assertEqual(periods.delta_percent(15, 10), 50)
		self.assertEqual(periods.delta_percent(5, 10), -50)
		self.assertIsNone(periods.delta_percent(5, 0))
		self.assertIsNone(periods.delta_percent(5, None))


class TestPack(unittest.TestCase):
	def line(self, *names, h=3, min_w=4):
		return {"items": [{"name": name, "type": "number"} for name in names], "h": h, "min_w": min_w}

	def test_a_full_row_is_shared_evenly(self):
		items = layout.pack([self.line("a", "b", "c", "d", "e")])
		self.assertEqual([item["layout"]["w"] for item in items], [4, 4, 4, 4, 4])
		self.assertEqual([item["layout"]["x"] for item in items], [0, 4, 8, 12, 16])

	def test_missing_widgets_leave_no_hole(self):
		items = layout.pack([self.line("a", "b", "c")])
		self.assertEqual([item["layout"]["w"] for item in items], [7, 7, 6])
		self.assertEqual(sum(item["layout"]["w"] for item in items), layout.GRID_COLUMNS)

	def test_a_crowded_line_wraps(self):
		items = layout.pack([self.line("a", "b", "c", "d", "e", "f")])
		self.assertEqual([item["layout"]["y"] for item in items], [0, 0, 0, 0, 0, 3])
		self.assertEqual(items[-1]["layout"]["w"], layout.GRID_COLUMNS)

	def test_lines_stack_and_keys_are_stable_and_unique(self):
		first = layout.pack([self.line("a", "b"), self.line("a", h=8, min_w=10)])
		again = layout.pack([self.line("a", "b"), self.line("a", h=8, min_w=10)])
		self.assertEqual(first, again)
		self.assertEqual([item["layout"]["i"] for item in first], ["a", "b", "a_2"])
		self.assertEqual(first[2]["layout"]["y"], 3)

	def test_empty_lines_are_skipped(self):
		self.assertEqual(layout.pack([{"items": []}, self.line()]), [])


class TestSanitize(unittest.TestCase):
	def test_keeps_only_well_formed_entries(self):
		raw = [
			"nope",
			{"name": ""},
			{"name": "won_deals", "layout": {"x": 0, "y": 0, "w": 4, "h": 3, "i": "won"}, "data": {"value": 1}},
		]
		cleaned = layout.sanitize(raw)
		self.assertEqual(len(cleaned), 1)
		self.assertNotIn("data", cleaned[0])
		self.assertEqual(cleaned[0]["layout"]["i"], "won")

	def test_pulls_widgets_back_inside_the_grid(self):
		cleaned = layout.sanitize([{"name": "a", "layout": {"x": 18, "y": -5, "w": 10, "h": 999}}])
		position = cleaned[0]["layout"]
		self.assertEqual((position["x"], position["y"], position["w"]), (10, 0, 10))
		self.assertEqual(position["h"], layout.MAX_HEIGHT)

	def test_duplicate_keys_get_fresh_ones(self):
		cleaned = layout.sanitize(
			[{"name": "a", "layout": {"i": "same"}}, {"name": "b", "layout": {"i": "same"}}, {"name": "c"}]
		)
		keys = [item["layout"]["i"] for item in cleaned]
		self.assertEqual(len(set(keys)), 3)
		self.assertEqual(keys[0], "same")

	def test_config_keeps_only_the_keys_the_widget_accepts(self):
		cleaned = layout.sanitize(
			[
				{
					"name": "deals_by_stage",
					"config": {"title": " Pipeline ", "measure": "value", "evil": "<script>", "limit": 5},
				}
			],
			{"deals_by_stage": {"measure"}},
		)
		self.assertEqual(cleaned[0]["config"], {"title": "Pipeline", "measure": "value"})

	def test_not_a_list_is_an_empty_layout(self):
		self.assertEqual(layout.sanitize({"name": "a"}), [])
		self.assertEqual(layout.sanitize(None), [])

	def test_at_most_max_items(self):
		cleaned = layout.sanitize([{"name": f"w{index}"} for index in range(layout.MAX_ITEMS + 10)])
		self.assertEqual(len(cleaned), layout.MAX_ITEMS)


class TestPayloads(unittest.TestCase):
	def test_number_compares_in_percent_or_in_points(self):
		self.assertEqual(charts.number(15, 10)["delta"], 50)
		self.assertEqual(charts.number(15, 10)["deltaUnit"], "percent")
		rate = charts.number(45.5, 40, format="percent", compare="points")
		self.assertEqual((rate["delta"], rate["deltaUnit"]), (5.5, "points"))
		# nothing to compare with is no delta, not an infinite rise
		self.assertNotIn("delta", charts.number(5, 0))
		self.assertNotIn("previous", charts.number(5))

	def test_number_keeps_progress_inside_a_meter(self):
		self.assertEqual(charts.number(1, progress=140)["progress"], 100)
		self.assertEqual(charts.number(1, progress=-3)["progress"], 0)

	def test_donut_folds_the_tail_into_other(self):
		rows = [(f"s{index}", 10 - index) for index in range(9)] + [("zero", 0)]
		donut = charts.donut(rows, other_label="Other")
		self.assertEqual(len(donut["slices"]), charts.MAX_SLICES)
		self.assertEqual(donut["slices"][-1], {"label": "Other", "value": 5 + 4 + 3 + 2})
		self.assertEqual(donut["total"], sum(10 - index for index in range(9)))

	def test_donut_names_the_empty_label(self):
		self.assertEqual(charts.donut([(None, 3)], empty_label="Not set")["slices"][0]["label"], "Not set")

	def test_funnel_shares(self):
		steps = charts.funnel([("Opened", 20), ("Proposal", 10), ("Won", 4)])["steps"]
		self.assertEqual([step["ofFirst"] for step in steps], [100, 50, 20])
		self.assertEqual([step["ofPrevious"] for step in steps], [None, 50, 40])

	def test_trend_fills_empty_buckets_with_zero(self):
		buckets = [D(2026, 9, 1), D(2026, 9, 2), D(2026, 9, 3)]
		values = charts.fill(buckets, {D(2026, 9, 2): 4})
		self.assertEqual(values, [0, 4, 0])
		trend = charts.trend(buckets, "day", [charts.series("a", "A", values)])
		self.assertEqual(trend["x"]["values"], ["2026-09-01", "2026-09-02", "2026-09-03"])

	def test_heatmap_keeps_non_empty_cells(self):
		heat = charts.heatmap({(9, 0): 3, (10, 0): 0}, x_labels=["09", "10"], y_labels=["Mon"])
		self.assertEqual(heat["cells"], [[9, 0, 3]])
		self.assertEqual(heat["max"], 3)

	def test_ratio_without_a_whole_is_none(self):
		self.assertIsNone(charts.ratio(3, 0))
		self.assertEqual(charts.ratio(1, 3), 33.3)


if __name__ == "__main__":
	unittest.main()
