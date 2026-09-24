# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The numbers this CRM may present, and what each one is actually good for.

A caller ID is not just a string. Whether a number can be shown on an outgoing
call, and whether a call *to* it ever reaches this CRM, depend on things that
live at the carrier and change without anyone here being told: what kind of
number it is, whether it was verified, and whether it has been handed to a SIP
trunk. So the list is synced rather than typed, and every row carries the answers.

The trunk case is the one that bites. A number assigned to an Elastic SIP Trunk
has its voice URL ignored by Twilio — the call goes straight to the trunk's
origination URI and never touches us — so the answering service simply cannot
run on it. Nothing announces that; the segreteria just never picks up.
"""

from __future__ import annotations

import frappe
import phonenumbers
from frappe import _
from frappe.utils import now_datetime

SOURCE_ACCOUNT = "Account Number"
SOURCE_VERIFIED = "Verified Caller ID"
SOURCE_MANUAL = "Manual"

_TYPES = {
	phonenumbers.PhoneNumberType.FIXED_LINE: "Geographic",
	phonenumbers.PhoneNumberType.MOBILE: "Mobile",
	phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
	phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
	phonenumbers.PhoneNumberType.VOIP: "VoIP",
	phonenumbers.PhoneNumberType.UAN: "National",
}


def classify(phone_number: str, default_region: str | None = None) -> dict:
	"""What kind of number this is, read from the number itself.

	Returns the E.164 spelling alongside the type and country, because storing a
	number in one canonical form is what makes the rest of this comparable.
	"""
	blank = {"e164": (phone_number or "").strip(), "number_type": "", "country": ""}
	if not phone_number:
		return blank

	try:
		parsed = phonenumbers.parse(phone_number, default_region)
	except phonenumbers.NumberParseException:
		return blank

	if not phonenumbers.is_possible_number(parsed):
		return blank

	return {
		"e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
		"number_type": _TYPES.get(phonenumbers.number_type(parsed), "Other"),
		"country": phonenumbers.region_code_for_number(parsed) or "",
	}


# --------------------------------------------------------------------------
# syncing
# --------------------------------------------------------------------------


def sync(provider_name: str = "twilio") -> dict:
	"""Rebuild the list from what the provider actually has.

	Numbers that have gone from the account are switched off rather than deleted:
	an agent or a call log may still point at one, and losing the row would lose
	the label that explains what it was.
	"""
	from crm.telephony import providers

	provider = providers.get(provider_name)
	if not provider.is_enabled():
		frappe.throw(_("{0} is not enabled.").format(provider.label), title=_("Not Configured"))
	if not hasattr(provider, "list_caller_ids"):
		frappe.throw(_("{0} cannot list its numbers.").format(provider.label), title=_("Not Supported"))

	seen: set[str] = set()
	added = 0

	for row in provider.list_caller_ids():
		name, is_new = _upsert(provider_name, row)
		if not name:
			continue
		seen.add(name)
		added += int(is_new)

	retired = _retire_missing(provider_name, seen)
	return {
		"total": len(seen),
		"added": added,
		"retired": retired,
		"provider": provider.label,
		"answering_capable": len(answering_capable_numbers()),
	}


def _upsert(provider_name: str, row: dict) -> tuple[str | None, bool]:
	facts = classify(row.get("phone_number"))
	number = facts["e164"] or (row.get("phone_number") or "").strip()
	if not number:
		return None, False

	values = {
		"provider": provider_name,
		"source": row.get("source") or SOURCE_MANUAL,
		"number_type": facts["number_type"],
		"country": facts["country"],
		"voice_capable": 1 if row.get("voice_capable", True) else 0,
		"sms_capable": 1 if row.get("sms_capable") else 0,
		"sip_trunk": row.get("sip_trunk") or None,
		"sip_trunk_sid": row.get("sip_trunk_sid") or None,
		"voice_url": row.get("voice_url") or None,
		"last_synced_on": now_datetime(),
		"enabled": 1,
	}
	values.update(_routing(row))

	if frappe.db.exists("CRM Caller ID", number):
		doc = frappe.get_doc("CRM Caller ID", number)
		# the label is a person's words about the number; the sync only fills it in
		# when nobody has, so a hand-written one survives every refresh
		if not doc.label and row.get("label"):
			values["label"] = row["label"]
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc.name, False

	doc = frappe.get_doc(
		{
			"doctype": "CRM Caller ID",
			"phone_number": number,
			"label": row.get("label") or "",
			**values,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name, True


def _routing(row: dict) -> dict:
	"""Does a call to this number reach us, and if not, why not."""
	if row.get("sip_trunk_sid"):
		return {
			"routes_to_crm": 0,
			"routing_note": _(
				"Assigned to the SIP trunk {0}. Twilio ignores the voice webhook on a "
				"trunked number and sends the call straight to your own SIP "
				"infrastructure, so the answering service cannot run on it."
			).format(row.get("sip_trunk") or row["sip_trunk_sid"]),
		}

	if row.get("source") == SOURCE_VERIFIED:
		return {
			"routes_to_crm": 0,
			"routing_note": _(
				"Verified as an outgoing caller ID only. It can be presented on calls "
				"you place, but incoming calls to it do not belong to this account."
			),
		}

	if row.get("points_at_crm") is True:
		return {"routes_to_crm": 1, "routing_note": None}

	if row.get("uses_crm_app"):
		# the TwiML app is the endpoint agents dial *out* through; a number pointed
		# at it for incoming calls reaches the CRM at the wrong door
		return {
			"routes_to_crm": 0,
			"routing_note": _(
				"Set to this CRM's TwiML app, which handles outgoing calls. Point its "
				"voice webhook at the incoming handler instead — the Twilio settings "
				"page shows the address."
			),
		}

	if row.get("voice_url") or row.get("voice_application_sid"):
		return {
			"routes_to_crm": 0,
			"routing_note": _(
				"Its voice webhook points somewhere other than this CRM, so incoming "
				"calls are handled elsewhere."
			),
		}

	return {
		"routes_to_crm": 0,
		"routing_note": _("No voice webhook is configured, so incoming calls go nowhere."),
	}


def _retire_missing(provider_name: str, seen: set[str]) -> int:
	"""Switch off rows the provider no longer reports."""
	stale = frappe.get_all(
		"CRM Caller ID",
		filters={"provider": provider_name, "enabled": 1, "source": ["!=", SOURCE_MANUAL]},
		pluck="name",
	)
	retired = [name for name in stale if name not in seen]
	for name in retired:
		frappe.db.set_value(
			"CRM Caller ID",
			name,
			{
				"enabled": 0,
				"routes_to_crm": 0,
				"routing_note": _("No longer present on the provider account."),
			},
			update_modified=False,
		)
	return len(retired)


# --------------------------------------------------------------------------
# reading the list
# --------------------------------------------------------------------------

FIELDS = (
	"name",
	"phone_number",
	"label",
	"enabled",
	"source",
	"number_type",
	"country",
	"voice_capable",
	"sms_capable",
	"routes_to_crm",
	"routing_note",
	"sip_trunk",
	"last_synced_on",
)


@frappe.whitelist()
def get_caller_ids(provider: str | None = None, only_enabled: bool = True) -> list[dict]:
	"""The list, for a settings page or an agent's number picker."""
	filters = {}
	if provider:
		filters["provider"] = provider
	if frappe.utils.sbool(only_enabled):
		filters["enabled"] = 1
	return frappe.get_list("CRM Caller ID", filters=filters, fields=list(FIELDS), order_by="phone_number asc")


