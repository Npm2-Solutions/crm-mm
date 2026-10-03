# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A booking made on the centre's own pages with no tracked visit was filed under
"Third Party", as a platform's booking is. It came in directly: the people and
deals it brought keep their source and read "Direct Traffic" for that touch
(`crm.api.booking.categoria_senza_visita`)."""

import frappe

from crm.api.tracking import FONTI_NOSTRE, TRACKED_DOCTYPES


def execute():
	for doctype in TRACKED_DOCTYPES:
		for tocco in ("first_touch", "last_touch"):
			frappe.db.set_value(
				doctype,
				{f"{tocco}_category": "Third Party", f"{tocco}_source": ["in", list(FONTI_NOSTRE)]},
				f"{tocco}_category",
				"Direct Traffic",
				update_modified=False,
			)
