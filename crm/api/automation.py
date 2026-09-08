import json

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from crm.automation.engine import (
	STEP_TYPES,
	TRIGGER_EVENTS,
	ensure_step_ids,
	parse_json,
	program_nodes,
	validate_steps,
)
from crm.utils import count_field

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage automations"), frappe.PermissionError)


@frappe.whitelist()
def list_automations() -> list[dict]:
	automations = frappe.get_list(
		"CRM Automation",
		fields=["name", "title", "enabled", "trigger_event", "description", "modified"],
		order_by="modified desc",
	)
	counts = dict(
		frappe.get_all(
			"CRM Automation Enrollment",
			fields=["automation", count_field()],
			group_by="automation",
			as_list=True,
		)
	)
	active = dict(
		frappe.get_all(
			"CRM Automation Enrollment",
			filters={"status": ["in", ["Active", "Waiting"]]},
			fields=["automation", count_field()],
			group_by="automation",
			as_list=True,
		)
	)
	trigger = frappe.qb.DocType("CRM Automation Trigger")
	events: dict[str, list[str]] = {}
	for row in (
		frappe.qb.from_(trigger)
		.select(trigger.parent, trigger.trigger_event)
		.where(trigger.parenttype == "CRM Automation")
		.orderby(trigger.parent)
		.orderby(trigger.idx)
	).run(as_dict=True):
		events.setdefault(row.parent, []).append(row.trigger_event)
	for row in automations:
		row["enrolled_count"] = counts.get(row.name, 0)
		row["active_count"] = active.get(row.name, 0)
		row["triggers"] = events.get(row.name) or [row.trigger_event]
	return automations


@frappe.whitelist()
def get_automation(name: str) -> dict:
	doc = frappe.get_doc("CRM Automation", name)
	doc.check_permission("read")
	return {
		"name": doc.name,
		"title": doc.title,
		"enabled": doc.enabled,
		"trigger_event": doc.trigger_event,
		"triggers": [
			{
				"event": row.trigger_event,
				"config": parse_json(row.trigger_config) or {},
				"condition": parse_json(row.trigger_condition),
			}
			for row in doc.triggers
		],
		"trigger_condition": parse_json(doc.trigger_condition),
		"allow_reenrollment": doc.allow_reenrollment,
		"exit_on_reply": doc.exit_on_reply,
		"description": doc.description or "",
		"steps": parse_json(doc.steps) or [],
		"trigger_config": parse_json(doc.trigger_config),
		"webhook_key": doc.webhook_key or "",
		"time_window_enabled": doc.time_window_enabled,
		"window_start": str(doc.window_start or ""),
		"window_end": str(doc.window_end or ""),
		"window_days": parse_json(doc.window_days) or [],
	}


@frappe.whitelist(methods=["POST"])
def save_automation(automation: dict | str, name: str | None = None) -> dict:
	"""Create or update an automation from the visual builder payload."""
	_check_manager()
	if isinstance(automation, str):
		automation = json.loads(automation)

	steps = ensure_step_ids(automation.get("steps") or [])
	validate_steps(steps)

	values = {
		"title": (automation.get("title") or "").strip(),
		"trigger_event": automation.get("trigger_event"),
		"trigger_condition": json.dumps(automation.get("trigger_condition") or None),
		"allow_reenrollment": 1 if automation.get("allow_reenrollment") else 0,
		"exit_on_reply": 1 if automation.get("exit_on_reply") else 0,
		"description": automation.get("description") or "",
		"steps": json.dumps(steps),
		"trigger_config": json.dumps(automation.get("trigger_config") or None),
		"time_window_enabled": 1 if automation.get("time_window_enabled") else 0,
		"window_start": automation.get("window_start") or None,
		"window_end": automation.get("window_end") or None,
		"window_days": json.dumps(automation.get("window_days") or []),
	}
	if not values["title"]:
		frappe.throw(_("Title is required"))

	# what the caller sends is what the automation listens to; a payload with the
	# old single trigger becomes one row, so the two shapes stay interchangeable
	rows = _trigger_rows(automation.get("triggers"))
	if not rows and automation.get("trigger_event"):
		rows = _trigger_rows(
			[
				{
					"event": automation.get("trigger_event"),
					"config": automation.get("trigger_config"),
					"condition": automation.get("trigger_condition"),
				}
			]
		)
	if not rows:
		frappe.throw(_("An automation needs at least one trigger"))
	values["triggers"] = rows
	values["trigger_event"] = rows[0]["trigger_event"]
	values["trigger_config"] = rows[0]["trigger_config"]
	values["trigger_condition"] = rows[0]["trigger_condition"]

	if name:
		doc = frappe.get_doc("CRM Automation", name)
		doc.update(values)
		doc.save()
	else:
		# the DocType is named after the title, so a clash needs to say so plainly
		if frappe.db.exists("CRM Automation", values["title"]):
			frappe.throw(_("An automation called «{0}» already exists").format(values["title"]))
		doc = frappe.get_doc({"doctype": "CRM Automation", "enabled": 0, **values})
		doc.insert()
	return get_automation(doc.name)


