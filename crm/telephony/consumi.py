# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the centre's Twilio space spends, and what went wrong in it (doc 52, fifth
part).

- **This month** by kind, from Twilio's usage records, and the space's problems of
  the last days from Twilio's log (its "Monitor"), each in DottorCloud's words: on
  Twilio's page, for whoever pays - the centre's manager on its own account, the
  agency on the agency's. What Twilio said is kept ten minutes.
- **The spend alert**: the amount the centre writes on the page becomes a usage
  trigger in the space, renewed every month; when this month's spend reaches it,
  Twilio calls ``spend_reached`` and whoever pays is told ("Phone", it opens
  Twilio's page). Put back every hour with the rest of the space.
- **The credit** is the account's, and a space has none of its own: Twilio shows
  it, and that is where it is topped up.

The rules without a site are in ``consumi_regole`` and ``errori_regole``.
"""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, flt, fmt_money, get_first_day, now_datetime, today

from crm.integrations.twilio.utils import get_public_url
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony import collegamento, errori
from crm.telephony import consumi_regole as R
from crm.telephony import errori_regole as E

IMPOSTAZIONI = collegamento.IMPOSTAZIONI
#: The spend alert's name in Twilio's console.
NOME_AVVISO = "DottorCloud: spend this month"
#: Where Twilio calls when this month's spend reaches the alert.
QUANDO_SPESO = "/api/method/crm.integrations.twilio.api.spend_reached"
#: How long what Twilio said is kept, in seconds.
DURATA = 600
#: How many days of problems the page shows.
GIORNI = 7


def _cliente(impostazioni):
	auth_token = impostazioni.get_password("auth_token", raise_exception=False)
	return collegamento.Client(impostazioni.account_sid, auth_token)


def _paga_l_agenzia(impostazioni) -> bool:
	return impostazioni.account_owner == "Agency"


def _vede(impostazioni, user: str | None = None) -> bool:
	"""Who reads what the space spends: whoever pays for it, the agency on the
	agency's account; on the centre's, its manager and the agency that helps."""
	if _paga_l_agenzia(impostazioni):
		return livelli.puo(collegamento.TECNICO, user)
	return livelli.puo(collegamento.CENTRO, user)


def _chiave(impostazioni) -> str:
	return f"crm:twilio:consumi:{impostazioni.account_sid}"


# ------------------------------------------------------------------ this month and its problems


def _chiedi(impostazioni) -> dict:
	"""What Twilio says of the space: this month's records, the last days' problems."""
	cliente = _cliente(impostazioni)
	righe = {}
	for categoria in R.CATEGORIE:
		for record in cliente.usage.records.this_month.list(category=categoria):
			righe[categoria] = {
				"count": record.count,
				"usage": record.usage,
				"usage_unit": record.usage_unit,
				"price": str(record.price if record.price is not None else 0),
				"price_unit": record.price_unit,
			}
	dal = now_datetime() - timedelta(days=GIORNI)
	avvisi = [
		{
			"error_code": avviso.error_code,
			"alert_text": avviso.alert_text,
			"date_created": _quando(avviso.date_created),
			"more_info": avviso.more_info,
		}
		for avviso in cliente.monitor.v1.alerts.list(log_level="error", start_date=dal, limit=200)
	]
	return {"records": righe, "alerts": avvisi}


def _quando(momento) -> str:
	"""A moment of Twilio's, in UTC, as the site's clock reads it."""
	if not momento:
		return ""
	return str(convert_utc_to_system_timezone(momento).replace(tzinfo=None, microsecond=0))


@frappe.whitelist()
def get_twilio_usage() -> dict:
	"""For Twilio's page: this month's spend by kind, the last days' problems in
	words, the alert. Nothing for whoever does not pay for the space."""
	livelli.verifica(collegamento.CENTRO)
	impostazioni = frappe.get_single(IMPOSTAZIONI)
	if not (collegamento.collegato(impostazioni) and _vede(impostazioni)):
		return {"visible": False}
	dati = frappe.cache.get_value(_chiave(impostazioni))
	if not dati:
		try:
			dati = _chiedi(impostazioni)
		except collegamento.NON_RISPONDE as errore:
			collegamento._registra("DottorCloud: Twilio's usage", errore)
			return {"visible": True, "error": collegamento.in_parole(errore)}
		frappe.cache.set_value(_chiave(impostazioni), dati, expires_in_sec=DURATA)
	mese = R.consumi(dati.get("records") or {})
	for voce in mese["items"]:
		voce["label"] = _(voce["label"])
	return {
		"visible": True,
		"since": str(get_first_day(today())),
		"month": mese,
		"problems": [
			{**riga, "sentence": errori.in_parole(riga["code"], riga["twilio"])}
			for riga in E.raggruppa(dati.get("alerts") or [])
		],
		"days": GIORNI,
		"alert": flt(impostazioni.spend_alert) or None,
		"agency": _paga_l_agenzia(impostazioni),
	}


# ------------------------------------------------------------------ the spend alert


def allinea_l_avviso(impostazioni=None) -> None:
	"""Twilio's trigger as the centre set the alert: made, replaced (Twilio does
	not change a trigger's amount), pointed here again or taken away. Only in a
	space DottorCloud made or was given; an account connected by hand is not
	touched."""
	impostazioni = impostazioni or frappe.get_single(IMPOSTAZIONI)
	if not (collegamento.collegato(impostazioni) and impostazioni.account_owner):
		return
	voluta = R.soglia(impostazioni.spend_alert)
	indirizzo = get_public_url(QUANDO_SPESO)
	cliente = _cliente(impostazioni)
	nostri = [
		trigger
		for trigger in cliente.usage.triggers.list(usage_category=R.TOTALE)
		if trigger.friendly_name == NOME_AVVISO
	]
	attuale = nostri[0] if nostri else None
	for doppio in nostri[1:]:
		cliente.usage.triggers(doppio.sid).delete()
	azione = R.cosa_fare_del_trigger(
		{"trigger_value": attuale.trigger_value, "callback_url": attuale.callback_url} if attuale else None,
		voluta,
		indirizzo,
	)
	sid = attuale.sid if attuale else None
	if azione in ("delete", "replace"):
		cliente.usage.triggers(attuale.sid).delete()
		sid = None
	if azione in ("create", "replace"):
		sid = cliente.usage.triggers.create(
			callback_url=indirizzo,
			callback_method="POST",
			trigger_value=str(voluta),
			usage_category=R.TOTALE,
			trigger_by="price",
			recurring="monthly",
			friendly_name=NOME_AVVISO,
		).sid
	if azione == "update":
		cliente.usage.triggers(attuale.sid).update(callback_url=indirizzo, callback_method="POST")
	if (sid or "") != (impostazioni.spend_alert_trigger or ""):
		frappe.db.set_single_value(IMPOSTAZIONI, "spend_alert_trigger", sid or "")


def _valuta(impostazioni) -> str:
	"""The account's currency, as Twilio's records give it; dollars, Twilio's own,
	when nothing says otherwise."""
	dati = frappe.cache.get_value(_chiave(impostazioni)) or {}
	for riga in (dati.get("records") or {}).values():
		if riga.get("price_unit"):
			return riga["price_unit"].upper()
	return "USD"


def chi_avvisare(impostazioni) -> list[str]:
	"""Who hears that the alert was reached: whoever pays for the space - the
	centre's managers, or the agency on its own account."""
	agenzia = _paga_l_agenzia(impostazioni)
	return [
		utente
		for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		if utente not in ("Administrator", "Guest")
		and _vede(impostazioni, utente)
		and agenzia == livelli.e_agenzia(utente)
	]


def speso(trigger: str | None, attuale, voluta) -> list[str]:
	"""Twilio's trigger fired: this month's spend (``attuale``) reached the alert
	(``voluta``). Only DottorCloud's trigger is heard. Returns who was told."""
	impostazioni = frappe.get_single(IMPOSTAZIONI)
	if not trigger or trigger != impostazioni.spend_alert_trigger:
		return []
	valuta = _valuta(impostazioni)
	importo = fmt_money(flt(attuale), precision=2, currency=valuta)
	soglia = fmt_money(flt(voluta), precision=2, currency=valuta)
	chi = chi_avvisare(impostazioni)
	for utente in chi:
		avvisa(utente, "Phone", N.SPESA_TWILIO, [importo, soglia])
	return chi
