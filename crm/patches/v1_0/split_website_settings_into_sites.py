# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Turn the one website into the first of several.

`CRM Website Settings` used to be a Single holding brand, menu, footer, SEO and tracking
for the one site a CRM could have. Sites are now records, so those values move to a
`CRM Web Site` named "Sito principale" and every existing Builder Page is assigned to it.

Runs before the model sync, while the old columns still exist — after the sync they are
gone, and with them anything not copied here.
"""

import frappe

MOVED_FIELDS = (
	"site_title",
	"tagline",
	"logo",
	"favicon",
	"primary_color",
	"font_family",
	"footer_text",
	"company_name",
	"vat_number",
	"address",
	"email",
	"phone",
	"whatsapp_number",
	"privacy_route",
	"terms_route",
	"default_meta_title",
	"default_meta_description",
	"default_og_image",
	"robots_indexable",
	"ga4_id",
	"meta_pixel_id",
	"consent_banner",
	"consent_text",
)


def execute():
	if not frappe.db.table_exists("Singles"):
		return
	if frappe.db.exists("CRM Web Site", {"slug": ""}) or frappe.db.count("CRM Web Site"):
		return

	values = {field: frappe.db.get_single_value("CRM Website Settings", field) for field in MOVED_FIELDS}
	home_page = frappe.db.get_single_value("CRM Website Settings", "home_page")
	serve_at_root = frappe.db.get_single_value("CRM Website Settings", "serve_at_root")
	enabled = frappe.db.get_single_value("CRM Website Settings", "enabled")

	if not any(values.values()) and not home_page and not enabled:
		# nothing was ever configured: leave a clean slate rather than an empty record
		return

	site = frappe.get_doc(
		{
			"doctype": "CRM Web Site",
			"site_name": "Sito principale",
			# empty on purpose: the pages that already exist have no folder in their
			# routes, and moving them would break every link already in circulation
			"slug": "",
			"enabled": 1,
			"home_page": home_page,
			"serve_at_root": serve_at_root,
			**{k: v for k, v in values.items() if v is not None},
		}
	)
	site.flags.ignore_validate = True
	site.insert(ignore_permissions=True)

	for table in ("CRM Web Nav Item", "CRM Web Social Link"):
		frappe.db.sql(
			"""update `tab{table}` set parent=%s, parenttype='CRM Web Site'
			where parenttype='CRM Website Settings'""".format(table=table),
			site.name,
		)

	if frappe.db.has_column("Builder Page", "crm_site"):
		frappe.db.sql("update `tabBuilder Page` set crm_site=%s where ifnull(crm_site,'')=''", site.name)

	frappe.db.set_single_value("CRM Website Settings", "default_site", site.name)
	print(f"Website settings moved to CRM Web Site {site.name}")
