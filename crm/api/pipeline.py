"""Pipelines and their stages.

A pipeline ("CRM Pipeline") is an ordered set of deal stages ("CRM Deal Status"
records pointing at it). Deals live in exactly one pipeline, derived from their
stage. This module is what the Settings > Pipelines screen talks to.

Stage names are unique across the whole site (the deal's `status` field links to
them by name), so two pipelines cannot both have a stage called "Qualification".
Callers get a readable error instead of a database one.
"""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import (
	get_default_pipeline,
	get_first_stage,
	get_pipeline_stages,
)
from crm.utils import is_frappe_version

MANAGER_ROLES = {"System Manager", "Sales Manager"}

DEFAULT_PIPELINE_NAME = "Sales"

DEFAULT_STAGES = [
	{"stage": "Qualification", "color": "gray", "type": "Open", "probability": 10},
	{"stage": "Demo/Making", "color": "orange", "type": "Ongoing", "probability": 25},
	{"stage": "Proposal/Quotation", "color": "blue", "type": "Ongoing", "probability": 50},
	{"stage": "Negotiation", "color": "yellow", "type": "Ongoing", "probability": 70},
	{"stage": "Ready to Close", "color": "purple", "type": "Ongoing", "probability": 90},
	{"stage": "Won", "color": "green", "type": "Won", "probability": 100},
	{"stage": "Lost", "color": "red", "type": "Lost", "probability": 0},
]


def create_default_pipeline() -> str:
	"""The pipeline new deals land in. Idempotent -- used by install and by the patch."""
	default = get_default_pipeline()
	if default:
		return default

	doc = frappe.new_doc("CRM Pipeline")
	doc.pipeline_name = DEFAULT_PIPELINE_NAME
	doc.description = _("Default sales pipeline")
	doc.is_default = 1
	doc.position = 1
	doc.insert(ignore_permissions=True)
	return doc.name


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage pipelines"), frappe.PermissionError)


def _parse(value, fallback):
	if value is None or value == "":
		return fallback
	if isinstance(value, str):
		return json.loads(value)
	return value


def _deal_counts(field: str) -> dict:
	# get_list, not get_all: a user only counts the deals they are allowed to see
	count = (
		{"COUNT": "name", "as": "total"} if is_frappe_version("16", above=True) else "count(name) as total"
	)
	rows = frappe.get_list("CRM Deal", fields=[field, count], group_by=field, as_list=True)
	return {row[0]: row[1] for row in rows}


@frappe.whitelist()
def get_pipelines(with_counts: bool | int = False) -> list[dict]:
	"""Every pipeline with its stages, in board order.

	`with_counts` adds how many deals sit in each pipeline and each stage -- two
	grouped queries the deal UI does not need, so it is off by default.
	"""
	pipelines = frappe.get_all(
		"CRM Pipeline",
		fields=["name", "description", "is_default", "disabled", "position"],
		order_by="position asc, name asc",
	)

	stages = frappe.get_all(
		"CRM Deal Status",
		fields=["name", "pipeline", "color", "type", "probability", "position"],
		order_by="position asc, name asc",
	)

	with_counts = frappe.utils.cint(with_counts)
	pipeline_counts = _deal_counts("pipeline") if with_counts else {}
	stage_counts = _deal_counts("status") if with_counts else {}

	stages_by_pipeline = {}
	for stage in stages:
		if with_counts:
			stage["deal_count"] = stage_counts.get(stage.name, 0)
		stages_by_pipeline.setdefault(stage.pipeline, []).append(stage)

	for pipeline in pipelines:
		if with_counts:
			pipeline["deal_count"] = pipeline_counts.get(pipeline.name, 0)
		pipeline["stages"] = stages_by_pipeline.get(pipeline.name, [])

	# stages left behind by an older install (no pipeline yet) must stay reachable
	orphans = stages_by_pipeline.get(None, []) + stages_by_pipeline.get("", [])
	if orphans:
		pipelines.append(
			frappe._dict(
				{
					"name": "",
					"description": _("Stages that do not belong to a pipeline yet"),
					"is_default": 0,
					"disabled": 0,
					"position": 999,
					"deal_count": 0,
					"stages": orphans,
				}
			)
		)

	return pipelines