@frappe.whitelist()
def sync_caller_ids(provider: str = "twilio") -> dict:
	"""Refresh the list from the provider. Managers only — it talks to the carrier."""
	if not frappe.has_permission("CRM Caller ID", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	result = sync(provider)
	frappe.db.commit()
	return result


@frappe.whitelist(methods=["POST"])
def verify_number(phone_number: str, label: str | None = None, provider: str = "twilio") -> dict:
	"""Start the provider's verification for a number the practice owns elsewhere.

	The provider rings it and hands back a code to type on the phone. Answering and
	entering it is the proof of control — which is the whole difference between a
	legitimate caller ID and spoofing.
	"""
	from crm.telephony import providers

	if not frappe.has_permission("CRM Caller ID", "create"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if not (phone_number or "").strip():
		frappe.throw(_("Enter the number to verify."))

	handler = providers.get(provider)
	if not hasattr(handler, "start_caller_id_verification"):
		frappe.throw(_("{0} cannot verify a caller ID.").format(handler.label), title=_("Not Supported"))
	return handler.start_caller_id_verification(phone_number.strip(), label)


@frappe.whitelist(methods=["POST"])
def set_label(name: str, label: str | None = None) -> dict:
	"""Rename a number in words. The sync leaves a hand-written label alone."""
	doc = frappe.get_doc("CRM Caller ID", name)
	doc.check_permission("write")
	doc.label = (label or "").strip()
	doc.save()
	return {"name": doc.name, "label": doc.label}


@frappe.whitelist(methods=["POST"])
def set_enabled(name: str, enabled: bool = True) -> dict:
	"""Take a number out of circulation without losing what it was."""
	doc = frappe.get_doc("CRM Caller ID", name)
	doc.check_permission("write")
	doc.enabled = 1 if frappe.utils.sbool(enabled) else 0
	doc.save()
	return {"name": doc.name, "enabled": bool(doc.enabled)}


def answering_capable_numbers() -> list[str]:
	"""Numbers the answering service can actually answer on."""
	return frappe.get_all("CRM Caller ID", filters={"enabled": 1, "routes_to_crm": 1}, pluck="phone_number")


def usable_for_outbound(provider: str = "twilio") -> list[str]:
	"""Numbers that may be presented as a caller ID.

	Both owned and verified numbers qualify — that is precisely what verifying a
	number is for — so this is wider than the set the CRM can answer on.
	"""
	return frappe.get_all(
		"CRM Caller ID",
		filters={"enabled": 1, "provider": provider, "voice_capable": 1},
		pluck="phone_number",
		order_by="phone_number asc",
	)
