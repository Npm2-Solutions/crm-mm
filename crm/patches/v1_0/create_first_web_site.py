# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Turn the one website into the first of several.

`CRM Website Settings` used to be a Single holding brand, menu, footer, SEO and tracking
for the one site a CRM could have. Sites are now records, so those values move to a
`CRM Web Site` named "Sito principale" and every existing Builder Page is assigned to it.

Renamed from `split_website_settings_into_sites`: that one was registered in
`[pre_model_sync]`, where it could only fail — so it never reached the Patch Log, and a
site that already tried it will run this one instead.

Runs **after** the model sync, for two reasons that the first version got wrong:

- the record cannot be created before `CRM Web Site` exists, and it is the sync that
  creates it;
- reading the old values afterwards is safe anyway. A Single's values live as rows in
  `tabSingles`, keyed by doctype and fieldname; dropping a field from the doctype leaves
  those rows alone, so `get_single_value` still finds them.

It also installs `Builder Page.crm_site` itself instead of waiting for the `after_migrate`
hook, which runs later — otherwise the column would not exist yet and no page would be
assigned to anything.
"""

import frappe

from crm.install import add_builder_page_custom_fields

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
	if not frappe.db.exists("DocType", "CRM Web Site"):
		return
	if frappe.db.count("CRM Web Site"):
		return

	add_builder_page_custom_fields()

	values = {field: frappe.db.get_single_value("CRM Website Settings", field) for field in MOVED_FIELDS}
	home_page = frappe.db.get_single_value("CRM Website Settings", "home_page")
	serve_at_root = frappe.db.get_single_value("CRM Website Settings", "serve_at_root")
	enabled = frappe.db.get_single_value("CRM Website Settings", "enabled")

	pages = _existing_pages()
	if not any(values.values()) and not home_page and not enabled and not pages:
		# nothing was ever configured and there is nothing to adopt: leave a clean slate
		# rather than an empty record the user then has to understand
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
		if not frappe.db.table_exists(table):
			continue
		frappe.db.sql(
			f"""update `tab{table}` set parent=%s, parenttype='CRM Web Site'
			where parenttype='CRM Website Settings'""",
			site.name,
		)

	if pages:
		frappe.db.sql("update `tabBuilder Page` set crm_site=%s where ifnull(crm_site,'')=''", site.name)

	frappe.db.set_single_value("CRM Website Settings", "default_site", site.name)
	print(f"Website settings moved to CRM Web Site {site.name} ({len(pages)} pages adopted)")


def _existing_pages() -> list[str]:
	if not frappe.db.exists("DocType", "Builder Page"):
		return []
	return frappe.get_all("Builder Page", filters={"is_template": 0}, pluck="name")
