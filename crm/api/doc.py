# Modifications copyright (c) 2026, NPM2 Solutions Srl
import json

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.desk.form.assign_to import set_status
from frappe.model import no_value_fields
from frappe.model.delete_doc import get_dynamic_linked_docs, get_linked_docs
from frappe.model.document import get_controller
from frappe.utils import make_filter_tuple
from pypika import Criterion

from crm.api.views import get_views
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script
from crm.liste.campi import della_lista
from crm.liste.regole import nome_della_colonna
from crm.utils import get_kanban_column_options, is_frappe_version

COUNT_NAME = (
	{"COUNT": "name", "as": "total_count"}
	if is_frappe_version("16", above=True)
	else "count(name) as total_count"
)

# The list pages that show quick filters (ViewControls.vue). Changing them writes a
# Property Setter on the doctype, so the endpoint reaches these and nothing else.
QUICK_FILTER_DOCTYPES = (
	"CRM Lead",
	"CRM Deal",
	"Contact",
	"CRM Organization",
	"CRM Task",
	"CRM Call Log",
	"FCRM Note",
)


@frappe.whitelist()
def sort_options(doctype: str):
	# what a list offers to sort by, filter by, group by, add as a column: one
	# rule for all (crm.liste.regole), each field once and in the reader's words
	return [{**campo, "value": campo["fieldname"]} for campo in della_lista(doctype, "ordine")]


@frappe.whitelist()
def get_filterable_fields(doctype: str):
	c = get_controller(doctype)
	restricted_fields = []
	if hasattr(c, "get_non_filterable_fields"):
		restricted_fields = c.get_non_filterable_fields()

	return [
		{**campo, "name": campo["fieldname"], "value": campo["fieldname"]}
		for campo in della_lista(doctype, "filtro", togli=restricted_fields)
	]


@frappe.whitelist()
def get_group_by_fields(doctype: str):
	return della_lista(doctype, "gruppo")


@frappe.whitelist()
def get_list_fields(doctype: str):
	"""What a list offers as a column, on a board's card, as a quick filter."""
	return [{**campo, "value": campo["fieldname"]} for campo in della_lista(doctype, "colonna")]


@frappe.whitelist()
def get_quick_filters(doctype: str, cached: bool = True):
	meta = frappe.get_meta(doctype, cached)
	quick_filters = []

	if global_settings := frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}):
		_quick_filters = frappe.db.get_value("CRM Global Settings", global_settings, "json")
		_quick_filters = json.loads(_quick_filters) or []

		fields = []

		for filter in _quick_filters:
			if filter == "name":
				fields.append({"label": "Name", "fieldname": "name", "fieldtype": "Data"})
			else:
				field = next((f for f in meta.fields if f.fieldname == filter), None)
				if field:
					fields.append(field)

	else:
		fields = [field for field in meta.fields if field.in_standard_filter]

	for field in fields:
		options = field.get("options")
		if field.get("fieldtype") == "Select" and options and isinstance(options, str):
			options = options.split("\n")
			# a choice reads in the user's language; the value stays the stored one
			options = [{"label": _(option) if option else "", "value": option} for option in options]
			if not any([not option.get("value") for option in options]):
				options.insert(0, {"label": "", "value": ""})
		quick_filters.append(
			{
				"label": _(field.get("label")),
				"fieldname": field.get("fieldname"),
				"fieldtype": field.get("fieldtype"),
				"options": options,
			}
		)

	return quick_filters


@frappe.whitelist()
def update_quick_filters(quick_filters: str, old_filters: str, doctype: str):
	from crm.permissions.livelli import verifica

	verifica("viste.configura", messaggio=_("Only sales managers can change the quick filters"))
	if doctype not in QUICK_FILTER_DOCTYPES:
		frappe.throw(_("Quick filters can't be changed on {0}").format(doctype), frappe.PermissionError)

	quick_filters = json.loads(quick_filters)
	old_filters = json.loads(old_filters)

	new_filters = [filter for filter in quick_filters if filter not in old_filters]
	removed_filters = [filter for filter in old_filters if filter not in quick_filters]

	# update or create global quick filter settings
	create_update_global_settings(doctype, quick_filters)

	# remove old filters
	for filter in removed_filters:
		update_in_standard_filter(filter, doctype, 0)

	# add new filters
	for filter in new_filters:
		update_in_standard_filter(filter, doctype, 1)