def _trigger_rows(triggers) -> list[dict]:
	"""Builder payload → rows of the triggers table, one per event it listens to."""
	rows = []
	for entry in triggers or []:
		event = entry.get("event") or entry.get("trigger_event")
		if event not in TRIGGER_EVENTS:
			frappe.throw(_("Unknown trigger: {0}").format(event))
		rows.append(
			{
				"trigger_event": event,
				"trigger_config": json.dumps(entry.get("config") or None),
				"trigger_condition": json.dumps(entry.get("condition") or None),
			}
		)
	return rows


@frappe.whitelist(methods=["POST"])
def toggle_automation(name: str, enabled: bool) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Automation", name)
	doc.enabled = 1 if frappe.utils.sbool(enabled) else 0
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist(methods=["POST"])
def delete_automation(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Automation", name)


@frappe.whitelist()
def get_enrollments(automation: str, status: str | None = None, limit: int = 50) -> list[dict]:
	filters = {"automation": automation}
	if status and status != "All":
		filters["status"] = status
	rows = frappe.get_list(
		"CRM Automation Enrollment",
		filters=filters,
		fields=[
			"name",
			"reference_doctype",
			"reference_name",
			"status",
			"current_step",
			"wait_until",
			"modified",
		],
		order_by="modified desc",
		page_length=min(int(limit), 200),
	)
	program = parse_json(frappe.db.get_value("CRM Automation", automation, "compiled_steps")) or []
	nodes = program_nodes(program)
	titles = _reference_titles(rows)
	for row in rows:
		row["node"] = nodes.get(row.current_step)
		row["title"] = titles.get((row.reference_doctype, row.reference_name)) or row.reference_name
	return rows


def _reference_titles(rows: list[dict]) -> dict:
	"""Human names for the lead/deal behind each enrollment, one query per doctype."""
	titles: dict = {}
	by_doctype: dict[str, list[str]] = {}
	for row in rows:
		by_doctype.setdefault(row["reference_doctype"], []).append(row["reference_name"])
	for doctype, names in by_doctype.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		title_field = frappe.get_meta(doctype).get_title_field()
		fields = ["name"] + ([title_field] if title_field and title_field != "name" else [])
		for record in frappe.get_all(doctype, filters={"name": ["in", names]}, fields=fields, limit=200):
			titles[(doctype, record["name"])] = record.get(title_field) or record["name"]
	return titles


# fieldtypes a condition or an "update field" step can sensibly work with
BUILDER_FIELDTYPES = {
	"Data",
	"Select",
	"Link",
	"Dynamic Link",
	"Autocomplete",
	"Int",
	"Float",
	"Currency",
	"Percent",
	"Check",
	"Date",
	"Datetime",
	"Time",
	"Duration",
	"Rating",
	"Phone",
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Read Only",
}

# always available on every record, whatever the DocType declares
STANDARD_FIELDS = (
	{"fieldname": "name", "label": "ID", "fieldtype": "Data"},
	{"fieldname": "owner", "label": "Created By", "fieldtype": "Link", "options": "User"},
	{"fieldname": "creation", "label": "Created On", "fieldtype": "Datetime"},
	{"fieldname": "modified", "label": "Last Modified", "fieldtype": "Datetime"},
	{"fieldname": "_user_tags", "label": "Tags", "fieldtype": "Data"},
)


def _builder_fields(doctype: str) -> list[dict]:
	"""The fields the condition builder and the update-field step offer, with their options."""
	if not frappe.db.exists("DocType", doctype):
		return []
	fields = []
	for field in frappe.get_meta(doctype).fields:
		if field.fieldtype not in BUILDER_FIELDTYPES or field.hidden:
			continue
		fields.append(
			{
				"fieldname": field.fieldname,
				"label": _(field.label or field.fieldname),
				"fieldtype": field.fieldtype,
				"options": field.options or "",
			}
		)
	fields.sort(key=lambda f: f["label"].lower())
	return [{**f, "label": _(f["label"]), "options": f.get("options", "")} for f in STANDARD_FIELDS] + fields


@frappe.whitelist()
def get_builder_meta() -> dict:
	"""Everything the visual builder needs: palette, triggers, fields, templates, people."""
	from crm.automation.engine import CONDITION_OPERATORS, GOAL_EVENTS, TRIGGER_EVENTS, WAIT_MODES

	email_templates = []
	if frappe.db.exists("DocType", "Email Template"):
		email_templates = frappe.get_all(
			"Email Template", fields=["name", "subject"], limit=100, order_by="name asc"
		)
	whatsapp_templates = []
	if frappe.db.exists("DocType", "WhatsApp Templates"):
		whatsapp_templates = frappe.get_all("WhatsApp Templates", pluck="name", limit=100)
	sales_users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Sales User", "Sales Manager"]], "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	users = frappe.get_all(
		"User",
		filters={"name": ["in", sorted(set(sales_users))], "enabled": 1},
		fields=["name", "full_name", "user_image"],
		limit=200,
	)
	return {
		"step_types": list(STEP_TYPES),
		"trigger_events": TRIGGER_EVENTS,
		"condition_operators": list(CONDITION_OPERATORS),
		"goal_events": list(GOAL_EVENTS),
		"wait_modes": list(WAIT_MODES),
		"email_templates": email_templates,
		"whatsapp_templates": whatsapp_templates,
		"tracked_links": frappe.get_all("CRM Tracked Link", pluck="name", limit=100),
		"automations": frappe.get_all(
			"CRM Automation", fields=["name", "title"], limit=200, order_by="title asc"
		),
		"users": users,
		"tags": frappe.get_all("Tag", pluck="name", limit=200, order_by="name asc"),
		"lead_statuses": frappe.get_all("CRM Lead Status", pluck="name", order_by="position asc"),
		"deal_statuses": frappe.get_all("CRM Deal Status", pluck="name", order_by="position asc"),
		"fields": {
			"CRM Lead": _builder_fields("CRM Lead"),
			"CRM Deal": _builder_fields("CRM Deal"),
		},
	}


@frappe.whitelist(methods=["POST"])
def save_settings(name: str, settings: dict | str) -> None:
	"""Workflow-level settings panel (time window, trigger config)."""
	_check_manager()
	if isinstance(settings, str):
		settings = json.loads(settings)
	doc = frappe.get_doc("CRM Automation", name)
	for field in (
		"trigger_config",
		"time_window_enabled",
		"window_start",
		"window_end",
		"window_days",
	):
		if field in settings:
			value = settings[field]
			if field in ("trigger_config", "window_days") and not isinstance(value, str):
				value = json.dumps(value)
			doc.set(field, value)
	doc.save()


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=300, seconds=60 * 60)
def inbound_webhook(automation: str, key: str) -> dict:
	"""GHL 'Inbound Webhook' trigger: external systems POST here to enroll a contact.

	URL: /api/method/crm.api.automation.inbound_webhook?automation=<name>&key=<webhook_key>
	Body: JSON with at least email or mobile_no; extra keys become the event payload.
	"""
	import hmac as hmac_mod

	doc = frappe.get_doc("CRM Automation", automation)
	trigger = next((row for row in doc.triggers if row.trigger_event == "Inbound Webhook"), None)
	listens = bool(trigger) or doc.trigger_event == "Inbound Webhook"
	if (
		not listens
		or not doc.enabled
		or not doc.webhook_key
		or not hmac_mod.compare_digest(str(key), str(doc.webhook_key))
	):
		frappe.throw(_("Invalid webhook"), frappe.PermissionError)

	payload = {}
	if frappe.request and frappe.request.data:
		try:
			payload = json.loads(frappe.request.data)
		except ValueError:
			payload = {}
	payload = {
		**{k: v for k, v in frappe.local.form_dict.items() if k not in ("automation", "key", "cmd")},
		**payload,
	}

	email = (payload.get("email") or "").strip()
	phone = (payload.get("mobile_no") or payload.get("phone") or "").strip()
	if not email and not phone:
		frappe.throw(_("Payload must contain email or mobile_no"))

	# the person, whether or not they already have a deal: excluding the ones
	# that had one is what made a second record for a customer who comes back
	from crm.api.lead import find_person

	lead = find_person(email=email, phone=phone)
	if not lead:
		from crm.api.form import _default_status

		lead_doc = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": payload.get("first_name") or email or phone,
				"last_name": payload.get("last_name") or "",
				"email": email,
				"mobile_no": phone,
				"status": _default_status("CRM Lead"),
			}
		)
		lead_doc.insert(ignore_permissions=True)
		lead = lead_doc.name

	from crm.automation.engine import enroll

	# only this automation: the key in the URL is its own, not everyone's
	enroll(automation, "CRM Lead", lead, payload, trigger_row=trigger)
	return {"lead": lead}