@frappe.whitelist(methods=["POST"])
def create_pipeline(
	pipeline_name: str, description: str | None = None, stages: list | str | None = None
) -> dict:
	"""Create a pipeline. Without stages it gets the standard set."""
	_check_manager()

	pipeline_name = (pipeline_name or "").strip()
	if not pipeline_name:
		frappe.throw(_("Pipeline name is required"))

	if frappe.db.exists("CRM Pipeline", pipeline_name):
		frappe.throw(_("A pipeline named {0} already exists").format(frappe.bold(pipeline_name)))

	doc = frappe.new_doc("CRM Pipeline")
	doc.pipeline_name = pipeline_name
	doc.description = description
	doc.insert()

	given = _parse(stages, None)
	if given:
		new_stages = [dict(stage) for stage in given]
	else:
		# the standard set, with names that do not clash with existing stages
		new_stages = [
			{**stage, "stage": _unique_stage_name(stage["stage"], doc.name)} for stage in DEFAULT_STAGES
		]

	save_stages(doc.name, new_stages)

	return get_pipeline(doc.name)


def _unique_stage_name(label: str, pipeline: str) -> str:
	"""Stage names are unique site-wide, so auto-created stages get a suffix if taken."""
	if not frappe.db.exists("CRM Deal Status", label):
		return label

	candidate = f"{label} ({pipeline})"
	suffix = 1
	while frappe.db.exists("CRM Deal Status", candidate):
		suffix += 1
		candidate = f"{label} ({pipeline}) {suffix}"

	return candidate


@frappe.whitelist()
def get_pipeline(name: str) -> dict:
	pipeline = frappe.get_doc("CRM Pipeline", name)
	pipeline.check_permission("read")
	return {
		"name": pipeline.name,
		"description": pipeline.description,
		"is_default": pipeline.is_default,
		"disabled": pipeline.disabled,
		"position": pipeline.position,
		"stages": get_pipeline_stages(pipeline.name, only_names=False),
	}


@frappe.whitelist(methods=["POST"])
def update_pipeline(
	name: str,
	pipeline_name: str | None = None,
	description: str | None = None,
	disabled: bool | int | None = None,
) -> dict:
	"""Rename a pipeline and/or update its details."""
	_check_manager()

	doc = frappe.get_doc("CRM Pipeline", name)

	if description is not None:
		doc.description = description
	if disabled is not None:
		doc.disabled = int(bool(disabled))
	doc.save()

	pipeline_name = (pipeline_name or "").strip()
	if pipeline_name and pipeline_name != doc.name:
		if frappe.db.exists("CRM Pipeline", pipeline_name):
			frappe.throw(_("A pipeline named {0} already exists").format(frappe.bold(pipeline_name)))
		name = frappe.rename_doc("CRM Pipeline", doc.name, pipeline_name)

	return get_pipeline(name)


@frappe.whitelist(methods=["POST"])
def set_default_pipeline(name: str) -> None:
	"""New deals without a pipeline land in this one."""
	_check_manager()

	doc = frappe.get_doc("CRM Pipeline", name)
	if doc.disabled:
		frappe.throw(_("A disabled pipeline cannot be the default one"))
	doc.is_default = 1
	doc.save()