def create_update_global_settings(doctype, quick_filters):
	if global_settings := frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}):
		frappe.db.set_value("CRM Global Settings", global_settings, "json", json.dumps(quick_filters))
	else:
		# create CRM Global Settings doc
		doc = frappe.new_doc("CRM Global Settings")
		doc.dt = doctype
		doc.type = "Quick Filters"
		doc.json = json.dumps(quick_filters)
		doc.insert()


def update_in_standard_filter(fieldname, doctype, value):
	if property_name := frappe.db.exists(
		"Property Setter",
		{"doc_type": doctype, "field_name": fieldname, "property": "in_standard_filter"},
	):
		frappe.db.set_value("Property Setter", property_name, "value", value)
	else:
		make_property_setter(
			doctype,
			fieldname,
			"in_standard_filter",
			value,
			"Check",
			validate_fields_for_doctype=False,
		)


@frappe.whitelist()
def get_data(
	doctype: str,
	filters: dict,
	order_by: str,
	page_length: int = 20,
	page_length_count: int = 20,
	column_field: str | None = None,
	title_field: str | None = None,
	columns: str | list | None = None,
	rows: str | list | None = None,
	kanban_columns: str | list | None = None,
	kanban_fields: str | list | None = None,
	view: str | dict | None = None,
	default_filters: dict | None = None,
):
	custom_view = False
	filters = frappe._dict(filters)
	rows = frappe.parse_json(rows or "[]")
	columns = frappe.parse_json(columns or "[]")
	kanban_fields = frappe.parse_json(kanban_fields or "[]")
	kanban_columns = frappe.parse_json(kanban_columns or "[]")

	custom_view_name = view.get("custom_view_name") if view else None
	view_type = view.get("view_type") if view else None
	group_by_field = view.get("group_by_field") if view else None

	for key in filters:
		value = filters[key]
		if isinstance(value, list):
			if "@me" in value:
				value[value.index("@me")] = frappe.session.user
			elif "%@me%" in value:
				index = [i for i, v in enumerate(value) if v == "%@me%"]
				for i in index:
					value[i] = "%" + frappe.session.user + "%"
		elif value == "@me":
			filters[key] = frappe.session.user

	if default_filters:
		default_filters = frappe.parse_json(default_filters)
		filters.update(default_filters)

	is_default = True
	data = []
	_list = get_controller(doctype)
	default_rows = []
	if hasattr(_list, "default_list_data"):
		default_rows = _list.default_list_data().get("rows")

	meta = frappe.get_meta(doctype)

	if view_type != "kanban":
		if columns or rows:
			custom_view = True
			is_default = False
			columns = frappe.parse_json(columns)
			rows = frappe.parse_json(rows)

		if not columns:
			columns = [
				{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
				{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
			]

		if not rows:
			rows = ["name"]

		default_view_filters = {
			"dt": doctype,
			"type": view_type or "list",
			"is_standard": 1,
			"user": frappe.session.user,
		}

		if not custom_view and frappe.db.exists("CRM View Settings", default_view_filters):
			list_view_settings = frappe.get_doc("CRM View Settings", default_view_filters)
			columns = frappe.parse_json(list_view_settings.columns)
			rows = frappe.parse_json(list_view_settings.rows)
			is_default = False
		elif not custom_view or (is_default and hasattr(_list, "default_list_data")):
			rows = default_rows
			columns = _list.default_list_data().get("columns")

		# The columns the controller itself declares are shown even when their
		# field is hidden: Frappe core hides `Contact.full_name`, a computed field,
		# and dropping it left the contact list without a name column — each
		# contact known only by its email.
		declared = (
			{c.get("key") for c in _list.default_list_data().get("columns", [])}
			if hasattr(_list, "default_list_data")
			else set()
		)

		# check if rows has all keys from columns if not add them
		# iterate over a copy: the hidden ones are removed below, and removing from
		# the list being walked makes the loop skip whatever follows them
		for column in list(columns):
			if column.get("key") not in rows:
				rows.append(column.get("key"))
			column["label"] = _(nome_della_colonna(column.get("key"), column.get("label")))

			if column.get("key") == "_liked_by" and column.get("width") == "10rem":
				column["width"] = "50px"

			# remove column if column.hidden is True
			column_meta = meta.get_field(column.get("key"))
			if column_meta and column_meta.get("hidden") and column.get("key") not in declared:
				columns.remove(column)

		# check if rows has group_by_field if not add it
		if group_by_field and group_by_field not in rows:
			rows.append(group_by_field)

		data = (
			frappe.get_list(
				doctype,
				fields=rows,
				filters=filters,
				order_by=order_by,
				page_length=page_length,
			)
			or []
		)
		data = parse_list_data(data, doctype)

	if view_type == "kanban":
		if not rows:
			rows = default_rows

		if not kanban_columns and column_field:
			kanban_columns = get_kanban_column_options(doctype, column_field, filters)

		if not title_field:
			title_field = "name"
			if hasattr(_list, "default_kanban_settings"):
				title_field = _list.default_kanban_settings().get("title_field")

		if title_field not in rows:
			rows.append(title_field)

		if not kanban_fields:
			kanban_fields = ["name"]
			if hasattr(_list, "default_kanban_settings"):
				kanban_fields = json.loads(_list.default_kanban_settings().get("kanban_fields"))

		for field in kanban_fields:
			if field not in rows:
				rows.append(field)

		for kc in kanban_columns:
			# Start with base filters
			column_filters = []

			# Convert and add the main filters first
			if filters:
				base_filters = convert_filter_to_tuple(doctype, filters)
				column_filters.extend(base_filters)

			# Add the column-specific filter
			if column_field and kc.get("name"):
				column_filters.append([doctype, column_field, "=", kc.get("name")])

			order = kc.get("order")
			if kc.get("delete"):
				column_data = []
			else:
				page_length = kc.get("page_length", 20)

				if order:
					column_data = get_records_based_on_order(
						doctype, rows, column_filters, page_length, order
					)
				else:
					column_data = frappe.get_list(
						doctype,
						fields=rows,
						filters=column_filters,
						order_by=order_by,
						page_length=page_length,
					)

				all_count = frappe.get_list(
					doctype,
					filters=column_filters,
					fields=[COUNT_NAME],
				)[0].total_count

				kc["all_count"] = all_count
				kc["count"] = len(column_data)

			if order:
				column_data = sorted(
					column_data,
					key=lambda x: order.index(x.get("name")) if x.get("name") in order else len(order),
				)

			data.append({"column": kc, "fields": kanban_fields, "data": column_data})

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": _(field.label),
			"fieldtype": field.fieldtype,
			"fieldname": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "fieldtype": "Data", "fieldname": "name"},
		{"label": "Created On", "fieldtype": "Datetime", "fieldname": "creation"},
		{"label": "Last Modified", "fieldtype": "Datetime", "fieldname": "modified"},
		{
			"label": "Modified By",
			"fieldtype": "Link",
			"fieldname": "modified_by",
			"options": "User",
		},
		{"label": "Assigned To", "fieldtype": "Text", "fieldname": "_assign"},
		{"label": "Owner", "fieldtype": "Link", "fieldname": "owner", "options": "User"},
		{"label": "Like", "fieldtype": "Data", "fieldname": "_liked_by"},
	]

	for field in std_fields:
		if field.get("fieldname") not in rows:
			rows.append(field.get("fieldname"))
		if field not in fields:
			field["label"] = _(field["label"])
			fields.append(field)

	if not is_default and custom_view_name:
		is_default = frappe.db.get_value("CRM View Settings", custom_view_name, "load_default_columns")

	if group_by_field and view_type == "group_by":

		def get_options(type, options):
			if type == "Select":
				return [option for option in options.split("\n")]
			else:
				has_empty_values = any([not d.get(group_by_field) for d in data])
				options = list(set([d.get(group_by_field) for d in data]))
				options = [u for u in options if u]
				if has_empty_values:
					options.append("")

				if order_by and group_by_field in order_by:
					order_by_fields = order_by.split(",")
					order_by_fields = [
						(field.split(" ")[0], field.split(" ")[1]) for field in order_by_fields
					]
					if (group_by_field, "asc") in order_by_fields:
						options.sort()
					elif (group_by_field, "desc") in order_by_fields:
						options.sort(reverse=True)
				else:
					options.sort()
				return options

		# the groups' heading names the field as the list offered it
		offerti = {c["fieldname"]: c["label"] for c in della_lista(doctype, "gruppo")}
		for field in fields:
			if field.get("fieldname") == group_by_field:
				group_by_field = {
					"label": offerti.get(group_by_field) or field.get("label"),
					"fieldname": field.get("fieldname"),
					"fieldtype": field.get("fieldtype"),
					# what a link points at: a colleague's heading is their name
					"link_doctype": field.get("options") if field.get("fieldtype") == "Link" else None,
					"options": get_options(field.get("fieldtype"), field.get("options")),
				}

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"column_field": column_field,
		"title_field": title_field,
		"kanban_columns": kanban_columns,
		"kanban_fields": kanban_fields,
		"group_by_field": group_by_field,
		"page_length": page_length,
		"page_length_count": page_length_count,
		"is_default": is_default,
		"views": get_views(doctype),
		"total_count": frappe.get_list(doctype, filters=filters, fields=[COUNT_NAME])[0].total_count,
		"row_count": len(data),
		"form_script": get_form_script(doctype),
		"list_script": get_form_script(doctype, "List"),
		"view_type": view_type,
	}


