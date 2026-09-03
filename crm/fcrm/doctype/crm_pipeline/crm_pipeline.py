# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

# A pipeline is a named, ordered set of deal stages ("CRM Deal Status" records
# pointing back at it). A deal always belongs to exactly one pipeline, derived
# from its stage -- the stage is the single source of truth, so the two can
# never drift apart.


class CRMPipeline(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.SmallText | None
		disabled: DF.Check
		is_default: DF.Check
		pipeline_name: DF.Data
		position: DF.Int
	# end: auto-generated types

	def validate(self):
		if self.is_default and self.disabled:
			frappe.throw(_("The default pipeline cannot be disabled"))

		if not self.position:
			last = frappe.get_all(
				"CRM Pipeline", fields=["position"], order_by="position desc", limit=1, pluck="position"
			)
			self.position = (last[0] if last else 0) + 1

		if not self.is_new() and self.has_value_changed("is_default") and not self.is_default:
			# the flag is only ever cleared by making another pipeline the default
			if not frappe.db.exists("CRM Pipeline", {"is_default": 1, "name": ("!=", self.name)}):
				frappe.throw(_("One pipeline must be the default one"))

	def before_insert(self):
		# the very first pipeline is the default one
		if not frappe.db.exists("CRM Pipeline", {"is_default": 1}):
			self.is_default = 1

	def on_update(self):
		if self.is_default:
			frappe.db.set_value(
				"CRM Pipeline",
				{"name": ("!=", self.name), "is_default": 1},
				"is_default",
				0,
				update_modified=False,
			)

	def on_trash(self):
		if self.is_default:
			frappe.throw(_("The default pipeline cannot be deleted"))

		if self.has_deals():
			frappe.throw(
				_("{0} still has deals in it. Move them to another pipeline first.").format(
					frappe.bold(self.name)
				)
			)

		# its stages hold no deals anymore (nothing links to them), so they go with it
		for stage in get_pipeline_stages(self.name):
			frappe.delete_doc("CRM Deal Status", stage, ignore_permissions=True)

	def has_deals(self) -> bool:
		return bool(frappe.db.exists("CRM Deal", {"pipeline": self.name}))


def get_default_pipeline() -> str | None:
	"""Name of the pipeline new deals land in, or None when there is none yet."""
	pipeline = frappe.db.get_value("CRM Pipeline", {"is_default": 1, "disabled": 0}, "name")
	if pipeline:
		return pipeline

	return frappe.db.get_value("CRM Pipeline", {"disabled": 0}, "name", order_by="position asc")


def get_pipeline_stages(pipeline: str | None, only_names: bool = True) -> list:
	"""Stages of a pipeline, in board order."""
	if not pipeline:
		return []

	fields = ["name"] if only_names else ["name", "color", "type", "position", "probability"]
	stages = frappe.get_all(
		"CRM Deal Status",
		filters={"pipeline": pipeline},
		fields=fields,
		order_by="position asc, name asc",
	)
	return [stage.name for stage in stages] if only_names else stages


def get_first_stage(pipeline: str | None) -> str | None:
	"""First open stage of a pipeline, falling back to its first stage."""
	if not pipeline:
		return None

	open_stage = frappe.get_all(
		"CRM Deal Status",
		filters={"pipeline": pipeline, "type": "Open"},
		pluck="name",
		order_by="position asc, name asc",
		limit=1,
	)
	if open_stage:
		return open_stage[0]

	stages = get_pipeline_stages(pipeline)
	return stages[0] if stages else None


def get_pipeline_of_stage(stage: str | None) -> str | None:
	if not stage:
		return None

	return frappe.db.get_value("CRM Deal Status", stage, "pipeline")
