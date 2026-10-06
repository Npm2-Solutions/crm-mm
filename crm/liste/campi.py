# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The fields a list offers (`crm.liste.regole`), read off a DocType's meta:
only what the session may read, each with the section and the tab it sits in,
leaving out what a document keeps only for the machine."""

import frappe
from frappe import _

from crm.liste import regole

# what a document keeps only for the machine, besides what no document offers
# (`regole.DELLA_MACCHINA`): the browser and the visits the tracking recognised
# a person in (the History tab reads them), Meta's ids of a lead form, where the
# conversations panel keeps its place, the totals of a products grid
# DottorCloud does not draw, the address book's entry behind a person, a call's
# id at Twilio and the address of its recording
SOLO_PER_LA_MACCHINA = {
	"CRM Lead": frozenset(
		{
			"contact",
			"conversation_seen_by",
			"conversation_seen_until",
			"facebook_ad_id",
			"facebook_form_id",
			"facebook_lead_id",
			"first_touch_session",
			"last_touch_session",
			"net_total",
			"total",
			"visitor",
		}
	),
	"CRM Deal": frozenset(
		{
			"conversation_seen_by",
			"conversation_seen_until",
			"first_touch_session",
			"last_touch_session",
			"net_total",
			"total",
			"visitor",
		}
	),
	"CRM Call Log": frozenset({"id", "note", "recording_url"}),
	# the framework's address book: its sync with Google Contacts, the user an
	# entry may be
	"Contact": frozenset(
		{
			"google_contacts",
			"google_contacts_id",
			"pulled_from_google_contacts",
			"sync_with_google_contacts",
			"user",
		}
	),
}


def della_lista(doctype: str, uso: str, togli=()) -> list[dict]:
	"""The fields `doctype`'s list offers for `uso` (`regole.USI`), in the
	reader's words: what sits on a permission level the session cannot read
	is not offered, as a record's page does not draw it."""
	meta = frappe.get_meta(doctype)
	alti = any((df.permlevel or 0) > 0 for df in meta.fields)
	leggibili = (
		set(meta.get_permlevel_access("read"))
		if alti and not meta.istable and frappe.session.user != "Administrator"
		else None
	)

	campi = []
	sezione = scheda = None
	for df in meta.fields:
		if df.fieldtype == "Tab Break":
			scheda, sezione = df.label, None
			continue
		# a section without a heading carries on the one above it (a touch's
		# pages, under «First Touch»)
		if df.fieldtype == "Section Break":
			sezione = df.label or sezione
			continue
		if leggibili is not None and (df.permlevel or 0) > 0 and df.permlevel not in leggibili:
			continue
		campi.append(
			{
				"fieldname": df.fieldname,
				"fieldtype": df.fieldtype,
				"label": df.label,
				"options": df.options,
				"hidden": df.hidden,
				"sezione": sezione,
				"scheda": scheda,
			}
		)

	return regole.scegli(
		campi,
		uso,
		t=_,
		togli=SOLO_PER_LA_MACCHINA.get(doctype, frozenset()) | set(togli),
	)