def parse_list_data(data, doctype):
	_list = get_controller(doctype)
	if hasattr(_list, "parse_list_data"):
		data = _list.parse_list_data(data)
	return data


def convert_filter_to_tuple(doctype, filters):
	if isinstance(filters, dict):
		filters_items = filters.items()
		filters = []
		for key, value in filters_items:
			filters.append(make_filter_tuple(doctype, key, value))
	return filters


def get_records_based_on_order(doctype, rows, filters, page_length, order):
	records = []
	filters = convert_filter_to_tuple(doctype, filters)
	in_filters = filters.copy()
	in_filters.append([doctype, "name", "in", order[:page_length]])
	records = frappe.get_list(
		doctype,
		fields=rows,
		filters=in_filters,
		order_by="creation desc",
		page_length=page_length,
	)

	if len(records) < page_length:
		not_in_filters = filters.copy()
		not_in_filters.append([doctype, "name", "not in", order])
		remaining_records = frappe.get_list(
			doctype,
			fields=rows,
			filters=not_in_filters,
			order_by="creation desc",
			page_length=page_length - len(records),
		)
		for record in remaining_records:
			records.append(record)

	return records


@frappe.whitelist()
def get_doc_permissions(doctype: str, docname: str | int) -> dict:
	"""What the session may do with a document, the way the server will judge it.

	`frappe.client.get_doc_permissions` asks the controllers one general question,
	which they answer as a read, and gives the roles' answer for the rest: a level
	that sees a person but may not change it (doc 30) was offered fields and buttons
	it could not save. Each write is asked of the controllers too.
	"""
	doc = frappe.get_lazy_doc(doctype, docname)
	permissions = frappe.permissions.get_doc_permissions(doc)
	for ptype in ("write", "create", "delete", "share", "email"):
		if permissions.get(ptype):
			allowed = frappe.has_permission(doctype, ptype, doc)
			permissions[ptype] = int(allowed)
	return {"permissions": permissions}


