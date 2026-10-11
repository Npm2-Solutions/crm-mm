# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""News in the area, told outside it (design.md, "Notifiche": "WhatsApp, SMS ed
email dicono solo 'c'è una novità nella tua area'; le email vanno solo a
indirizzi verificati").

- **The words are the same everywhere**: there is news in the area of the
  centre, and the link. What it is stays inside.
- **Email always**, to the address the person enters the area with: verified by
  every code it received.
- **WhatsApp or SMS if the person asks**, from the Messages of their area, and
  only to a number that is verified the same way: the person's number on file,
  which has written to the centre at least once on that channel. A number typed
  in the area is never used: a wrong digit would tell a stranger that somebody is
  a client of the centre - of a medical centre, a patient.
- **The centre chooses what it offers** (Settings > Client area): the approved
  WhatsApp template of the news, the number SMS leave from.
- **Not a flood**: WhatsApp and SMS at most once every two hours per person; the
  email as before. A notice that cannot leave never stops what caused it: the
  error log says why.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_url, now_datetime

from crm.area import accesso
from crm.permissions import livelli
from crm.telephony import operatore, sms

AVVISO = "CRM Area Notice"
IMPOSTAZIONI = "CRM Area Settings"
WHATSAPP, SMS = "WhatsApp", "SMS"
CANALI = (WHATSAPP, SMS)
#: How long after a WhatsApp or an SMS the next one waits.
ORE_TRA_AVVISI = 2


# ------------------------------------------------------------------ what the centre offers


def _modello_whatsapp() -> str | None:
	nome = frappe.db.get_single_value(IMPOSTAZIONI, "whatsapp_template")
	if not nome or not frappe.db.exists("DocType", "WhatsApp Templates"):
		return None
	return nome if frappe.db.exists("WhatsApp Templates", nome) else None


def _numero_sms() -> str | None:
	"""The centre's one sender (doc 52), the same as every other SMS of its."""
	return sms.mittente()


def offerti() -> list[str]:
	"""The channels the centre offers besides the email."""
	canali = []
	if _modello_whatsapp():
		canali.append(WHATSAPP)
	if _numero_sms():
		canali.append(SMS)
	return canali


@frappe.whitelist()
def get_notice_settings() -> dict:
	livelli.verifica("canali.configura")
	from crm.area.api import arrivo_dal_telefono

	# the ones the number that sends can send: the offers and the news leave from it
	from crm.integrations.whatsapp.templates import modelli_inviabili

	modelli = modelli_inviabili()
	return {
		"whatsapp_template": frappe.db.get_single_value(IMPOSTAZIONI, "whatsapp_template"),
		"sms_sender": _numero_sms(),
		"templates": modelli,
		# the centre's carrier, whose page sets the SMS sender
		"carrier": operatore.attivo() or "",
		"email_new_documents": cint(frappe.db.get_single_value(IMPOSTAZIONI, "email_new_documents")),
		"self_check_in": int(arrivo_dal_telefono()),
	}


@frappe.whitelist(methods=["POST"])
def save_notice_settings(
	whatsapp_template: str | None = None,
	email_new_documents: int | None = None,
	self_check_in: int | None = None,
) -> dict:
	"""What the area offers besides the email: the centre's, with the channels'
	capability. The SMS leave from the centre's one sender (the carrier's page). And
	whether a new document is told by email (`collegamento`), and whether the
	person may say «I'm here» from the area (`api.check_in`)."""
	livelli.verifica("canali.configura")
	if whatsapp_template and not frappe.db.exists("WhatsApp Templates", whatsapp_template):
		frappe.throw(_("This WhatsApp template does not exist"))
	frappe.db.set_single_value(IMPOSTAZIONI, "whatsapp_template", whatsapp_template or None)
	if email_new_documents is not None:
		frappe.db.set_single_value(IMPOSTAZIONI, "email_new_documents", int(bool(cint(email_new_documents))))
	if self_check_in is not None:
		frappe.db.set_single_value(IMPOSTAZIONI, "self_check_in", int(bool(cint(self_check_in))))
	return get_notice_settings()


# ------------------------------------------------------------------ whose number, verified


def _persona_di(user: str) -> str | None:
	"""The person the area user is: the area they enter as themselves, or the
	person with their address."""
	for riga in frappe.get_all(
		accesso.ACCESSO, filters={"user": user, "enabled": 1, "relation": accesso.SE_STESSO}, pluck="lead"
	):
		return riga
	return frappe.db.get_value("CRM Lead", {"email": user}, "name")


def _ha_scritto(lead: str, numero: str, canale: str) -> bool:
	"""Whether this number wrote to the centre on this channel, about this person
	or their deals."""
	from crm.api.lead import deal_names_of
	from crm.utils import to_e164

	riferimenti = [("CRM Lead", lead)] + [("CRM Deal", deal) for deal in deal_names_of(lead)]
	doctype = "WhatsApp Message" if canale == WHATSAPP else "CRM SMS Message"
	if not frappe.db.exists("DocType", doctype):
		return False
	for tipo, nome in riferimenti:
		mittenti = frappe.get_all(
			doctype,
			filters={"type": "Incoming", "reference_doctype": tipo, "reference_name": nome},
			pluck="from",
			limit=50,
		)
		if any(to_e164(m) == numero for m in mittenti if m):
			return True
	return False


