# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Notifications by email too: what somebody of the centre has not read in the
panel a few minutes after it came, in their email, in their language.

- **Which ones** each person chooses (Settings > Your account > Notifications): the
  groups of `regole.GRUPPI_EMAIL`, the usual ones on until they say otherwise. A
  notification knows when it is written whether it may go (`email_due`).
- **When**: every five minutes, what is still unread after `ATTESA` minutes - what
  was read in DottorCloud meanwhile never goes. One notification is one email; more
  than one are one email that lists them. A conversation goes once while it is
  unread, not at every message.
- **How**: in the brand's layout, the sentence of the panel, the first words of the
  message where the person may read them, a button that opens it in DottorCloud -
  never the Desk's form. The framework's own emails for an assignment, a mention, a
  document shared (doctypes and IDs, a link to the Desk) are not sent
  (`notification_skip_email_types`): these are.
"""

from __future__ import annotations

import json
from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import add_to_date, escape_html, get_url, now_datetime

from crm.marchio import con_nome
from crm.notifiche import regole as R

NOTIFICA = "CRM Notification"
#: Minutes a notification waits in the panel before it goes by email.
ATTESA = 5
#: The most an email lists; the rest are in the panel.
AL_PIU = 10
#: Where a person's choices are kept: a default of theirs.
CHIAVE = "crm_notifications_by_email"
#: Where the panel's page and the preferences are, in DottorCloud.
PAGINA = "/crm/notifications"
PREFERENZE = "/crm?settings=Notifications"


# ------------------------------------------------------------------ the choices


def preferenze(utente: str | None = None) -> dict:
	"""A person's choices: the groups they turned on or off (the rest as usual)."""
	valore = frappe.defaults.get_user_default(CHIAVE, user=utente or frappe.session.user)
	try:
		scelte = json.loads(valore) if valore else {}
	except ValueError:
		scelte = {}
	return {k: bool(v) for k, v in scelte.items() if k in R.GRUPPI_EMAIL} if isinstance(scelte, dict) else {}


def riceve(gruppo: str, utente: str | None = None) -> bool:
	"""Whether a person is among those a group's notifications go to: the page
	offers them only those. The questions from the area go to who reads the boards,
	the day's question about the agenda to who marks every appointment, invoicing's
	alerts to who manages invoicing (`monitoraggio.avvisa`), Twilio's answer on a
	new number's documents to who sets the phone up."""
	from crm.permissions import livelli

	utente = utente or frappe.session.user
	if gruppo == "area":
		return livelli.puo("area.messaggi", utente)
	if gruppo == "messages":
		return livelli.puo("conversazioni.vedi", utente)
	if gruppo == "agenda":
		return livelli.ambito("agenda.presenze", utente) == livelli.CENTRO
	if gruppo == "invoicing":
		return "Invoicing Manager" in frappe.get_roles(utente)
	if gruppo == "phone":
		return livelli.puo("telefono.configura", utente)
	return True


@frappe.whitelist()
def get_email_preferences() -> dict:
	"""The session's choices, each group they receive on or off."""
	scelte = preferenze()
	return {
		"groups": [
			{"key": gruppo, "on": scelte.get(gruppo, gruppo in R.EMAIL_DI_SOLITO)}
			for gruppo in R.GRUPPI_EMAIL
			if riceve(gruppo)
		],
		"minutes": ATTESA,
	}


@frappe.whitelist(methods=["POST"])
def save_email_preferences(groups: dict | str) -> dict:
	"""The session's choices: which groups go by email too. Only one's own."""
	scelte = frappe.parse_json(groups) if isinstance(groups, str) else (groups or {})
	if not isinstance(scelte, dict):
		frappe.throw(_("Choose what to receive by email"))
	pulite = {k: bool(v) for k, v in scelte.items() if k in R.GRUPPI_EMAIL}
	frappe.defaults.set_user_default(CHIAVE, json.dumps(pulite), user=frappe.session.user)
	return get_email_preferences()


# ------------------------------------------------------------------ sending