@frappe.whitelist()
def remove_assignments(doctype: str, name: str, assignees: str | list):
	from crm.permissions.documenti import verifica_assegnazione

	verifica_assegnazione(doctype)
	assignees = frappe.parse_json(assignees)

	if not assignees:
		return

	# no ignore_permissions from the caller: cancelling an assignment also clears
	# lead_owner / deal_owner (crm.api.todo), which decides who sees the record
	for assign_to in assignees:
		set_status(doctype, name, todo=None, assign_to=assign_to, status="Cancelled")


@frappe.whitelist()
def get_assigned_users(doctype: str, name: str | int, default_assigned_to: str | None = None):
	frappe.has_permission(doctype, "read", name, throw=True)

	users = assigned_users_of(doctype, name)

	# if users is empty, add default_assigned_to
	if not users and default_assigned_to:
		users = [default_assigned_to]
	return users


def assigned_users_of(doctype: str, name: str | int) -> list[str]:
	"""Who a document is assigned to, with no permission check.

	For the server's own callers: an inbound WhatsApp or SMS arrives as Guest and
	still has to reach whoever the lead is with.
	"""
	assigned_users = frappe.get_all(
		"ToDo",
		fields=["allocated_to"],
		filters={
			"reference_type": doctype,
			"reference_name": name,
			"status": ("not in", ("Closed", "Cancelled")),
		},
		pluck="allocated_to",
	)
	return list(set(assigned_users))


