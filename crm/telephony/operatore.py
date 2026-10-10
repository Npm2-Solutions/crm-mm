# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's carrier: Twilio or Telnyx, one at a time (doc 64).

The centre's phone goes through one carrier, the one it connected on Settings >
Phone > Telephony: its calls, its numbers, its SMS and what it spends. Connecting
the other one asks to disconnect the first: the SMS leave from one sender, the
lines show one carrier's numbers, the spend is one carrier's. What was written
through the first - calls, messages - stays, each with the carrier it went
through (`telephony_medium`).

Every module that has something of the carrier's to do asks here which one it is,
and the carrier's own module does it: ``crm.telephony.collegamento`` and its
neighbours for Twilio, ``crm.telephony.telnyx`` for Telnyx.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

TWILIO, TELNYX = "twilio", "telnyx"
#: In the order they are asked: a site connected to both by hand in the Desk
#: answers with the first.
OPERATORI = (TWILIO, TELNYX)
#: Each carrier's settings, a Single with the same names for what they share:
#: ``enabled``, ``allowed_countries``, ``sms_from``, ``sms_sender_name``,
#: ``sms_sender_number``, ``record_calls``, ``recording_notice``, ``spend_alert``.
IMPOSTAZIONI = {TWILIO: "CRM Twilio Settings", TELNYX: "CRM Telnyx Settings"}
#: Its name, as a person reads it and as `telephony_medium` keeps it.
ETICHETTE = {TWILIO: "Twilio", TELNYX: "Telnyx"}
#: The field of `CRM Telephony Agent` with one's own line on that carrier.
LINEA = {TWILIO: "twilio_number", TELNYX: "telnyx_number"}
#: The step of Settings > Phone > Telephony that is the carrier's page.
PAGINA = {TWILIO: "twilio-settings", TELNYX: "telnyx-settings"}


def acceso(nome: str) -> bool:
	"""Whether a carrier is connected and switched on."""
	doctype = IMPOSTAZIONI.get(nome)
	return bool(doctype and cint(frappe.db.get_single_value(doctype, "enabled")))


def collegati() -> list[str]:
	"""The carriers switched on; one, as a rule."""
	return [nome for nome in OPERATORI if acceso(nome)]


def attivo() -> str | None:
	"""The centre's carrier, or None while none is connected."""
	accesi = collegati()
	return accesi[0] if accesi else None


def impostazioni(nome: str | None = None) -> str | None:
	"""The settings' doctype of a carrier, of the centre's one without a name."""
	nome = nome or attivo()
	return IMPOSTAZIONI.get(nome) if nome else None


def etichetta(nome: str | None = None) -> str:
	nome = nome or attivo()
	return ETICHETTE.get(nome or "", "")


def da_medium(medium: str | None) -> str | None:
	"""The carrier a `telephony_medium` names ("Twilio", "Telnyx"); None for a call
	logged by hand."""
	valore = (medium or "").strip().lower()
	return valore if valore in IMPOSTAZIONI else None


def linea(nome: str | None = None) -> str | None:
	"""The field of one's own line on a carrier, the centre's one without a name."""
	nome = nome or attivo()
	return LINEA.get(nome) if nome else None


def pagina(nome: str | None = None) -> str:
	"""The step of the telephony settings that is the carrier's page; the
	telephony's own while none is connected."""
	nome = nome or attivo()
	return PAGINA.get(nome or "", "telephony-settings")


def libero_per(nome: str) -> None:
	"""Refuse to connect ``nome`` while the other carrier is connected: the centre's
	phone goes through one."""
	for altro in collegati():
		if altro != nome:
			frappe.throw(
				_(
					"{0} is connected: the centre's phone goes through one carrier. Disconnect {0} first, then connect {1}."
				).format(ETICHETTE[altro], ETICHETTE[nome]),
				title=_("Telephony"),
			)