def manda_le_email() -> None:
	"""Every five minutes: what is still unread after `ATTESA` minutes, by email to
	whoever wants it - one email for each person."""
	limite = add_to_date(now_datetime(), minutes=-ATTESA)
	from crm.notifiche.api import CAMPI

	righe = frappe.get_all(
		NOTIFICA,
		filters={"email_due": 1, "read": 0, "creation": ("<=", limite)},
		fields=[*CAMPI, "to_user"],
		order_by="creation asc",
		limit=1000,
	)
	per_persona: dict[str, list] = {}
	for riga in righe:
		per_persona.setdefault(riga.to_user, []).append(riga)
	for utente, sue in per_persona.items():
		try:
			_manda(utente, sue)
		except Exception:
			frappe.log_error(title="Notifications: an email could not be sent", reference_doctype=NOTIFICA)
		finally:
			# sent or not, it is not tried again every five minutes
			frappe.db.set_value(
				NOTIFICA,
				{"name": ("in", [r.name for r in sue])},
				{"email_due": 0, "emailed_on": now_datetime()},
				update_modified=False,
			)


@contextmanager
def nella_lingua_di(utente: str):
	"""The words of an email, or a push, in the language of whoever it goes to."""
	from frappe.translate import get_user_lang

	prima = getattr(frappe.local, "lang", None)
	frappe.local.lang = get_user_lang(utente) or prima
	try:
		yield
	finally:
		frappe.local.lang = prima


def _manda(utente: str, righe: list) -> None:
	from crm.notifiche import api

	persona = frappe.db.get_value("User", utente, ["email", "enabled"], as_dict=True)
	if not persona or not persona.enabled or not persona.email:
		return
	with nella_lingua_di(utente):
		# newest first, as the panel shows them
		pannello = api.righe_del_pannello(sorted(righe, key=lambda r: r.creation, reverse=True), utente)
		if len(pannello) == 1:
			oggetto, titolo, corpo = _una(pannello[0])
		else:
			oggetto, titolo, corpo = _tante(pannello)
		frappe.sendmail(
			recipients=[persona.email],
			subject=oggetto,
			header=escape_html(titolo),
			with_container=True,
			message=corpo + _perche(len(pannello) > 1),
			reference_doctype=NOTIFICA,
			reference_name=pannello[0]["name"],
		)


def indirizzo(percorso: dict | None) -> str:
	"""The address in DottorCloud a notification opens: the person or the deal on
	what it names, the desk's day (the agenda's reception desk), the invoices; the
	panel's page without one."""
	if not percorso:
		return get_url(PAGINA)
	nome = percorso.get("name")
	parametri = percorso.get("params") or {}
	segno = percorso.get("hash") or ""
	if nome == "Lead":
		return get_url(f"/crm/leads/{parametri.get('leadId')}{segno}")
	if nome == "Deal":
		return get_url(f"/crm/deals/{parametri.get('dealId')}{segno}")
	if nome == "Today":
		return get_url("/crm/accoglienza")
	if nome == "Invoices":
		return get_url("/crm/fatture")
	return get_url(PAGINA)


def _una(riga: dict) -> tuple[str, str, str]:
	from crm.posta.aspetto import pulsante

	titolo = R.solo_testo(riga["text"])
	parti = []
	if riga.get("excerpt"):
		parti.append(
			'<p class="dc-citazione" style="border-left:3px solid #ebeeed;padding-left:12px;'
			f'color:#4e5352 !important">{escape_html(riga["excerpt"])}</p>'
		)
	parti.append(pulsante(indirizzo(riga.get("route")), con_nome(_("Open in {brand}"))))
	return titolo, titolo, "".join(parti)


def _tante(righe: list) -> tuple[str, str, str]:
	from crm.posta.aspetto import pulsante

	titolo = con_nome(_("You have {0} notifications in {brand}")).format(len(righe))
	parti = []
	for riga in righe[:AL_PIU]:
		parti.append(
			f'<p>{riga["text"]}<br><a href="{escape_html(indirizzo(riga.get("route")))}">{escape_html(_("Open it"))}</a></p>'
		)
	if len(righe) > AL_PIU:
		parti.append(
			f'<p class="text-muted">{escape_html(_("And {0} more.").format(len(righe) - AL_PIU))}</p>'
		)
	parti.append(pulsante(get_url(PAGINA), _("Open the notifications")))
	return titolo, titolo, "".join(parti)


def _perche(tante: bool = False) -> str:
	"""Why the email came, and where to choose otherwise."""
	if tante:
		frase = _(
			'We write to you because you have not read them in {brand} yet. Choose what you receive by email in <a href="{0}">your notification settings</a>.'
		)
	else:
		frase = _(
			'We write to you because you have not read it in {brand} yet. Choose what you receive by email in <a href="{0}">your notification settings</a>.'
		)
	return '<p class="text-muted text-small">{}</p>'.format(
		con_nome(frase).format(escape_html(get_url(PREFERENZE)))
	)