@frappe.whitelist()
def get_fields(doctype: str, allow_all_fieldtypes: bool = False):
	not_allowed_fieldtypes = [*list(frappe.model.no_value_fields), "Read Only"]
	if allow_all_fieldtypes:
		not_allowed_fieldtypes = []
	meta = frappe.get_meta(doctype)
	# what sits on a permission level the user cannot read is not drawn: its value
	# never reaches them, and an empty field they cannot fill is a question nobody
	# can answer (the agency's keys on a centre's settings page)
	# (a child table has no permissions of its own: its parent's decide, elsewhere)
	alti = any((field.permlevel or 0) > 0 for field in meta.fields)
	leggibili = (
		set(meta.get_permlevel_access("read"))
		if alti and not meta.istable and frappe.session.user != "Administrator"
		else None
	)

	_fields = []

	for field in meta.fields:
		if leggibili is not None and (field.permlevel or 0) > 0 and field.permlevel not in leggibili:
			continue
		if field.fieldtype not in not_allowed_fieldtypes and field.fieldname:
			_fields.append(field)

	for adatta in _adattatori:
		_fields = adatta(doctype, _fields)
	return _fields


#: What a module changes in its own DocTypes' fields when a screen draws them:
#: invoicing's code selects offer their choices in words (`crm.invoicing.scelte`).
#: Each one is called with every DocType and leaves the others' untouched.
_adattatori: list = []


def registra_adattatore(funzione) -> None:
	if funzione not in _adattatori:
		_adattatori.append(funzione)


def getCounts(d, doctype):
	d["_email_count"] = (
		frappe.db.count(
			"Communication",
			filters={
				"reference_doctype": doctype,
				"reference_name": d.get("name"),
				"communication_type": "Communication",
			},
		)
		or 0
	)
	d["_email_count"] = d["_email_count"] + frappe.db.count(
		"Communication",
		filters={
			"reference_doctype": doctype,
			"reference_name": d.get("name"),
			"communication_type": "Automated Message",
		},
	)
	d["_comment_count"] = frappe.db.count(
		"Comment",
		filters={"reference_doctype": doctype, "reference_name": d.get("name"), "comment_type": "Comment"},
	)
	d["_task_count"] = frappe.db.count(
		"CRM Task", filters={"reference_doctype": doctype, "reference_docname": d.get("name")}
	)
	d["_note_count"] = frappe.db.count(
		"FCRM Note", filters={"reference_doctype": doctype, "reference_docname": d.get("name")}
	)
	return d


#: Documents that belong to the record they point at, and the records whose
#: `on_trash` deletes them: never offered for unlinking when one of those goes.
DELETED_WITH_THEIR_RECORD = {
	"CRM Billing Profile": {"CRM Lead", "CRM Organization"},
	"CRM Consent": {"CRM Lead"},
	"CRM Related Person": {"CRM Lead"},
	"CRM Waiting List Entry": {"CRM Lead"},
	"CRM Automation Enrollment": {"CRM Lead", "CRM Deal"},
}


@frappe.whitelist()
def get_linked_docs_of_document(doctype: str, docname: str):
	try:
		doc = frappe.get_doc(doctype, docname)
	except frappe.DoesNotExistError:
		return []

	frappe.has_permission(doctype, "read", doc, throw=True)

	nome_del_record = doc.get(doc.meta.title_field) if doc.meta.title_field else None

	linked_docs = get_linked_docs(doc)
	dynamic_linked_docs = get_dynamic_linked_docs(doc)

	linked_docs.extend(dynamic_linked_docs)
	linked_docs = list({doc["reference_docname"]: doc for doc in linked_docs}.values())

	docs_data = []
	for doc in linked_docs:
		if not doc.get("reference_doctype") or not doc.get("reference_docname"):
			continue

		try:
			data = frappe.get_doc(doc["reference_doctype"], doc["reference_docname"])
		except (frappe.DoesNotExistError, frappe.ValidationError):
			continue

		# linked is not the same as readable: a person's deal can belong to somebody else
		if not frappe.has_permission(data.doctype, "read", data):
			continue

		# part of the record rather than linked to it: it goes with it (the
		# record's own on_trash), there is nothing to choose about it
		if doctype in DELETED_WITH_THEIR_RECORD.get(data.doctype, ()):
			continue

		title = data.get("title")
		if data.doctype == "CRM Call Log":
			# a call logged by hand may not know the number it was made from
			title = (
				_("Call from {0} to {1}").format(data.get("from"), data.get("to"))
				if data.get("from")
				else _("Call to {0}").format(data.get("to") or "")
			)

		if data.doctype == "CRM Deal":
			title = data.get("organization")

		if data.doctype == "CRM Notification":
			title = data.get("message")

		if not title and data.meta.title_field:
			title = data.get(data.meta.title_field)
			# the record's own name on what is its own says nothing
			if title and title == nome_del_record:
				title = None

		docs_data.append(
			{
				"doc": data.doctype,
				# never the record's code: what it is, in words
				"title": title or _(data.doctype),
				"reference_docname": doc["reference_docname"],
				"reference_doctype": doc["reference_doctype"],
			}
		)
	return docs_data