def numero_verificato(user: str, canale: str) -> str | None:
	"""The number a notice may go to on this channel: the person's own, that
	wrote to the centre from it."""
	from crm.api.whatsapp import numbers_of

	lead = _persona_di(user)
	if not lead:
		return None
	numeri = numbers_of("CRM Lead", lead)
	if not numeri:
		return None
	return numeri[0] if _ha_scritto(lead, numeri[0], canale) else None


def _mascherato(numero: str) -> str:
	return "•••• " + numero[-3:]


# ------------------------------------------------------------------ the person's choice


def _scelti(user: str) -> dict[str, dict]:
	return {
		riga.channel: riga
		for riga in frappe.get_all(AVVISO, filters={"user": user}, fields=["name", "channel", "enabled"])
	}


@frappe.whitelist()
def notice_options() -> dict:
	"""How the session hears of news: the email, and what else it may choose."""
	utente = frappe.session.user
	if utente == "Guest" or not accesso.entra_nell_area(utente):
		frappe.throw(_("Enter the area first"), frappe.PermissionError)
	scelti = _scelti(utente)
	canali = []
	for canale in offerti():
		numero = numero_verificato(utente, canale)
		canali.append(
			{
				"channel": canale,
				"number": _mascherato(numero) if numero else None,
				"on": bool(numero and scelti.get(canale) and scelti[canale].enabled),
			}
		)
	return {"email": utente, "channels": canali}


@frappe.whitelist(methods=["POST"])
def set_notice(channel: str, on: int = 1) -> dict:
	"""On or off, for one channel: only to the verified number, never to one typed."""
	utente = frappe.session.user
	if utente == "Guest" or not accesso.entra_nell_area(utente):
		frappe.throw(_("Enter the area first"), frappe.PermissionError)
	if channel not in offerti():
		frappe.throw(_("The centre does not send news this way"))
	acceso = bool(cint(on))
	if acceso and not numero_verificato(utente, channel):
		frappe.throw(_("Write to the centre once from your number on {0}, then turn this on").format(channel))
	riga = _scelti(utente).get(channel)
	if riga:
		frappe.db.set_value(AVVISO, riga.name, {"enabled": int(acceso), "set_on": now_datetime()})
	else:
		frappe.get_doc(
			{
				"doctype": AVVISO,
				"user": utente,
				"channel": channel,
				"enabled": int(acceso),
				"set_on": now_datetime(),
			}
		).insert(ignore_permissions=True)
	return notice_options()


# ------------------------------------------------------------------ telling


def _testo(centro: str) -> str:
	return _("There is news in your area at {0}: {1}").format(centro, get_url("/area"))


def _manda_whatsapp(lead_utente: str, numero: str, centro: str) -> None:
	from crm.api.whatsapp import manda_modello

	modello = _modello_whatsapp()
	# the template's words are approved; its one variable, if any, is the centre
	variabili = frappe.db.get_value("WhatsApp Templates", modello, "template") or ""
	manda_modello(
		"CRM Lead", lead_utente, numero, modello, [centro] if "{{1}}" in variabili.replace(" ", "") else []
	)


def _manda_sms(lead_utente: str, numero: str, centro: str) -> None:
	from crm.api.sms import create_sms, deliver_sms

	doc = create_sms(
		type="Outgoing",
		from_number=_numero_sms(),
		to=numero,
		message=_testo(centro),
		reference_doctype="CRM Lead",
		reference_name=lead_utente,
	)
	deliver_sms(doc)


def _chiave_pausa(user: str, canale: str) -> str:
	return f"crm:area:avviso:{canale}:{user}"


def avvisa_fuori(lead: str) -> list[tuple[str, str]]:
	"""WhatsApp and SMS to whoever enters this area and asked for them: at most one
	every two hours each. Returns who was told how, for the trace."""
	from crm.moduli.richieste import nome_del_centro

	canali = offerti()
	if not canali:
		return []
	centro = nome_del_centro() or _("your centre")
	fatti = []
	for utente in sorted({riga.user for riga in accesso.accessi_aperti(lead)}):
		scelti = _scelti(utente)
		persona = _persona_di(utente)
		for canale in canali:
			if not (scelti.get(canale) and scelti[canale].enabled):
				continue
			# a STOP to the centre's SMS is heard by the area's news too (doc 52)
			if canale == SMS and sms.ha_fermato("CRM Lead", persona):
				continue
			if frappe.cache.get_value(_chiave_pausa(utente, canale)):
				continue
			numero = numero_verificato(utente, canale)
			if not numero:
				continue
			try:
				(_manda_whatsapp if canale == WHATSAPP else _manda_sms)(persona, numero, centro)
			except Exception:
				frappe.clear_last_message()
				frappe.log_error(title=f"Area news not sent by {canale}")
				continue
			frappe.cache.set_value(_chiave_pausa(utente, canale), 1, expires_in_sec=ORE_TRA_AVVISI * 3600)
			fatti.append((utente, canale))
	return fatti