@frappe.whitelist(methods=["POST"])
def duplicate_automation(name: str) -> dict:
	"""Copy of an automation, always as a draft, with its own step ids and webhook key."""
	_check_manager()
	source = frappe.get_doc("CRM Automation", name)
	copy = frappe.copy_doc(source)
	copy.title = _free_title(_("{0} (copy)").format(source.title))
	copy.enabled = 0
	copy.webhook_key = None
	copy.steps = json.dumps(_strip_step_ids(parse_json(source.steps) or []))
	copy.insert()
	return {"name": copy.name, "title": copy.title}


def _free_title(title: str) -> str:
	"""Titles are the names here, so the second copy has to be «… (copy) 2»."""
	candidate = title
	suffix = 1
	while frappe.db.exists("CRM Automation", candidate):
		suffix += 1
		candidate = f"{title} {suffix}"
	return candidate


def _strip_step_ids(steps: list) -> list:
	"""Drop node ids so a copy starts with fresh ones — statistics do not travel."""
	for step in steps or []:
		if not isinstance(step, dict):
			continue
		step.pop("id", None)
		for branch in step.get("branches") or []:
			branch.pop("id", None)
			_strip_step_ids(branch.get("steps") or [])
		_strip_step_ids(step.get("else_steps") or [])
		for path in step.get("paths") or []:
			path.pop("id", None)
			_strip_step_ids(path.get("steps") or [])
	return steps