def remove_doc_link(doctype, docname):
	if not doctype or not docname:
		return

	try:
		linked_doc_data = frappe.get_doc(doctype, docname)
		if doctype == "CRM Notification":
			delete_notification_type = {
				"notification_type_doctype": "",
				"notification_type_doc": "",
			}
			delete_references = {
				"reference_doctype": "",
				"reference_name": "",
			}

			if linked_doc_data.get("notification_type_doctype") == linked_doc_data.get("reference_doctype"):
				delete_references.update(delete_notification_type)

			linked_doc_data.update(delete_references)
		else:
			linked_doc_data.update(
				{
					"reference_doctype": "",
					"reference_docname": "",
				}
			)
		linked_doc_data.save(ignore_permissions=True)
	except (frappe.DoesNotExistError, frappe.ValidationError):
		pass


def remove_contact_link(doctype, docname):
	if not doctype or not docname:
		return

	try:
		linked_doc_data = frappe.get_doc(doctype, docname)
		linked_doc_data.update(
			{
				"contact": None,
				"contacts": [],
			}
		)
		linked_doc_data.save(ignore_permissions=True)
	except (frappe.DoesNotExistError, frappe.ValidationError):
		pass


@frappe.whitelist()
def remove_linked_doc_reference(items: str | list, remove_contact: bool = False, delete: bool = False):
	if isinstance(items, str):
		items = frappe.parse_json(items)

	for item in items:
		if not item.get("doctype") or not item.get("docname"):
			continue

		if not frappe.has_permission(item["doctype"], "write", item["docname"]):
			continue

		try:
			if remove_contact:
				remove_contact_link(item["doctype"], item["docname"])
			else:
				remove_doc_link(item["doctype"], item["docname"])

			if delete:
				frappe.delete_doc(item["doctype"], item["docname"])
		except (frappe.DoesNotExistError, frappe.ValidationError):
			# Skip if document doesn't exist or has validation errors
			continue

	return "success"


@frappe.whitelist(methods=["POST"])
def delete_bulk_docs(doctype: str, items: str | list, delete_linked: bool = False):
	from frappe.desk.reportview import delete_bulk

	if not doctype:
		frappe.throw(_("Doctype is required"))

	if not items:
		frappe.throw(_("Items are required"))

	items = frappe.parse_json(items)
	if not isinstance(items, list):
		frappe.throw(_("Items must be a list"))

	for doc in items:
		try:
			if not frappe.db.exists(doctype, doc):
				frappe.log_error(f"Document {doctype} {doc} does not exist", "Bulk Delete Error")
				continue

			linked_docs = get_linked_docs_of_document(doctype, doc)
			for linked_doc in linked_docs:
				if not linked_doc.get("reference_doctype") or not linked_doc.get("reference_docname"):
					continue

				remove_linked_doc_reference(
					[
						{
							"doctype": linked_doc["reference_doctype"],
							"docname": linked_doc["reference_docname"],
						}
					],
					remove_contact=doctype == "Contact",
					delete=delete_linked,
				)
		except Exception as e:
			frappe.log_error(f"Error processing linked docs for {doctype} {doc}: {e!s}", "Bulk Delete Error")

	if len(items) > 10:
		frappe.enqueue("frappe.desk.reportview.delete_bulk", doctype=doctype, items=items)
	else:
		delete_bulk(doctype, items)
	return "success"
