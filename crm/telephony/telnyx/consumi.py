# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the centre's Telnyx account spends, and what went wrong in it (doc 65).

- **This month** by kind and **the balance**, from Telnyx's usage reports, monthly
  charges and balance; **the last days' problems** from its messaging detail
  records, each in DottorCloud's words: on Telnyx's page, for whoever pays - the
  centre's manager on its own account, the agency on the agency's. What Telnyx
  said is kept ten minutes.
- **The alerts**, looked at every hour (`collegamento.assicura`): the month's spend
  reaching the centre's amount, the balance going down to its own; whoever pays is
  told ("Phone", it opens Telnyx's page).

The rules without a site are in ``consumi_regole`` and ``errori_regole``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, fmt_money, get_first_day, now_datetime, today

from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.telephony.telnyx import collegamento, errori
from crm.telephony.telnyx import consumi_regole as R
from crm.telephony.telnyx import errori_regole as E
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama, registra

IMPOSTAZIONI = collegamento.IMPOSTAZIONI
#: How long what Telnyx said is kept, in seconds.
DURATA = 600
#: How many days of problems the page shows.
GIORNI = 7


def _paga_l_agenzia(impostazioni) -> bool:
	return impostazioni.account_owner == "Agency"


def _vede(impostazioni, user: str | None = None) -> bool:
	"""Who reads what the account spends: whoever pays for it, the agency on the
	agency's account; on the centre's, its manager and the agency that helps."""
	if _paga_l_agenzia(impostazioni):
		return livelli.puo(collegamento.TECNICO, user)
	return livelli.puo(collegamento.CENTRO, user)


def _chiave(impostazioni) -> str:
	return f"crm:telnyx:consumi:{impostazioni.texml_application_id}"


# ------------------------------------------------------------------ this month and its problems


def _del_mese(api_secret: str, prodotto: str) -> list[dict]:
	"""A product's usage this month, from the first at midnight (UTC) to now."""
	adesso = now_datetime()
	inizio = get_first_day(today())
	parametri = {
		"product": prodotto,
		"dimensions": "direction",
		"metrics": ",".join(R.METRICHE.get(prodotto, ("cost",))),
		"start_date": f"{inizio}T00:00:00Z",
		"end_date": f"{add_days(adesso.date(), 1)}T00:00:00Z",
		"page[size]": 100,
	}
	try:
		risposto = chiama("GET", "usage_reports", api_secret, parametri=parametri)
	except ErroreTelnyx as errore:
		if errore.stato not in (400, 422):
			raise
		# a metric this product does not count: its cost alone
		risposto = chiama("GET", "usage_reports", api_secret, parametri={**parametri, "metrics": "cost"})
	return list((risposto or {}).get("data") or [])


def _chiedi(impostazioni) -> dict:
	"""What Telnyx says of the account: its balance, this month's usage and numbers'
	fees, the last days' failed messages."""
	api_secret = collegamento.chiave(impostazioni)
	bilancio = (chiama("GET", "balance", api_secret) or {}).get("data") or {}
	per_prodotto = {}
	for prodotto in R.PRODOTTI:
		try:
			per_prodotto[prodotto] = _del_mese(api_secret, prodotto)
		except ErroreTelnyx as errore:
			if errore.stato is None:
				raise
			# a product the account does not use, or Telnyx does not report on
			per_prodotto[prodotto] = []
	try:
		inizio = get_first_day(today())
		sommario = (
			chiama(
				"GET",
				"charges_summary",
				api_secret,
				parametri={"start_date": str(inizio), "end_date": str(add_days(today(), 1))},
			)
			or {}
		).get("data")
	except ErroreTelnyx as errore:
		registra("DottorCloud: Telnyx's monthly charges", errore)
		sommario = None
	try:
		falliti = (
			chiama(
				"GET",
				"detail_records",
				api_secret,
				parametri={
					"filter[record_type]": "messaging",
					"filter[date_range]": f"last_{GIORNI}_days",
					"filter[direction]": "outbound",
					"filter[status]": "failed",
					"sort": "-created_at",
					"page[size]": 50,
				},
			)
			or {}
		).get("data") or []
	except ErroreTelnyx as errore:
		registra("DottorCloud: Telnyx's detail records", errore)
		falliti = []
	return {
		"balance": {
			"balance": bilancio.get("balance"),
			"available_credit": bilancio.get("available_credit"),
			"currency": bilancio.get("currency") or "USD",
		},
		"products": per_prodotto,
		"numbers": R.dei_numeri(sommario) if sommario else None,
		"failed": [
			{
				"code": E.codice((riga.get("errors") or [None])[0]),
				"created_at": riga.get("created_at") or "",
			}
			for riga in falliti
		],
	}


def _dati(impostazioni, fresco: bool = False) -> dict:
	dati = None if fresco else frappe.cache.get_value(_chiave(impostazioni))
	if not dati:
		dati = _chiedi(impostazioni)
		if dati.get("numbers"):
			dati["numbers"] = {"count": dati["numbers"]["count"], "price": str(dati["numbers"]["price"])}
		frappe.cache.set_value(_chiave(impostazioni), dati, expires_in_sec=DURATA)
	return dati


def _mese(dati: dict) -> dict:
	numeri = dati.get("numbers")
	if numeri:
		numeri = {"count": numeri.get("count") or 0, "price": R._numero(numeri.get("price"))}
	return R.consumi(dati.get("products") or {}, numeri, (dati.get("balance") or {}).get("currency"))


@frappe.whitelist()
def get_telnyx_usage() -> dict:
	"""For Telnyx's page: the balance, this month's spend by kind, the last days'
	problems in words, the alerts. Nothing for whoever does not pay for the account."""
	livelli.verifica(collegamento.CENTRO)
	impostazioni = frappe.get_single(IMPOSTAZIONI)
	if not (collegamento.collegato(impostazioni) and _vede(impostazioni)):
		return {"visible": False}
	pagina = {
		"visible": True,
		"since": str(get_first_day(today())),
		"days": GIORNI,
		"alert": flt(impostazioni.spend_alert) or None,
		"balance_alert": flt(impostazioni.balance_alert) or None,
		"agency": _paga_l_agenzia(impostazioni),
	}
	try:
		dati = _dati(impostazioni)
	except ErroreTelnyx as errore:
		registra("DottorCloud: Telnyx's usage", errore)
		return {**pagina, "error": errore.in_parole()}
	mese = _mese(dati)
	for voce in mese["items"]:
		voce["label"] = _(voce["label"])
	bilancio = dati.get("balance") or {}
	nota = R.bilancio_in_parole(bilancio.get("balance"), bilancio.get("available_credit"))
	return {
		**pagina,
		"month": mese,
		"balance": {**bilancio, "note": _(nota) if nota else ""},
		"problems": [
			{**riga, "sentence": errori.in_parole(riga["code"], riga["telnyx"])}
			for riga in E.raggruppa(dati.get("failed") or [])
		],
	}


# ------------------------------------------------------------------ the alerts


def chi_avvisare(impostazioni) -> list[str]:
	"""Who hears that an alert was reached: whoever pays for the account - the
	centre's managers, or the agency on its own account."""
	agenzia = _paga_l_agenzia(impostazioni)
	return [
		utente
		for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
		if utente not in ("Administrator", "Guest")
		and _vede(impostazioni, utente)
		and agenzia == livelli.e_agenzia(utente)
	]


def controlla_gli_avvisi(impostazioni=None) -> list[str]:
	"""Every hour: the month's spend that reached the alert, told once a month; the
	balance down to its alert, told once until it is topped up. Returns the
	sentences told."""
	impostazioni = impostazioni or frappe.get_single(IMPOSTAZIONI)
	if not collegamento.collegato(impostazioni):
		return []
	if not (flt(impostazioni.spend_alert) or flt(impostazioni.balance_alert)):
		return []
	dati = _dati(impostazioni, fresco=True)
	valuta = ((dati.get("balance") or {}).get("currency") or "USD").upper()
	dette = []
	mese = str(get_first_day(today()))[:7]
	totale = _mese(dati)["total"]
	if R.da_avvisare_della_spesa(totale, impostazioni.spend_alert, impostazioni.spend_alert_told, mese):
		importo = fmt_money(flt(totale), precision=2, currency=valuta)
		soglia = fmt_money(flt(impostazioni.spend_alert), precision=2, currency=valuta)
		for utente in chi_avvisare(impostazioni):
			avvisa(utente, "Phone", N.SPESA_TELNYX, [importo, soglia])
		frappe.db.set_single_value(IMPOSTAZIONI, "spend_alert_told", mese)
		dette.append(N.SPESA_TELNYX)
	bilancio = (dati.get("balance") or {}).get("balance")
	azione = R.cosa_fare_del_bilancio(
		bilancio, impostazioni.balance_alert, bool(frappe.utils.cint(impostazioni.balance_alert_told))
	)
	if azione == "tell":
		importo = fmt_money(flt(bilancio), precision=2, currency=valuta)
		for utente in chi_avvisare(impostazioni):
			avvisa(utente, "Phone", N.CREDITO_TELNYX, [importo])
		frappe.db.set_single_value(IMPOSTAZIONI, "balance_alert_told", 1)
		dette.append(N.CREDITO_TELNYX)
	elif azione == "reset":
		frappe.db.set_single_value(IMPOSTAZIONI, "balance_alert_told", 0)
	return dette
