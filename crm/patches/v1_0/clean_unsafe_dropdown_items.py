# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Home Actions a browser would run.

The avatar menu drew any icon beginning with `<svg` as raw HTML and opened
whatever route it was given, and a Sales Manager can edit both: an `onerror=` in
the icon or a `javascript:` route ran in the browser of everyone who opened the
menu, System Managers included. Saving now takes only a Feather icon name and a
path or http(s) link; this clears what was stored before.

An icon that is not a Feather name is emptied, SVG included, since the menu no
longer draws markup of any kind: the entry gets the default icon. A route with
any other scheme is emptied and its row hidden, so the entry stays in Home
Actions for someone to look at rather than vanishing. FCRM Settings keeps no
version history, so what was removed is printed: it may be the only trace of who
planted what.
"""

import frappe

from crm.fcrm.doctype.crm_dropdown_item.crm_dropdown_item import is_allowed_icon, is_safe_route


def execute():
	for row in frappe.get_all(
		"CRM Dropdown Item", fields=["name", "idx", "type", "icon", "route"], order_by="idx"
	):
		values = {}
		if row.icon and not is_allowed_icon(row.icon.strip()):
			values["icon"] = None
		if row.route and not is_safe_route(row.route):
			values["route"] = None
			if row.type != "Separator":  # a separator never opens its route
				values["hidden"] = 1
		if not values:
			continue

		frappe.db.set_value("CRM Dropdown Item", row.name, values, update_modified=False)
		for field in ("icon", "route"):
			if field in values:
				print(f"Home Actions row #{row.idx}: removed {field} {row[field]!r:.200}")
