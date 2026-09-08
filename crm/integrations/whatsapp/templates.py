# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp message templates, managed from the CRM.

Outside the 24-hour window that opens when a customer writes, WhatsApp only
allows **approved templates**, so creating them cannot be a trip into the Desk:
it belongs in the CRM next to the chat.

frappe_whatsapp owns the `WhatsApp Templates` doctype and submits each one to
Meta for review when it is saved; this module is the CRM-facing surface over it.
Field names are read from the installed doctype rather than assumed, so a
different frappe_whatsapp release degrades instead of breaking.
"""

import json
import re

import frappe
from frappe import _

MANAGER_ROLES = {"System Manager", "Sales Manager"}
EDITABLE_FIELDS = (
	"template_name",
	"category",
	"language",
	"header",
	"header_type",
	"template",
	"footer",
	"sample_values",
)

# {{1}}, {{2}}… — Meta wants an example for every one of them, and wants them
# numbered from 1 without holes
PLACEHOLDER = re.compile(r"\{\{\s*(\d+)\s*\}\}")

# The only three Meta accepts. The installed doctype still offers TRANSACTIONAL,
# retired in 2023, and choosing it fails at submission with
# "(#100) Param category must be one of {UTILITY, MARKETING, AUTHENTICATION}" —
# after the template has been saved, so it looks like the CRM lost it.
META_CATEGORIES = ("UTILITY", "MARKETING", "AUTHENTICATION")


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage WhatsApp templates"), frappe.PermissionError)


def templates_available() -> bool:
	return bool(frappe.db.exists("DocType", "WhatsApp Templates"))


def _known_fields() -> set[str]:
	return {df.fieldname for df in frappe.get_meta("WhatsApp Templates").fields}


def _options_for(fieldname: str) -> list[str]:
	"""Select options straight from the installed doctype."""
	meta = frappe.get_meta("WhatsApp Templates")
	field = meta.get_field(fieldname)
	if not field or field.fieldtype != "Select" or not field.options:
		return []
	return [option for option in field.options.split("\n") if option]


def _languages() -> list[dict]:
	"""The languages the doctype will accept, which are Frappe's own.

	`language_code` is derived from this by frappe_whatsapp — it is not a field
	to fill in by hand, and the short hardcoded list we offered before ("en",
	"en_US", "it") both looked like a duplicate and left `language`, which is
	mandatory, empty.
	"""
	languages = frappe.get_all("Language", fields=["name", "language_name"], order_by="language_name")
	return [
		{"value": language.name, "label": f"{language.language_name} ({language.name})"}
		for language in languages
	]


def _categories() -> list[str]:
	"""What the doctype offers, minus what Meta has stopped accepting."""
	usable = [option for option in _options_for("category") if option.upper() in META_CATEGORIES]
	return usable or list(META_CATEGORIES)


@frappe.whitelist()
def get_templates() -> dict:
	_check_manager()
	if not templates_available():
		return {"available": False, "templates": []}

	known = _known_fields()
	fields = ["name"] + [f for f in ("template_name", "status", *EDITABLE_FIELDS) if f in known]
	return {
		"available": True,
		"templates": frappe.get_all(
			"WhatsApp Templates", fields=list(dict.fromkeys(fields)), order_by="modified desc"
		),
		"categories": _categories(),
		"languages": _languages(),
		"fields": sorted(known & set(EDITABLE_FIELDS)),
	}


def check_placeholders(values: dict) -> None:
	"""Every {{1}} needs an example, and they must run 1, 2, 3 without holes.

	Meta requires an example value for each parameter at creation time, and
	rejects the template the moment it is submitted when one is missing — so the
	CRM shows it saved and Meta answers REJECTED a second later, with the reason
	only in WhatsApp Manager. Better to refuse it here, while the person is still
	looking at the body they wrote.
	"""
	found = [int(number) for number in PLACEHOLDER.findall(values.get("template") or "")]
	if not found:
		return

	wanted = sorted(set(found))
	if wanted != list(range(1, len(wanted) + 1)):
		frappe.throw(
			_("The placeholders must be numbered from {{1}} without gaps. This body has: {0}").format(
				", ".join(f"{{{{{number}}}}}" for number in wanted)
			)
		)

	samples = [value.strip() for value in (values.get("sample_values") or "").split(",") if value.strip()]
	if len(samples) != len(wanted):
		frappe.throw(
			_(
				"Meta wants an example for every placeholder: this body has {0} and {1} were given. "
				"Write them separated by commas, in order."
			).format(len(wanted), len(samples))
		)


@frappe.whitelist(methods=["POST"])
def sync_templates() -> dict:
	"""Bring in the templates that live on Meta but not here.

	The list is read from the local records, so a template made in WhatsApp
	Manager — or `hello_world`, which Meta creates by itself with every new
	WhatsApp Business Account — exists on Meta and is invisible here, and cannot
	be sent.

	It also refreshes the status of the ones we did create: normally that arrives
	on the `message_template_status_update` webhook, and this is the way back if
	one is ever missed.

	frappe_whatsapp's `fetch` writes with `db_insert`/`db_update`, not `insert`,
	so it does not re-submit anything to Meta — it only reads.
	"""
	_check_manager()
	if not templates_available():
		frappe.throw(_("The WhatsApp app is not installed on this site"))

	from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates import fetch

	fetch()
	return get_templates()


@frappe.whitelist(methods=["POST"])
def save_template(template: dict | str, name: str | None = None) -> dict:
	"""Create or update a template. Saving submits it to Meta for review."""
	_check_manager()
	if not templates_available():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	if isinstance(template, str):
		template = json.loads(template)

	known = _known_fields()
	values = {
		field: template.get(field)
		for field in EDITABLE_FIELDS
		if field in known and template.get(field) is not None
	}
	if not values.get("template"):
		frappe.throw(_("The message body is required"))
	if not name and not values.get("template_name"):
		frappe.throw(_("A template name is required"))

	check_placeholders(values)

	# frappe_whatsapp only puts the header in the payload when `header_type` says
	# what kind it is; without it the header typed here was dropped in silence
	if "header_type" in known:
		values["header_type"] = "TEXT" if values.get("header") else ""

	category = values.get("category")
	if category and category.upper() not in META_CATEGORIES:
		# say it here, before the template is saved and Meta rejects it with a
		# number instead of a reason
		frappe.throw(
			_("Meta no longer accepts the category {0}. Choose Utility, Marketing or Authentication.").format(
				category
			)
		)

	if name:
		doc = frappe.get_doc("WhatsApp Templates", name)
		# Meta does not allow renaming an approved template
		values.pop("template_name", None)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "WhatsApp Templates", **values})
		doc.insert()
	return {"name": doc.name, "status": doc.get("status") or ""}


@frappe.whitelist(methods=["POST"])
def delete_template(name: str) -> None:
	_check_manager()
	frappe.delete_doc("WhatsApp Templates", name)