@frappe.whitelist()
def get_step_stats(name: str) -> dict:
	"""Per-node counters for the canvas: what ran, what failed, who is sitting where."""
	from frappe.query_builder.functions import Count

	doc = frappe.get_doc("CRM Automation", name)
	doc.check_permission("read")
	nodes = program_nodes(parse_json(doc.compiled_steps) or [])

	def bucket(node: str) -> dict:
		return stats.setdefault(node, {"success": 0, "failed": 0, "skipped": 0, "here": 0})

	stats: dict[str, dict] = {}
	log = frappe.qb.DocType("CRM Automation Step Log")
	enrollment = frappe.qb.DocType("CRM Automation Enrollment")
	rows = (
		frappe.qb.from_(log)
		.join(enrollment)
		.on(log.parent == enrollment.name)
		.select(log.step_index, log.status, Count(log.name).as_("total"))
		.where(enrollment.automation == name)
		.groupby(log.step_index, log.status)
	).run(as_dict=True)
	for row in rows:
		node = nodes.get(row.step_index)
		if not node:
			continue
		key = (row.status or "").lower()
		if key in bucket(node):
			bucket(node)[key] += row.total

	for row in frappe.get_all(
		"CRM Automation Enrollment",
		filters={"automation": name, "status": ["in", ["Active", "Waiting"]]},
		fields=["current_step", count_field()],
		group_by="current_step",
	):
		node = nodes.get(row.current_step)
		if node:
			bucket(node)["here"] += row.total

	totals = dict(
		frappe.get_all(
			"CRM Automation Enrollment",
			filters={"automation": name},
			fields=["status", count_field()],
			group_by="status",
			as_list=True,
		)
	)
	return {"nodes": stats, "totals": totals}


@frappe.whitelist()
def get_enrollment_detail(name: str) -> dict:
	"""One enrollment with its step log, each entry mapped back to a builder node."""
	enrollment = frappe.get_doc("CRM Automation Enrollment", name)
	enrollment.check_permission("read")
	program = parse_json(frappe.db.get_value("CRM Automation", enrollment.automation, "compiled_steps")) or []
	nodes = program_nodes(program)
	return {
		"name": enrollment.name,
		"automation": enrollment.automation,
		"status": enrollment.status,
		"reference_doctype": enrollment.reference_doctype,
		"reference_name": enrollment.reference_name,
		"wait_until": enrollment.wait_until,
		"current_step": enrollment.current_step,
		"current_node": nodes.get(enrollment.current_step),
		"logs": [
			{
				"step_index": row.step_index,
				"node": nodes.get(row.step_index),
				"action": row.action,
				"status": row.status,
				"detail": row.detail,
				"creation": row.creation,
			}
			for row in enrollment.logs
		],
	}


@frappe.whitelist(methods=["POST"])
def simulate_automation(
	reference_doctype: str,
	reference_name: str,
	steps: list | str | None = None,
	name: str | None = None,
) -> dict:
	"""Dry run of the flow (saved or still being edited) against one record.

	Nothing is sent, written or enrolled: conditions and branches are evaluated
	for real, messages are only rendered.
	"""
	from crm.automation.engine import simulate

	_check_manager()
	if reference_doctype not in ("CRM Lead", "CRM Deal"):
		frappe.throw(_("A preview runs against a lead or a deal"))
	if isinstance(steps, str):
		steps = json.loads(steps)
	if steps is None and name:
		steps = parse_json(frappe.db.get_value("CRM Automation", name, "steps")) or []
	steps = steps or []
	validate_steps(steps)

	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	ref_doc.check_permission("read")
	title_field = frappe.get_meta(reference_doctype).get_title_field()
	return {
		"record": {
			"doctype": reference_doctype,
			"name": ref_doc.name,
			"title": ref_doc.get(title_field) or ref_doc.name,
		},
		"trace": simulate(steps, ref_doc),
	}
