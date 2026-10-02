# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Twilio account, connected from DottorCloud (doc 52).

The centre pastes its Account SID and Auth Token once, on Settings > Phone >
Telephony > Twilio. DottorCloud uses them in that moment to make its own space in
the account - a subaccount named after the site - with its own key and its TwiML
app, points every number of the space at itself, and keeps only the space's codes:
the account's token is never stored, and the rest of the account is neither read
nor touched. Twilio bills the space to the centre's account.

Codes of a subaccount make that subaccount the space: a centre connecting again,
or the agency that made one by hand. The agency's own account works the same way
(``dottorcloud_twilio`` in ``common_site_config.json``), for a centre with the
agency's front desk: the space lives there and the agency pays.

Every hour ``assicura()`` puts back what somebody changed in the console: the app's
address, a number's. Only in a space: an account connected by hand in the Desk
may hold other sites' numbers, and is never touched. A number handed to a SIP
trunk is left as it is.

Twilio Connect would be a login instead of two codes, but a Connect app may not
manage numbers, use the regulatory API every Italian number needs, nor make the
key the browser calls with (Twilio's "Known Limitations for Connect Apps").

The codes travel in variables named ``*_token`` and ``*_secret``: a traceback that
lists variables hides those names.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_url, now_datetime
from requests import RequestException
from twilio.base.exceptions import TwilioException, TwilioRestException
from twilio.rest import Client

from crm import marchio
from crm.integrations.twilio.utils import get_public_url
from crm.marchio import con_nome
from crm.permissions import livelli
from crm.telephony import collegamento_regole as R

#: The agency's account, in common_site_config.json.
CONF = "dottorcloud_twilio"
#: Who connects the centre's account, and who connects the agency's.
CENTRO = "telefono.configura"
TECNICO = "tecnico.integrazioni"
IMPOSTAZIONI = "CRM Twilio Settings"

#: Where Twilio calls DottorCloud: a number's calls and messages, the browser's calls.
VOCE_IN_ARRIVO = "/api/method/crm.integrations.twilio.api.twilio_incoming_call_handler"
SMS_IN_ARRIVO = "/api/method/crm.integrations.twilio.api.incoming_sms_handler"
DAL_BROWSER = "/api/method/crm.integrations.twilio.api.voice"

#: What Twilio may answer with instead of an answer.
NON_RISPONDE = (TwilioException, RequestException)


def configurazione_dell_agenzia() -> dict | None:
	"""The agency's account, from common_site_config.json; None without both codes."""
	conf = frappe.conf.get(CONF)
	if not isinstance(conf, dict):
		return None
	account_sid, auth_token = R.pulito(conf.get("account_sid")), R.pulito(conf.get("auth_token"))
	if not (account_sid and auth_token):
		return None
	return {"account_sid": account_sid, "auth_token": auth_token}


def indirizzi() -> dict:
	"""Where Twilio calls DottorCloud, on the address it knows the site by."""
	return {
		"voce": get_public_url(VOCE_IN_ARRIVO),
		"sms": get_public_url(SMS_IN_ARRIVO),
		"app": get_public_url(DAL_BROWSER),
	}


def in_parole(errore: Exception) -> str:
	"""Twilio's refusal, or its silence, in the user's words."""
	if isinstance(errore, TwilioRestException):
		frase, argomenti = R.errore_in_parole(errore.status, errore.code)
	else:
		frase, argomenti = R.errore_in_parole(None)
	return _(frase).format(*argomenti)


def _registra(titolo: str, errore: Exception):
	"""An error of Twilio's in the log, with what Twilio said and never the codes."""
	stato = getattr(errore, "status", "")
	codice = getattr(errore, "code", "")
	frappe.log_error(title=titolo, message=f"{type(errore).__name__} {stato} {codice}: {errore}"[:1000])


# ---------------------------------------------------------------------------
# what the page reads


def _impostazioni():
	return frappe.get_single(IMPOSTAZIONI)


def collegato(impostazioni=None) -> bool:
	impostazioni = impostazioni or _impostazioni()
	return bool(cint(impostazioni.enabled) and impostazioni.account_sid)


def stato() -> dict:
	"""The connection as the page shows it: whose account, which space, the numbers.
	The SIDs masked; the codes never leave the server."""
	impostazioni = _impostazioni()
	attivo = collegato(impostazioni)
	di = impostazioni.account_owner or ""
	numeri = frappe.get_all(
		"CRM Caller ID",
		filters={"provider": "twilio", "source": "Account Number", "enabled": 1},
		fields=["routes_to_crm"],
	)
	agenzia = livelli.puo(TECNICO)
	return {
		"connected": attivo,
		# connected by hand in the Desk, before doc 52: the agency's
		"owner": di if di or not attivo else "Manual",
		"main_account": {
			"sid": R.mascherato(impostazioni.main_account_sid),
			"name": impostazioni.main_account_name or "",
		},
		"space": {
			"sid": R.mascherato(impostazioni.space_sid or impostazioni.account_sid),
			"name": impostazioni.space_name or "",
		},
		"connected_on": impostazioni.connected_on,
		"connected_by": get_fullname(impostazioni.connected_by) if impostazioni.connected_by else "",
		"numbers": len(numeri),
		"not_reaching": sum(1 for numero in numeri if not numero.routes_to_crm),
		"agency": agenzia,
		"agency_account": agenzia and bool(configurazione_dell_agenzia()),
		"may_change": not attivo or di == R.CENTRO or agenzia,
	}


@frappe.whitelist()
def get_twilio_connection() -> dict:
	livelli.verifica(CENTRO)
	return stato()


# ---------------------------------------------------------------------------
# connecting


def _puo_cambiare(impostazioni):
	"""The centre changes its own connection; the agency's, or one made by hand in
	the Desk, only the agency."""
	if collegato(impostazioni) and impostazioni.account_owner != R.CENTRO:
		livelli.verifica(
			TECNICO, messaggio=_("The agency connected this Twilio account: only the agency changes it.")
		)


@frappe.whitelist(methods=["POST"])
def connect_twilio(account_sid: str, auth_token: str) -> dict:
	"""Connect the centre's own account with its two codes: the token is used now
	and not kept."""
	livelli.verifica(CENTRO)
	_puo_cambiare(_impostazioni())
	return _collega(account_sid, auth_token, R.CENTRO)


@frappe.whitelist(methods=["POST"])
def connect_agency_twilio() -> dict:
	"""Connect the agency's account, for a centre with the agency's front desk."""
	livelli.verifica(TECNICO)
	conf = configurazione_dell_agenzia()
	if not conf:
		frappe.throw(_("The agency's Twilio account is not set up on this server."))
	return _collega(conf["account_sid"], conf["auth_token"], R.AGENZIA)


def _collega(account_sid: str, auth_token: str, di: str) -> dict:
	manca = R.cosa_manca(account_sid, auth_token)
	if manca:
		frappe.throw(_(manca))
	account_sid, auth_token = R.pulito(account_sid), R.pulito(auth_token)
	try:
		principale = Client(account_sid, auth_token)
		conto = principale.api.v2010.accounts(account_sid).fetch()
		if conto.owner_account_sid and conto.owner_account_sid != conto.sid:
			# a subaccount: it is the space, and its own token is the one to keep
			spazio, space_token = conto, auth_token
			padre_sid, padre_nome = conto.owner_account_sid, ""
		else:
			spazio = _spazio(principale, conto)
			space_token = spazio.auth_token
			padre_sid, padre_nome = conto.sid, conto.friendly_name
		if not space_token:
			frappe.throw(
				con_nome(_("Twilio did not give the codes of {brand}'s space: try again in a few minutes."))
			)
		cliente = Client(spazio.sid, space_token)
		chiave = cliente.new_keys.create(friendly_name=R.NOME)
		app = _app(cliente)
		numeri = _numeri(cliente)
	except NON_RISPONDE as errore:
		frappe.throw(in_parole(errore), title=_("Twilio"))

	precedente = _impostazioni()
	vecchia = precedente.api_key if precedente.space_sid == spazio.sid else None
	impostazioni = precedente
	impostazioni.update(
		{
			"enabled": 1,
			"account_sid": spazio.sid,
			"auth_token": space_token,
			"api_key": chiave.sid,
			"api_secret": chiave.secret,
			"twiml_sid": app.sid,
			"app_name": R.NOME,
			"account_owner": di,
			"main_account_sid": padre_sid,
			"main_account_name": padre_nome,
			"space_sid": spazio.sid,
			"space_name": spazio.friendly_name,
			"connected_on": now_datetime(),
			"connected_by": frappe.session.user,
		}
	)
	impostazioni.flags.dal_collegamento = True
	impostazioni.save(ignore_permissions=True)

	# the keys of before stop working only now that the new one is kept
	_togli_le_chiavi(cliente, tranne=chiave.sid, anche=vecchia)
	_aggiorna_i_numeri()
	return {**stato(), "repaired": numeri["sistemati"], "trunked": numeri["a_un_tronco"]}


def _spazio(principale, conto):
	"""DottorCloud's space in the account: the one remembered, else the one with the
	site's name, else a new one. A suspended one is woken; a closed one stays closed."""
	nome = R.nome_dello_spazio(get_url(), marchio.nome())
	candidati = []
	ricordato = frappe.db.get_single_value(IMPOSTAZIONI, "space_sid")
	if ricordato and ricordato != conto.sid:
		try:
			candidati.append(principale.api.v2010.accounts(ricordato).fetch())
		except TwilioRestException as errore:
			if errore.status != 404:
				raise
	candidati.extend(principale.api.v2010.accounts.list(friendly_name=nome))
	for spazio in candidati:
		if spazio.sid == conto.sid or spazio.owner_account_sid != conto.sid or spazio.status == "closed":
			continue
		if spazio.status == "suspended":
			spazio = principale.api.v2010.accounts(spazio.sid).update(status="active")
		return spazio
	return principale.api.v2010.accounts.create(friendly_name=nome)


def _app(cliente):
	"""DottorCloud's TwiML app in the space, with the address of the browser's calls."""
	indirizzo = indirizzi()["app"]
	for app in cliente.applications.list(friendly_name=R.NOME):
		cambi = R.app_da_sistemare({"voice_url": app.voice_url, "voice_method": app.voice_method}, indirizzo)
		if cambi:
			app = cliente.applications(app.sid).update(**cambi)
		return app
	return cliente.applications.create(friendly_name=R.NOME, voice_url=indirizzo, voice_method="POST")


def _numeri(cliente) -> dict:
	"""Every number of the space pointed at DottorCloud: the ones changed, and the
	ones a SIP trunk takes, left as they are."""
	dove = indirizzi()
	sistemati, a_un_tronco = [], []
	for numero in cliente.incoming_phone_numbers.list():
		if numero.trunk_sid:
			a_un_tronco.append(numero.phone_number)
			continue
		descritto = {
			"voice_url": numero.voice_url,
			"voice_method": numero.voice_method,
			"voice_application_sid": numero.voice_application_sid,
			"sms_url": numero.sms_url,
			"sms_method": numero.sms_method,
			"sms_application_sid": numero.sms_application_sid,
			"capabilities": numero.capabilities or {},
		}
		cambi = R.da_sistemare(descritto, dove["voce"], dove["sms"])
		if cambi:
			cliente.incoming_phone_numbers(numero.sid).update(**cambi)
			sistemati.append(numero.phone_number)
	return {"sistemati": sistemati, "a_un_tronco": a_un_tronco}


def _togli_le_chiavi(cliente, tranne: str, anche: str | None = None):
	"""DottorCloud's keys of before, in the space: nobody has their secret any more."""
	try:
		vecchie = [k.sid for k in cliente.keys.list() if k.friendly_name == R.NOME and k.sid != tranne]
		if anche and anche != tranne and anche not in vecchie:
			vecchie.append(anche)
		for sid in vecchie:
			cliente.keys(sid).delete()
	except NON_RISPONDE as errore:
		# the new key works all the same; the old ones go at the next connection
		_registra("DottorCloud: Twilio's old keys", errore)


def _aggiorna_i_numeri():
	"""The list of the numbers, from what the space really has."""
	from crm.telephony import caller_ids

	try:
		caller_ids.sync("twilio")
	except NON_RISPONDE as errore:
		_registra("DottorCloud: Twilio's numbers", errore)


# ---------------------------------------------------------------------------
# checking, every hour and on the page


def _ripara(impostazioni) -> dict:
	"""The space's app and numbers as DottorCloud needs them; the account as Twilio
	describes it."""
	auth_token = impostazioni.get_password("auth_token", raise_exception=False)
	cliente = Client(impostazioni.account_sid, auth_token)
	conto = cliente.api.v2010.accounts(impostazioni.account_sid).fetch()
	app = _app(cliente)
	numeri = _numeri(cliente)
	if app.sid != impostazioni.twiml_sid:
		frappe.db.set_single_value(IMPOSTAZIONI, "twiml_sid", app.sid)
	if numeri["sistemati"]:
		_aggiorna_i_numeri()
	return {"conto": conto, **numeri}


def assicura():
	"""Every hour: put back what somebody changed in the console. Only in a space
	DottorCloud made or was given; an account connected by hand may hold other
	sites' numbers."""
	impostazioni = _impostazioni()
	if not (collegato(impostazioni) and impostazioni.account_owner):
		return
	try:
		_ripara(impostazioni)
	except NON_RISPONDE as errore:
		_registra("DottorCloud: Twilio's space", errore)


@frappe.whitelist(methods=["POST"])
def check_twilio_connection() -> dict:
	"""What «Check» says: how the account is, and what was put back."""
	livelli.verifica(CENTRO)
	impostazioni = _impostazioni()
	if not collegato(impostazioni):
		frappe.throw(_("Twilio is not connected."))
	try:
		if impostazioni.account_owner:
			fatto = _ripara(impostazioni)
		else:
			# connected by hand: looked at, never changed
			auth_token = impostazioni.get_password("auth_token", raise_exception=False)
			conto = (
				Client(impostazioni.account_sid, auth_token)
				.api.v2010.accounts(impostazioni.account_sid)
				.fetch()
			)
			fatto = {"conto": conto, "sistemati": [], "a_un_tronco": []}
	except NON_RISPONDE as errore:
		return {**stato(), "ok": False, "error": in_parole(errore)}
	conto = fatto["conto"]
	nota = R.stato_in_parole(conto.status, conto.type)
	return {
		**stato(),
		"ok": True,
		"status": conto.status,
		"type": conto.type,
		"note": _(nota) if nota else "",
		"repaired": fatto["sistemati"],
		"trunked": fatto["a_un_tronco"],
	}


# ---------------------------------------------------------------------------
# disconnecting


@frappe.whitelist(methods=["POST"])
def disconnect_twilio() -> dict:
	"""Forget the space's codes and take DottorCloud's key away. The space and its
	numbers stay in the account, and connecting again finds them."""
	livelli.verifica(CENTRO)
	impostazioni = _impostazioni()
	_puo_cambiare(impostazioni)
	if impostazioni.account_owner and impostazioni.account_sid and impostazioni.api_key:
		auth_token = impostazioni.get_password("auth_token", raise_exception=False)
		try:
			Client(impostazioni.account_sid, auth_token).keys(impostazioni.api_key).delete()
		except NON_RISPONDE as errore:
			_registra("DottorCloud: Twilio's key", errore)
	impostazioni.update(
		{
			"enabled": 0,
			"account_sid": "",
			"auth_token": "",
			"api_key": "",
			"api_secret": "",
			"twiml_sid": "",
			"connected_on": None,
			"connected_by": None,
		}
	)
	impostazioni.flags.dal_collegamento = True
	impostazioni.save(ignore_permissions=True)
	return stato()