@frappe.whitelist(methods=["POST"])
def save_stages(pipeline: str, stages: list | str) -> list[dict]:
	"""Create, rename, recolour and reorder the stages of one pipeline.

	`stages` is the full ordered list of the pipeline's stages. Each entry:
	`{"name": <existing stage or empty>, "stage": <label>, "color", "type", "probability"}`.
	Stages missing from the list are left alone -- deleting one needs `delete_stage`,
	which knows what to do with the deals inside it.
	"""
	_check_manager()

	if not frappe.db.exists("CRM Pipeline", pipeline):
		frappe.throw(_("Pipeline {0} does not exist").format(frappe.bold(pipeline)))

	stages = _parse(stages, [])
	if not stages:
		frappe.throw(_("A pipeline needs at least one stage"))

	labels = [(stage.get("stage") or stage.get("name") or "").strip() for stage in stages]
	if not all(labels):
		frappe.throw(_("Every stage needs a name"))
	if len(set(labels)) != len(labels):
		frappe.throw(_("Two stages of the same pipeline cannot share a name"))

	for position, stage in enumerate(stages, start=1):
		label = (stage.get("stage") or stage.get("name") or "").strip()
		existing = (stage.get("name") or "").strip()

		is_new = not (existing and frappe.db.exists("CRM Deal Status", existing))
		if is_new:
			_assert_stage_name_free(label)
			doc = frappe.new_doc("CRM Deal Status")
			doc.deal_status = label
		else:
			doc = frappe.get_doc("CRM Deal Status", existing)

		doc.pipeline = pipeline
		doc.position = position
		if stage.get("color"):
			doc.color = stage["color"]
		if stage.get("type"):
			doc.type = stage["type"]
		if stage.get("probability") is not None:
			doc.probability = stage["probability"]

		if is_new:
			doc.insert()
		else:
			doc.save()

		if doc.name != label:
			_assert_stage_name_free(label)
			frappe.rename_doc("CRM Deal Status", doc.name, label)

	return get_pipeline_stages(pipeline, only_names=False)


def _assert_stage_name_free(label: str) -> None:
	if not frappe.db.exists("CRM Deal Status", label):
		return

	owner = frappe.db.get_value("CRM Deal Status", label, "pipeline")
	frappe.throw(
		_("A stage named {0} already exists in the pipeline {1}. Stage names must be unique.").format(
			frappe.bold(label), frappe.bold(owner or _("(none)"))
		)
	)


@frappe.whitelist(methods=["POST"])
def delete_stage(stage: str, move_deals_to: str | None = None) -> None:
	"""Delete a stage, moving whatever deals sit in it to another stage first."""
	_check_manager()

	doc = frappe.get_doc("CRM Deal Status", stage)
	siblings = [s for s in get_pipeline_stages(doc.pipeline) if s != stage]
	if doc.pipeline and not siblings:
		frappe.throw(_("A pipeline needs at least one stage"))

	deals = frappe.db.count("CRM Deal", {"status": stage})
	if deals:
		move_deals_to = move_deals_to or (siblings[0] if siblings else None)
		if not move_deals_to:
			frappe.throw(_("{0} deals are in this stage. Pick a stage to move them to.").format(deals))
		_move_deals({"status": stage}, move_deals_to)

	frappe.delete_doc("CRM Deal Status", stage)


@frappe.whitelist(methods=["POST"])
def delete_pipeline(name: str, move_deals_to: str | None = None) -> None:
	"""Delete a pipeline. Its deals move to another pipeline, its stages go with it."""
	_check_manager()

	doc = frappe.get_doc("CRM Pipeline", name)
	if doc.is_default:
		frappe.throw(_("The default pipeline cannot be deleted"))

	deals = frappe.db.count("CRM Deal", {"pipeline": name})
	if deals:
		target_pipeline = move_deals_to or get_default_pipeline()
		target_stage = get_first_stage(target_pipeline)
		if not target_stage:
			frappe.throw(_("{0} deals are in this pipeline. Pick a pipeline to move them to.").format(deals))
		_move_deals({"pipeline": name}, target_stage)

	frappe.delete_doc("CRM Pipeline", name)


def _move_deals(filters: dict, stage: str) -> None:
	"""Bulk-move deals to another stage.

	Written straight to the database: moving a whole stage is a settings action on
	possibly thousands of deals, so it does not run the deal's save hooks (no status
	change log entries, no SLA recalculation) the way a per-deal move does.
	"""
	pipeline = frappe.db.get_value("CRM Deal Status", stage, "pipeline")
	frappe.db.set_value("CRM Deal", filters, {"status": stage, "pipeline": pipeline})
