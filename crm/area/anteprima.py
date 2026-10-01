# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The preview of a person's area: the area as they see it, opened by the centre
from the person's page, before the area is theirs or after (docs/progetto-ghl/41).

- **Who**: whoever opens areas (`area.invita`) and reads the person, from the
  desk's own session; never a client of the area.
- **How**: `start` ties the preview to the session (its id, in the cache, half an
  hour): the area's calls take the person from it, and `stop` ends it. Nothing is
  sent to the person, and no code is asked: the session is the centre's.
- **What it shows**: the area as the person would see it, through the same calls,
  but only what whoever previews reads in DottorCloud (`vede`): a plan, a document,
  a quote, an invoice they do not read keeps its place with nothing of it; one with
  health data they read goes in the access log, as on the person's page.
- **What it never does**: write, send, book or download. The area's calls are
  closed to a preview unless they say they only read (`anche_in_anteprima`), so a
  call that would tick an item, post a message, join a waiting list or open a form
  answers that this is a preview.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_url

from crm.permissions import livelli

#: How long a preview lasts without being opened again.
MINUTI = 30


def _chiave(sid: str | None = None) -> str:
	return f"crm-area-preview:{sid or frappe.session.sid}"


def in_anteprima() -> frappe._dict | None:
	"""The preview this session has open: who opened it, and whose area. None
	for a client of the area, a guest, or a session that opened none."""
	utente = frappe.session.user
	if not utente or utente == "Guest" or not getattr(frappe.session, "sid", None):
		return None
	dati = frappe.cache.get_value(_chiave())
	if not dati or dati.get("user") != utente:
		return None
	return frappe._dict(dati)


@frappe.whitelist(methods=["POST"])
def start(lead: str) -> dict:
	"""Open the preview of this person's area for this session: its address."""
	livelli.verifica("area.invita")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	utente = frappe.session.user
	if frappe.db.get_value("User", utente, "user_type") != "System User":
		frappe.throw(_("Only the centre previews an area"), frappe.PermissionError)
	frappe.cache.set_value(
		_chiave(),
		{
			"user": utente,
			"lead": lead,
			"lead_name": frappe.db.get_value("CRM Lead", lead, "lead_name") or lead,
		},
		expires_in_sec=MINUTI * 60,
	)
	return {"url": get_url("/area"), "minutes": MINUTI}


@frappe.whitelist(methods=["POST"])
def stop() -> None:
	"""Close the preview this session has open."""
	frappe.cache.delete_value(_chiave())


def rifiuta() -> None:
	frappe.throw(
		_("This is a preview: from here nothing is changed and nothing is sent"),
		frappe.PermissionError,
	)


def vede(doctype: str, nome: str) -> bool:
	"""In a preview, whether whoever previews reads this in DottorCloud; one with
	health data they read goes in the access log. Outside a preview, always: the
	area is the person's own."""
	vista = in_anteprima()
	if not vista:
		return True
	if not nome or not frappe.has_permission(doctype, "read", doc=nome, user=vista.user):
		return False
	if frappe.get_meta(doctype).has_field("clinical") and cint(
		frappe.db.get_value(doctype, nome, "clinical")
	):
		frappe.get_doc(doctype, nome).add_viewed(force=True)
	return True


def coperta(riga: dict, chiave: str = "name") -> dict:
	"""What a preview shows of a row whoever previews may not read: its place."""
	return {chiave: riga.get(chiave), "hidden": 1}


def filtra(doctype: str, righe: list, chiave: str = "name", campo: str | None = None) -> list:
	"""A list of the area as whoever previews reads it: each row read (`vede`), or
	kept in its place with nothing of it. ``campo`` names the row's record when it
	is not the row's key (a delivery points to its document)."""
	if not in_anteprima():
		return righe
	return [riga if vede(doctype, riga.get(campo or chiave)) else coperta(riga, chiave) for riga in righe]
