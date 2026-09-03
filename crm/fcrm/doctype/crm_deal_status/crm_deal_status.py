# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline


class CRMDealStatus(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		color: DF.Literal[
			"black",
			"gray",
			"blue",
			"green",
			"red",
			"pink",
			"orange",
			"amber",
			"yellow",
			"cyan",
			"teal",
			"violet",
			"purple",
		]
		deal_status: DF.Data
		pipeline: DF.Link
		position: DF.Int
		probability: DF.Percent
		type: DF.Literal["Open", "Ongoing", "On Hold", "Won", "Lost"]
	# end: auto-generated types

	def validate(self):
		# a stage always belongs to a pipeline -- older records and records created
		# by scripts/tests land in the default one
		if not self.pipeline:
			self.pipeline = get_default_pipeline()

		if not self.position:
			last = frappe.get_all(
				"CRM Deal Status",
				filters={"pipeline": self.pipeline},
				fields=["position"],
				order_by="position desc",
				limit=1,
				pluck="position",
			)
			self.position = (last[0] if last else 0) + 1

	def on_update(self):
		# moving a stage to another pipeline takes its deals along
		if not self.is_new() and self.has_value_changed("pipeline"):
			frappe.db.set_value(
				"CRM Deal", {"status": self.name}, "pipeline", self.pipeline, update_modified=False
			)
