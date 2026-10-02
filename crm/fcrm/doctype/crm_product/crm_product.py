# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

from frappe.model.document import Document

from crm.api.site_routes import apply_website_fields


class CRMProduct(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cta_label: DF.Data | None
		cta_target: DF.Data | None
		cta_type: DF.Literal["Book", "Form", "Link", "None"]
		description: DF.TextEditor | None
		disabled: DF.Check
		image: DF.AttachImage | None
		naming_series: DF.Literal["CRM-PROD-.YYYY.-"]
		product_code: DF.Data
		product_name: DF.Data | None
		publish_on_website: DF.Check
		seo_description: DF.SmallText | None
		seo_title: DF.Data | None
		short_description: DF.SmallText | None
		standard_rate: DF.Currency
		website_order: DF.Int
		website_slug: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.set_product_name()
		apply_website_fields(self)

	def set_product_name(self):
		self.product_name = (self.product_name or self.product_code or "").strip()
