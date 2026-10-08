# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's own Stripe account, connected from DottorCloud (doc 60).

The money of an online payment goes to the centre's account and stays there:
DottorCloud resells nothing and holds nothing, as with Twilio (doc 52). The centre
pastes a secret or restricted key once, on Settings > Invoicing > Online payments;
DottorCloud asks Stripe whose account it is (name, country, currency; test or live
from the key's prefix), makes its own webhook endpoint on the account for the four
events it reads, and keeps the endpoint's signing secret. Disconnecting deletes
the endpoint there and forgets both.

Key and secret are Password fields; they travel in variables named ``*_secret``,
which a traceback hides, and never reach the page.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_url, now_datetime

from crm.pagamenti import cliente
from crm.pagamenti import regole as R
from crm.permissions import livelli

IMPOSTAZIONI = "CRM Stripe Settings"
#: Who connects the account and sets the deposits' rule: the centre's manager.
CAPACITA = "pagamenti.gestisci"
#: Where Stripe tells DottorCloud what happened.
WEBHOOK = "/api/method/crm.pagamenti.webhook.stripe"


def _impostazioni():
	return frappe.get_single(IMPOSTAZIONI)


def collegato(impostazioni=None) -> bool:
	impostazioni = impostazioni or _impostazioni()
	return bool(cint(impostazioni.enabled) and impostazioni.account_id)


def chiave(impostazioni=None) -> str:
	"""The account's key, for a call to Stripe; empty while not connected."""
	impostazioni = impostazioni or _impostazioni()
	if not collegato(impostazioni):
		return ""
	return impostazioni.get_password("secret_key", raise_exception=False) or ""


def segreto_del_webhook() -> str:
	impostazioni = _impostazioni()
	if not collegato(impostazioni):
		return ""
	return impostazioni.get_password("webhook_secret", raise_exception=False) or ""


def regola_dei_rimborsi() -> tuple[bool, int]:
	"""Whether a cancellation in time gives the deposit back, and how many hours
	before the appointment is in time."""
	impostazioni = _impostazioni()
	return bool(cint(impostazioni.refund_on_cancel)), cint(impostazioni.refund_hours)


def stato() -> dict:
	"""The connection as the page shows it: whose account, in which mode. The key
	masked; the secrets never leave the server."""
	impostazioni = _impostazioni()
	attivo = collegato(impostazioni)
	return {
		"connected": attivo,
		"mode": impostazioni.mode or "" if attivo else "",
		"account_id": impostazioni.account_id or "" if attivo else "",
		"account_name": impostazioni.account_name or "" if attivo else "",
		"country": impostazioni.country or "" if attivo else "",
		"currency": (impostazioni.currency or "").upper() if attivo else "",
		"key": R.mascherata(chiave(impostazioni)) if attivo else "",
		"webhook_url": impostazioni.webhook_url or get_url(WEBHOOK),
		"connected_on": impostazioni.connected_on if attivo else None,
		"connected_by": get_fullname(impostazioni.connected_by)
		if attivo and impostazioni.connected_by
		else "",
		"refund_on_cancel": bool(cint(impostazioni.refund_on_cancel)),
		"refund_hours": cint(impostazioni.refund_hours),
	}


@frappe.whitelist()
def get_stripe_connection() -> dict:
	livelli.verifica(CAPACITA)
	return stato()


@frappe.whitelist()
def online_payments_on() -> bool:
	"""Whether a service may ask a deposit online: for the service editor."""
	livelli.verifica("agenda.configura")
	return collegato()


# ---------------------------------------------------------------------------
# connecting


def _endpoint(stripe_secret: str) -> dict:
	"""DottorCloud's webhook endpoint on the account, made now."""
	return cliente.chiama(
		"POST",
		"webhook_endpoints",
		stripe_secret,
		{
			"url": get_url(WEBHOOK),
			"enabled_events": list(R.EVENTI),
			"api_version": cliente.VERSIONE,
			"description": f"DottorCloud · {frappe.local.site}",
			"metadata": {"site": frappe.local.site},
		},
	)


def _togli_endpoint(stripe_secret: str, endpoint: str | None) -> None:
	if not (stripe_secret and endpoint):
		return
	try:
		cliente.chiama("DELETE", R.percorso("webhook_endpoints", endpoint), stripe_secret)
	except cliente.ErroreStripe as errore:
		# gone already, or the key no longer works: nothing of the site's is left there
		if errore.stato not in (401, 404):
			frappe.log_error(title="Stripe: the old webhook endpoint", message=str(errore))


@frappe.whitelist(methods=["POST"])
def connect_stripe(stripe_secret: str) -> dict:
	"""Connect the centre's account with its key: checked with Stripe, the endpoint
	made on it, both kept."""
	livelli.verifica(CAPACITA)
	manca = R.cosa_manca(stripe_secret)
	if manca:
		frappe.throw(_(manca))
	stripe_secret = R.pulita(stripe_secret)
	precedente = _impostazioni()
	vecchia_secret = chiave(precedente)
	vecchio_endpoint = precedente.webhook_id
	try:
		conto = cliente.chiama("GET", "account", stripe_secret)
		endpoint = _endpoint(stripe_secret)
	except cliente.ErroreStripe as errore:
		frappe.throw(errore.in_parole(), title=_("Stripe"))
	webhook_secret = endpoint.get("secret") or ""
	if not webhook_secret:
		frappe.throw(_("Stripe did not give the webhook's signing secret: try again."))

	impostazioni = precedente
	impostazioni.update(
		{
			"enabled": 1,
			"secret_key": stripe_secret,
			"mode": R.modalita(stripe_secret),
			"account_id": conto.get("id") or "",
			"account_name": _nome_del_conto(conto),
			"country": conto.get("country") or "",
			"currency": conto.get("default_currency") or "",
			"webhook_id": endpoint.get("id") or "",
			"webhook_url": endpoint.get("url") or get_url(WEBHOOK),
			"webhook_secret": webhook_secret,
			"connected_on": now_datetime(),
			"connected_by": frappe.session.user,
		}
	)
	impostazioni.save(ignore_permissions=True)
	# the endpoint of before stops only now that the new one is kept
	if vecchio_endpoint and vecchio_endpoint != impostazioni.webhook_id:
		_togli_endpoint(vecchia_secret or stripe_secret, vecchio_endpoint)
	return stato()


def _nome_del_conto(conto: dict) -> str:
	profilo = conto.get("business_profile") or {}
	impostazioni = (conto.get("settings") or {}).get("dashboard") or {}
	return profilo.get("name") or impostazioni.get("display_name") or conto.get("email") or ""


@frappe.whitelist(methods=["POST"])
def check_stripe() -> dict:
	"""What «Check» says: the account answers, and its endpoint is there (made
	again where somebody deleted or switched it off in the dashboard)."""
	livelli.verifica(CAPACITA)
	impostazioni = _impostazioni()
	if not collegato(impostazioni):
		frappe.throw(_("Stripe is not connected."))
	stripe_secret = chiave(impostazioni)
	rifatto = False
	try:
		cliente.chiama("GET", "account", stripe_secret)
		try:
			endpoint = cliente.chiama(
				"GET", R.percorso("webhook_endpoints", impostazioni.webhook_id), stripe_secret
			)
		except cliente.ErroreStripe as errore:
			if errore.stato != 404:
				raise
			endpoint = None
		if not endpoint or endpoint.get("status") != "enabled" or endpoint.get("url") != get_url(WEBHOOK):
			nuovo = _endpoint(stripe_secret)
			if endpoint:
				_togli_endpoint(stripe_secret, endpoint.get("id"))
			impostazioni.update(
				{
					"webhook_id": nuovo.get("id"),
					"webhook_url": nuovo.get("url"),
					"webhook_secret": nuovo.get("secret"),
				}
			)
			impostazioni.save(ignore_permissions=True)
			rifatto = True
	except cliente.ErroreStripe as errore:
		return {**stato(), "ok": False, "error": errore.in_parole()}
	return {**stato(), "ok": True, "repaired": rifatto}


@frappe.whitelist(methods=["POST"])
def disconnect_stripe() -> dict:
	"""Delete the endpoint on Stripe and forget the key: the payments already made
	stay in the account, and in DottorCloud's register."""
	livelli.verifica(CAPACITA)
	impostazioni = _impostazioni()
	_togli_endpoint(chiave(impostazioni), impostazioni.webhook_id)
	impostazioni.update(
		{
			"enabled": 0,
			"secret_key": "",
			"mode": "",
			"account_id": "",
			"account_name": "",
			"country": "",
			"currency": "",
			"webhook_id": "",
			"webhook_url": "",
			"webhook_secret": "",
			"connected_on": None,
			"connected_by": None,
		}
	)
	impostazioni.save(ignore_permissions=True)
	return stato()


@frappe.whitelist(methods=["POST"])
def save_stripe_options(refund_on_cancel: int | str = 0, refund_hours: int | str = 24) -> dict:
	"""The deposits' rule: whether a cancellation in time gives the deposit back."""
	livelli.verifica(CAPACITA)
	impostazioni = _impostazioni()
	impostazioni.refund_on_cancel = cint(refund_on_cancel)
	impostazioni.refund_hours = max(cint(refund_hours), 0)
	impostazioni.save(ignore_permissions=True)
	return stato()
