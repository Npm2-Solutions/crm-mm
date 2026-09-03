import json

import frappe

from crm.api.pipeline import create_default_pipeline


def execute():
	"""Give existing sites the pipeline they never had.

	Every deal stage joins the default pipeline, and every deal inherits the pipeline
	of its stage -- which is exactly the invariant CRM Deal.validate_status keeps from
	here on.
	"""
	pipeline = create_default_pipeline()

	frappe.db.sql(
		"update `tabCRM Deal Status` set pipeline = %s where coalesce(pipeline, '') = ''",
		(pipeline,),
	)

	frappe.db.sql(
		"""
		update `tabCRM Deal` deal
		inner join `tabCRM Deal Status` stage on stage.name = deal.status
		set deal.pipeline = stage.pipeline
		where coalesce(deal.pipeline, '') = ''
		"""
	)

	add_pipeline_quick_filter()
	add_pipeline_to_quick_entry()


def add_pipeline_quick_filter():
	"""Same quick filter new installs get, without dropping the ones already there."""
	name = frappe.db.exists("CRM Global Settings", {"dt": "CRM Deal"})
	if not name:
		return

	doc = frappe.get_doc("CRM Global Settings", name)
	filters = json.loads(doc.json or "[]")
	if "pipeline" in filters:
		return

	position = filters.index("status") if "status" in filters else len(filters)
	filters.insert(position, "pipeline")
	doc.json = json.dumps(filters)
	doc.save(ignore_permissions=True)


def add_pipeline_to_quick_entry():
	"""Show the pipeline next to the stage in the create-deal modal."""
	if not frappe.db.exists("CRM Fields Layout", "CRM Deal-Quick Entry"):
		return

	doc = frappe.get_doc("CRM Fields Layout", "CRM Deal-Quick Entry")
	layout = json.loads(doc.layout) if doc.layout else []
	# layout is either a plain list of sections or a list of tabs with sections
	has_tabs = any("sections" in item for item in layout)
	sections = [section for tab in layout for section in tab.get("sections", [])] if has_tabs else layout

	columns = [column for section in sections for column in section.get("columns") or []]
	fieldnames = [
		(field.get("fieldname") or field.get("name")) if isinstance(field, dict) else field
		for column in columns
		for field in column.get("fields") or []
	]
	if "pipeline" in fieldnames or "status" not in fieldnames:
		return

	for column in columns:
		fields = column.get("fields") or []
		names = [
			(field.get("fieldname") or field.get("name")) if isinstance(field, dict) else field
			for field in fields
		]
		if "status" in names:
			fields.insert(names.index("status"), "pipeline")
			break

	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)
