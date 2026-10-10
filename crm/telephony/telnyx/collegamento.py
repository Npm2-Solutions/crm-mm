# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Telnyx account, connected from DottorCloud (doc 65).

The centre pastes two codes once, on Settings > Phone > Telephony > Telnyx: its
API key and its public key (Mission Control > Keys & Credentials). DottorCloud
checks them, then makes its own resources in the account, named after the site:

- an **outbound voice profile** with the countries the centre may call, and only
  those, so a key that leaked could not call elsewhere either;
- a **TeXML application**, where Telnyx asks what a call to one of the centre's
  numbers does (the answering service, everyone ringing at once);
- a **credential connection**, where each person's browser registers with a
  credential of their own; its outgoing calls are parked and Telnyx asks
  DottorCloud first (`crm.integrations.telnyx.api.voice`): whether the call may
  leave, and which number it shows - never one the browser made up;
- a **messaging profile**, where the numbers' SMS come and go.

Then it points the account's numbers at itself: the free ones and the ones it
manages (its tag), never one on the centre's own switchboard, nor one on another
application that DottorCloud never managed. Every hour ``assicura()`` puts back
what somebody changed in the portal.

Telnyx has no space of its own for an ordinary account - no subaccount, no key
limited to part of it - so the key is kept, encrypted, on level 1 (the agency's),
and only DottorCloud's resources and its numbers are touched. The agency's account
works the same way (``dottorcloud_telnyx`` in ``common_site_config.json``), for a
centre with the agency's front desk: there the free numbers are not taken, as the
account holds other sites' numbers, and the key is read from the server's
configuration, never written on the site.

The codes travel in variables named ``*_secret``: a traceback that lists variables
hides those names.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_url, now_datetime

from crm import marchio
from crm.integrations.telnyx.utils import get_public_url
from crm.permissions import livelli
from crm.telephony import operatore
from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx.cliente import ErroreTelnyx, chiama, registra, tutte

#: The agency's account, in common_site_config.json.
CONF = "dottorcloud_telnyx"
#: Who connects the centre's account, and who connects the agency's.
CENTRO = "telefono.configura"
TECNICO = "tecnico.integrazioni"
IMPOSTAZIONI = "CRM Telnyx Settings"

#: Where Telnyx calls DottorCloud.
VOCE_IN_ARRIVO = "/api/method/crm.integrations.telnyx.api.incoming_call"
STATO_CHIAMATA = "/api/method/crm.integrations.telnyx.api.call_status"
DAL_BROWSER = "/api/method/crm.integrations.telnyx.api.voice"
SMS_IN_ARRIVO = "/api/method/crm.integrations.telnyx.api.sms"

#: What Telnyx may answer with instead of an answer.
NON_RISPONDE = (ErroreTelnyx,)


def configurazione_dell_agenzia() -> dict | None:
	"""The agency's account, from common_site_config.json; None without both codes."""
	conf = frappe.conf.get(CONF)
	if not isinstance(conf, dict):
		return None
	api_secret, pubblica = R.pulito(conf.get("api_key")), R.pulito(conf.get("public_key"))
	if R.cosa_manca(api_secret, pubblica):
		return None
	return {"api_key": api_secret, "public_key": pubblica}


def indirizzi() -> dict:
	"""Where Telnyx calls DottorCloud, on the address it knows the site by."""
	return {
		"voce": get_public_url(VOCE_IN_ARRIVO),
		"stato": get_public_url(STATO_CHIAMATA),
		"app": get_public_url(DAL_BROWSER),
		"sms": get_public_url(SMS_IN_ARRIVO),
	}


def in_parole(errore: Exception) -> str:
	"""Telnyx's refusal, or its silence, in the user's words."""
	if isinstance(errore, ErroreTelnyx):
		return errore.in_parole()
	return _("Telnyx does not answer: try again in a few minutes.")


# ---------------------------------------------------------------------------
# what the page reads


def _impostazioni():
	return frappe.get_single(IMPOSTAZIONI)


def chiave(impostazioni=None) -> str | None:
	"""The account's key: the agency's from the server's configuration, the
	centre's from its settings, decrypted only to be used."""
	impostazioni = impostazioni or _impostazioni()
	if impostazioni.account_owner == R.AGENZIA:
		return (configurazione_dell_agenzia() or {}).get("api_key")
	return impostazioni.get_password("api_key", raise_exception=False) or None


def pubblica(impostazioni=None) -> str | None:
	"""The account's public key, which Telnyx signs every webhook with."""
	impostazioni = impostazioni or _impostazioni()
	if impostazioni.account_owner == R.AGENZIA:
		return (configurazione_dell_agenzia() or {}).get("public_key")
	return impostazioni.public_key or None


def collegato(impostazioni=None) -> bool:
	impostazioni = impostazioni or _impostazioni()
	return bool(cint(impostazioni.enabled) and impostazioni.texml_application_id and chiave(impostazioni))


def segno() -> str:
	"""The tag on the numbers DottorCloud manages in the account."""
	return R.etichetta(get_url())


def nostre(impostazioni=None) -> set[str]:
	"""DottorCloud's connections in the account: its application and the browsers'."""
	impostazioni = impostazioni or _impostazioni()
	return {
		str(valore)
		for valore in (impostazioni.texml_application_id, impostazioni.credential_connection_id)
		if valore
	}


def stato() -> dict:
	"""The connection as the page shows it: whose account, the key masked, the
	resources, the numbers. The codes never leave the server."""
	impostazioni = _impostazioni()
	attivo = collegato(impostazioni)
	di = impostazioni.account_owner or ""
	numeri = frappe.get_all(
		"CRM Caller ID",
		filters={"provider": operatore.TELNYX, "source": "Account Number", "enabled": 1},
		fields=["routes_to_crm"],
	)
	agenzia = livelli.puo(TECNICO)
	return {
		"connected": attivo,
		"owner": di,
		"key": R.mascherata(chiave(impostazioni)) if attivo else "",
		"resources": {
			"name": R.nome_delle_risorse(get_url(), marchio.nome()),
			"texml_application": impostazioni.texml_application_id or "",
			"credential_connection": impostazioni.credential_connection_id or "",
			"outbound_voice_profile": impostazioni.outbound_voice_profile_id or "",
			"messaging_profile": impostazioni.messaging_profile_id or "",
		},
		"connected_on": impostazioni.connected_on,
		"connected_by": get_fullname(impostazioni.connected_by) if impostazioni.connected_by else "",
		"numbers": len(numeri),
		"not_reaching": sum(1 for numero in numeri if not numero.routes_to_crm),
		"agency": agenzia,
		"agency_account": agenzia and bool(configurazione_dell_agenzia()),
		"may_change": not attivo or di == R.CENTRO or agenzia,
		# the other carrier connected: this one waits for it to go
		"other": next((operatore.ETICHETTE[n] for n in operatore.collegati() if n != operatore.TELNYX), ""),
	}


@frappe.whitelist()
def get_telnyx_connection() -> dict:
	livelli.verifica(CENTRO)
	return stato()


# ---------------------------------------------------------------------------
# connecting


def _puo_cambiare(impostazioni):
	"""The centre changes its own connection; the agency's only the agency."""
	if collegato(impostazioni) and impostazioni.account_owner != R.CENTRO:
		livelli.verifica(
			TECNICO, messaggio=_("The agency connected this Telnyx account: only the agency changes it.")
		)


@frappe.whitelist(methods=["POST"])
def connect_telnyx(api_key: str, public_key: str) -> dict:
	"""Connect the centre's own account with its two codes."""
	livelli.verifica(CENTRO)
	_puo_cambiare(_impostazioni())
	operatore.libero_per(operatore.TELNYX)
	return _collega(api_key, public_key, R.CENTRO)


@frappe.whitelist(methods=["POST"])
def connect_agency_telnyx() -> dict:
	"""Connect the agency's account, for a centre with the agency's front desk."""
	livelli.verifica(TECNICO)
	operatore.libero_per(operatore.TELNYX)
	conf = configurazione_dell_agenzia()
	if not conf:
		frappe.throw(_("The agency's Telnyx account is not set up on this server."))
	return _collega(conf["api_key"], conf["public_key"], R.AGENZIA)


def _collega(api_key: str, public_key: str, di: str) -> dict:
	manca = R.cosa_manca(api_key, public_key)
	if manca:
		frappe.throw(_(manca))
	api_secret, pubblica_ = R.pulito(api_key), R.pulito(public_key)
	impostazioni = _impostazioni()
	try:
		# the key works, or Telnyx says why
		chiama("GET", "balance", api_secret)
		risorse = _risorse(api_secret, impostazioni)
		numeri = _numeri(api_secret, risorse, di)
	except NON_RISPONDE as errore:
		registra("DottorCloud: connecting Telnyx", errore)
		frappe.throw(in_parole(errore), title=_("Telnyx"))

	impostazioni.update(
		{
			"enabled": 1,
			"account_owner": di,
			# the agency's codes stay in the server's configuration
			"api_key": api_secret if di == R.CENTRO else "",
			"public_key": pubblica_ if di == R.CENTRO else "",
			"texml_application_id": risorse["applicazione"],
			"credential_connection_id": risorse["connessione"],
			"outbound_voice_profile_id": risorse["profilo_voce"],
			"messaging_profile_id": risorse["profilo_sms"],
			"connected_on": now_datetime(),
			"connected_by": frappe.session.user,
		}
	)
	impostazioni.flags.dal_collegamento = True
	impostazioni.save(ignore_permissions=True)
	_aggiorna_i_numeri()
	return {**stato(), "repaired": numeri["sistemati"], "trunked": numeri["altrove"]}


def _uno(percorso: str, api_secret: str, ident: str | None) -> dict | None:
	"""One resource by its id, or None when Telnyx has it no more."""
	if not ident:
		return None
	try:
		risposto = chiama("GET", f"{percorso}/{ident}", api_secret)
	except ErroreTelnyx as errore:
		if errore.stato == 404:
			return None
		raise
	return (risposto or {}).get("data") or None


#: How each list filters by name: Telnyx's spellings differ from one to the other.
FILTRI = {
	"outbound_voice_profiles": ("name", "filter[name][contains]"),
	"texml_applications": ("friendly_name", "filter[friendly_name]"),
	"messaging_profiles": ("name", "filter[name][contains]"),
	"credential_connections": ("connection_name", "filter[connection_name][contains]"),
}


def _per_nome(percorso: str, api_secret: str, nome: str) -> dict | None:
	"""A resource of DottorCloud's by its name: Telnyx filters by what a name
	contains, the name is compared whole here."""
	campo, filtro = FILTRI[percorso]
	for riga in tutte(percorso, api_secret, {filtro: nome[:60]}):
		if (riga.get(campo) or "") == nome:
			return riga
	return None


def _risorse(api_secret: str, impostazioni) -> dict:
	"""DottorCloud's resources in the account, found again or made, and put right."""
	nome = R.nome_delle_risorse(get_url(), marchio.nome())
	dove = indirizzi()
	paesi = R.paesi_del_profilo(_paesi(impostazioni))

	profilo_voce = _uno("outbound_voice_profiles", api_secret, impostazioni.outbound_voice_profile_id)
	profilo_voce = profilo_voce or _per_nome("outbound_voice_profiles", api_secret, nome)
	if not profilo_voce:
		profilo_voce = chiama(
			"POST",
			"outbound_voice_profiles",
			api_secret,
			corpo={
				"name": nome,
				"traffic_type": "conversational",
				"service_plan": "global",
				"whitelisted_destinations": paesi,
				"enabled": True,
			},
		)["data"]
	elif sorted(profilo_voce.get("whitelisted_destinations") or []) != paesi or not profilo_voce.get(
		"enabled", True
	):
		chiama(
			"PATCH",
			f"outbound_voice_profiles/{profilo_voce['id']}",
			api_secret,
			corpo={
				"name": profilo_voce.get("name") or nome,
				"whitelisted_destinations": paesi,
				"enabled": True,
			},
		)

	voluta = {
		"friendly_name": nome,
		"voice_url": dove["voce"],
		"voice_method": "post",
		"status_callback": dove["stato"],
		"status_callback_method": "post",
		"active": True,
		"outbound": {"outbound_voice_profile_id": str(profilo_voce["id"])},
	}
	applicazione = _uno("texml_applications", api_secret, impostazioni.texml_application_id)
	applicazione = applicazione or _per_nome("texml_applications", api_secret, nome)
	if not applicazione:
		applicazione = chiama("POST", "texml_applications", api_secret, corpo=voluta)["data"]
	elif _diversa(applicazione, voluta):
		chiama(
			"PATCH",
			f"texml_applications/{applicazione['id']}",
			api_secret,
			corpo={**voluta, "friendly_name": applicazione.get("friendly_name") or nome},
		)

	profilo_sms = _uno("messaging_profiles", api_secret, impostazioni.messaging_profile_id)
	profilo_sms = profilo_sms or _per_nome("messaging_profiles", api_secret, nome)
	voluto_sms = {
		"webhook_url": dove["sms"],
		"webhook_api_version": "2",
		"whitelisted_destinations": paesi,
		"enabled": True,
	}
	if not profilo_sms:
		profilo_sms = chiama("POST", "messaging_profiles", api_secret, corpo={"name": nome, **voluto_sms})[
			"data"
		]
	elif _diversa(profilo_sms, voluto_sms):
		chiama("PATCH", f"messaging_profiles/{profilo_sms['id']}", api_secret, corpo=voluto_sms)

	voluta_connessione = {
		"active": True,
		"sip_uri_calling_preference": "internal",
		"webhook_event_url": dove["app"],
		"webhook_api_version": "texml",
		"outbound": {"call_parking_enabled": True, "outbound_voice_profile_id": str(profilo_voce["id"])},
		"inbound": {"simultaneous_ringing": "enabled"},
	}
	connessione = _uno("credential_connections", api_secret, impostazioni.credential_connection_id)
	connessione = connessione or _per_nome("credential_connections", api_secret, nome)
	if not connessione:
		connessione = _nuova_connessione(api_secret, nome, voluta_connessione)
	elif _diversa(connessione, voluta_connessione):
		chiama("PATCH", f"credential_connections/{connessione['id']}", api_secret, corpo=voluta_connessione)

	return {
		"nome": nome,
		"profilo_voce": str(profilo_voce["id"]),
		"applicazione": str(applicazione["id"]),
		"profilo_sms": str(profilo_sms["id"]),
		"connessione": str(connessione["id"]),
	}


def _nuova_connessione(api_secret: str, nome: str, voluta: dict) -> dict:
	"""The browsers' credential connection. Its username and password are Telnyx's
	business only - each browser registers with a credential of its own - so they
	are drawn at random and kept nowhere; a username somebody else has is drawn
	again, once."""
	for _tentativo in range(2):
		try:
			return chiama(
				"POST",
				"credential_connections",
				api_secret,
				corpo={
					"connection_name": nome,
					"user_name": "dottorcloud" + secrets.token_hex(8),
					"password": secrets.token_urlsafe(24),
					**voluta,
				},
			)["data"]
		except ErroreTelnyx as errore:
			if errore.stato != 422:
				raise
			ultimo = errore
	raise ultimo


def _diversa(attuale: dict, voluta: dict) -> bool:
	"""Whether a resource as Telnyx describes it differs from what DottorCloud wants:
	only the keys wanted are compared, the nested ones one by one."""
	for campo, valore in voluta.items():
		if isinstance(valore, dict):
			if _diversa(attuale.get(campo) or {}, valore):
				return True
			continue
		presente = attuale.get(campo)
		if isinstance(valore, list):
			if sorted(presente or []) != sorted(valore):
				return True
		elif str(presente if presente is not None else "").lower() != str(valore).lower():
			return True
	return False


def _paesi(impostazioni) -> list[str]:
	from crm.telephony import uscita_regole

	return uscita_regole.paesi(impostazioni.allowed_countries)


def _numeri(api_secret: str, risorse: dict, di: str) -> dict:
	"""Every number of the account that is DottorCloud's pointed at it: the ones
	changed, and the ones left where they are (`R.cosa_fare`)."""
	applicazione, profilo = risorse["applicazione"], risorse["profilo_sms"]
	try:
		sms = {
			riga.get("phone_number"): bool((riga.get("features") or {}).get("sms"))
			for riga in tutte("phone_numbers/messaging", api_secret)
		}
	except ErroreTelnyx as errore:
		registra("DottorCloud: Telnyx's messaging numbers", errore)
		sms = {}
	try:
		tipi = {
			str(riga.get("id")): riga.get("record_type") or "" for riga in tutte("connections", api_secret)
		}
	except ErroreTelnyx as errore:
		registra("DottorCloud: Telnyx's connections", errore)
		tipi = {}
	sistemati, altrove = [], []
	for numero in tutte("phone_numbers", api_secret):
		descritto = {
			"connection_id": numero.get("connection_id"),
			"messaging_profile_id": numero.get("messaging_profile_id"),
			"tags": numero.get("tags") or [],
			"sms": sms.get(numero.get("phone_number")),
		}
		azione, cambi = R.cosa_fare(
			descritto,
			applicazione,
			profilo,
			{applicazione, risorse["connessione"]},
			tipi,
			segno(),
			prende_i_liberi=di == R.CENTRO,
		)
		if azione == "altrove":
			altrove.append(numero.get("phone_number"))
			continue
		if azione != "sistema":
			continue
		voce = {campo: cambi[campo] for campo in ("connection_id", "tags") if campo in cambi}
		if voce:
			chiama("PATCH", f"phone_numbers/{numero['id']}", api_secret, corpo=voce)
		if "messaging_profile_id" in cambi:
			chiama(
				"PATCH",
				f"phone_numbers/{numero['id']}/messaging",
				api_secret,
				corpo={"messaging_profile_id": cambi["messaging_profile_id"]},
			)
		sistemati.append(numero.get("phone_number"))
	return {"sistemati": sistemati, "altrove": altrove}


def _aggiorna_i_numeri():
	"""The list of the numbers, from what the account really has."""
	from crm.telephony import caller_ids

	try:
		caller_ids.sync(operatore.TELNYX)
	except NON_RISPONDE as errore:
		registra("DottorCloud: Telnyx's numbers", errore)


# ---------------------------------------------------------------------------
# the countries, and the name SMS leave with


def allinea_i_paesi(impostazioni=None, avvisa_se_no: bool = False) -> bool:
	"""The countries the centre may call, on DottorCloud's outbound voice profile;
	the same on its messaging profile, where the SMS may go. Returns whether Telnyx
	took them."""
	impostazioni = impostazioni or _impostazioni()
	api_secret = chiave(impostazioni)
	if not (collegato(impostazioni) and impostazioni.account_owner and api_secret):
		return False
	paesi = R.paesi_del_profilo(_paesi(impostazioni))
	try:
		profilo = _uno("outbound_voice_profiles", api_secret, impostazioni.outbound_voice_profile_id)
		if profilo and sorted(profilo.get("whitelisted_destinations") or []) != paesi:
			chiama(
				"PATCH",
				f"outbound_voice_profiles/{profilo['id']}",
				api_secret,
				corpo={"name": profilo.get("name"), "whitelisted_destinations": paesi},
			)
		if impostazioni.messaging_profile_id:
			chiama(
				"PATCH",
				f"messaging_profiles/{impostazioni.messaging_profile_id}",
				api_secret,
				corpo={"whitelisted_destinations": paesi},
			)
	except NON_RISPONDE as errore:
		registra("DottorCloud: Telnyx's countries", errore)
		if avvisa_se_no:
			frappe.msgprint(
				_("Telnyx did not take the countries now: {0} They are tried again within the hour.").format(
					in_parole(errore)
				),
				title=_("Countries That Can Be Called"),
			)
		return False
	return True


def allinea_il_mittente(impostazioni=None) -> None:
	"""The centre's name as the messaging profile's alphanumeric sender, when the
	SMS leave with it: Telnyx sends with a name only one its profile knows."""
	from crm.telephony import sms
	from crm.telephony import sms_regole as S

	impostazioni = impostazioni or _impostazioni()
	api_secret = chiave(impostazioni)
	if not (collegato(impostazioni) and impostazioni.messaging_profile_id and api_secret):
		return
	da = sms.mittente()
	if not da or sms.si_risponde(da) or S.problema_del_nome(da):
		return
	try:
		profilo = _uno("messaging_profiles", api_secret, impostazioni.messaging_profile_id) or {}
		if profilo and (profilo.get("alpha_sender") or "") != da:
			chiama(
				"PATCH",
				f"messaging_profiles/{impostazioni.messaging_profile_id}",
				api_secret,
				corpo={"alpha_sender": da},
			)
	except NON_RISPONDE as errore:
		registra("DottorCloud: Telnyx's SMS sender", errore)


# ---------------------------------------------------------------------------
# each person's browser


def credenziale(utente: str, nuova: bool = False) -> dict | None:
	"""The person's credential on DottorCloud's credential connection, made the
	first time their browser asks: its id and the SIP username a call rings."""
	impostazioni = _impostazioni()
	api_secret = chiave(impostazioni)
	if not (collegato(impostazioni) and impostazioni.credential_connection_id and api_secret):
		return None
	riga = frappe.db.get_value(
		"CRM Telephony Agent", utente, ["telnyx_credential_id", "telnyx_sip_username"], as_dict=True
	)
	if riga and riga.telnyx_credential_id and riga.telnyx_sip_username and not nuova:
		return {"id": riga.telnyx_credential_id, "sip_username": riga.telnyx_sip_username}
	fatta = chiama(
		"POST",
		"telephony_credentials",
		api_secret,
		corpo={
			"connection_id": impostazioni.credential_connection_id,
			"name": utente[:255],
			"tag": segno(),
		},
	)["data"]
	valori = {"telnyx_credential_id": fatta["id"], "telnyx_sip_username": fatta["sip_username"]}
	if riga:
		frappe.db.set_value("CRM Telephony Agent", utente, valori, update_modified=False)
	else:
		frappe.get_doc({"doctype": "CRM Telephony Agent", "user": utente, **valori}).insert(
			ignore_permissions=True
		)
	return {"id": fatta["id"], "sip_username": fatta["sip_username"]}


def gettone(utente: str) -> str | None:
	"""A token for the person's browser, a day long: Telnyx's JWT for their
	credential, made again when the portal removed it."""
	impostazioni = _impostazioni()
	api_secret = chiave(impostazioni)
	propria = credenziale(utente)
	if not (propria and api_secret):
		return None
	try:
		return chiama("POST", f"telephony_credentials/{propria['id']}/token", api_secret)
	except ErroreTelnyx as errore:
		if errore.stato != 404:
			raise
	propria = credenziale(utente, nuova=True)
	return chiama("POST", f"telephony_credentials/{propria['id']}/token", api_secret)


def _togli_le_credenziali(api_secret: str | None) -> None:
	"""Every person's credential, gone with the connection: a browser that kept a
	token calls no more once it expires, and cannot get another."""
	for riga in frappe.get_all(
		"CRM Telephony Agent",
		filters={"telnyx_credential_id": ["is", "set"]},
		fields=["name", "telnyx_credential_id"],
	):
		if api_secret:
			try:
				chiama("DELETE", f"telephony_credentials/{riga.telnyx_credential_id}", api_secret)
			except ErroreTelnyx as errore:
				if errore.stato != 404:
					registra("DottorCloud: a Telnyx credential", errore)
		frappe.db.set_value(
			"CRM Telephony Agent",
			riga.name,
			{"telnyx_credential_id": None, "telnyx_sip_username": None},
			update_modified=False,
		)


# ---------------------------------------------------------------------------
# checking, every hour and on the page


def _ripara(impostazioni) -> dict:
	"""DottorCloud's resources and numbers as it needs them; the account's balance."""
	api_secret = chiave(impostazioni)
	bilancio = (chiama("GET", "balance", api_secret) or {}).get("data") or {}
	risorse = _risorse(api_secret, impostazioni)
	numeri = _numeri(api_secret, risorse, impostazioni.account_owner)
	cambi = {
		campo: risorse[chiave_]
		for campo, chiave_ in (
			("texml_application_id", "applicazione"),
			("credential_connection_id", "connessione"),
			("outbound_voice_profile_id", "profilo_voce"),
			("messaging_profile_id", "profilo_sms"),
		)
		if str(impostazioni.get(campo) or "") != risorse[chiave_]
	}
	if cambi:
		frappe.db.set_single_value(IMPOSTAZIONI, cambi)
		impostazioni.update(cambi)
	_aggiorna_i_numeri()
	allinea_il_mittente(impostazioni)
	return {"bilancio": bilancio, **numeri}


def assicura():
	"""Every hour: put back what somebody changed in the portal, and tell whoever
	pays when the month's spend or the balance reaches its alert."""
	impostazioni = _impostazioni()
	if not (collegato(impostazioni) and impostazioni.account_owner):
		return
	try:
		_ripara(impostazioni)
	except NON_RISPONDE as errore:
		registra("DottorCloud: Telnyx's resources", errore)
	from crm.telephony.telnyx import consumi

	try:
		consumi.controlla_gli_avvisi(impostazioni)
	except NON_RISPONDE as errore:
		registra("DottorCloud: Telnyx's alerts", errore)


@frappe.whitelist(methods=["POST"])
def check_telnyx_connection() -> dict:
	"""What «Check» says: how the account is, and what was put back."""
	livelli.verifica(CENTRO)
	impostazioni = _impostazioni()
	if not collegato(impostazioni):
		frappe.throw(_("Telnyx is not connected."))
	try:
		fatto = _ripara(impostazioni)
	except NON_RISPONDE as errore:
		return {**stato(), "ok": False, "error": in_parole(errore)}
	from crm.telephony.telnyx import consumi_regole as C

	bilancio = fatto["bilancio"]
	nota = C.bilancio_in_parole(bilancio.get("balance"), bilancio.get("available_credit"))
	return {
		**stato(),
		"ok": True,
		"balance": bilancio.get("balance"),
		"available_credit": bilancio.get("available_credit"),
		"currency": bilancio.get("currency") or "USD",
		"note": _(nota) if nota else "",
		"repaired": fatto["sistemati"],
		"trunked": fatto["altrove"],
	}


# ---------------------------------------------------------------------------
# disconnecting


@frappe.whitelist(methods=["POST"])
def disconnect_telnyx() -> dict:
	"""Forget the codes and take every person's credential away. DottorCloud's
	resources and the numbers stay in the account, and connecting again finds
	them."""
	livelli.verifica(CENTRO)
	impostazioni = _impostazioni()
	_puo_cambiare(impostazioni)
	_togli_le_credenziali(chiave(impostazioni))
	impostazioni.update(
		{
			"enabled": 0,
			"api_key": "",
			"public_key": "",
			"connected_on": None,
			"connected_by": None,
		}
	)
	impostazioni.flags.dal_collegamento = True
	impostazioni.save(ignore_permissions=True)
	return stato()
