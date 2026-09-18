# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Fill `facebook_ad_id` on the leads imported before the field existed.

The spend report joins ads to leads on this field, so without it every lead
imported so far would count for nothing. Two places still hold the answer:
`first_touch_content`, which carried the bare ad id whenever the name could not
be read, and nothing else — a lead whose content is already a name cannot be
resolved backwards, and inventing one would be worse than leaving it empty.
"""

import frappe


def execute():
	if not frappe.db.has_column("CRM Lead", "facebook_ad_id"):
		return

	frappe.db.sql(
		"""
		update `tabCRM Lead`
		set facebook_ad_id = first_touch_content
		where ifnull(facebook_ad_id, '') = ''
			and first_touch_landing_page = 'lead_ad_form'
			and first_touch_content regexp '^[0-9]{6,}$'
		"""
	)
