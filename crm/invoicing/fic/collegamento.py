# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An issuing company connected to Fatture in Cloud, and kept connected.

The centre's manager presses «Connect» in Settings > Invoicing > Fatture in Cloud,
signs in there and allows the app; Fatture in Cloud sends the browser back with a
code, exchanged here for the access (a day long, renewed by itself every hour it is
near its end: `rinnova_i_token`) and its refresh token (a year from the last
renewal). Then the company there is chosen - by itself when the person has one -
and what it has (VAT rates, accounts, numerations) is read, each of ours matched
to one of its own where only one can be meant (`regole.scegli_tipo`).

The app is the agency's, one for every centre (`fic_client_id`, `fic_client_secret`
in common_site_config.json): Fatture in Cloud compares the address it sends back
to letter by letter, so every sign-in goes through the hub that Meta's and Google's
use (`meta_hub_url`), which hands the code back to the site named in the signed
state. What travels through Fatture in Cloud says nothing of the centre: a nonce,
which the site that asked turns back into its company.

The tokens never leave the server: the page reads what they allow, never them.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from functools import partial
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, get_url, now_datetime

from crm.invoicing.engine import voci
from crm.invoicing.fic import regole
from crm.invoicing.fic.client import AUTORIZZA, ErroreFiC, chiama, chiedi_token
from crm.permissions.livelli import puo

DOCTYPE = "CRM Fatture in Cloud"
AZIENDA = "CRM Invoicing Company"
#: The settings page where it is set up (Settings > Invoicing > Fatture in Cloud).
PAGINA = "Fatture in Cloud"
CALLBACK_PATH = "/api/method/crm.invoicing.fic.collegamento.callback"
#: What the app is allowed: invoices and credit notes, written and read; the
#: company's settings (VAT rates, accounts), only read. Nothing of its clients.
SCOPES = ("issued_documents.invoices:a", "issued_documents.credit_notes:a", "settings:r")
#: The access is renewed when it has less than this left.
MARGINE_MINUTI = 5
#: The hourly job renews it when it has less than this left.
MARGINE_ORE = 3
#: How long a sign-in may take, from the button to the way back.
STATO_SECONDI = 600
CHIAVE_STATO = "crm-fic-stato"

#: The VAT treatments always offered for matching: the ordinary rate, and the
#: exemption of healthcare where the company reports to the Sistema TS, the
#: flat-rate regime's where it is in it.
IVA_ORDINARIA = "22"
IVA_SANITARIA = "0|N4"
IVA_FORFETTARIA = "0|N2.2"
#: The payment methods always offered: cash, card, bank transfer, cheque.
METODI_DI_BASE = ("MP01", "MP08", "MP05", "MP02")


# ---------------------------------------------------------------------------- app


def client_id() -> str:
	return frappe.conf.get("fic_client_id") or ""


def _client_secret() -> str:
	return frappe.conf.get("fic_client_secret") or ""


def configurata() -> bool:
	"""Whether the agency set the app up on this server."""
	return bool(client_id() and _client_secret())


def _hub_url() -> str:
	return (frappe.conf.get("meta_hub_url") or "").rstrip("/")


def redirect_uri() -> str:
	"""Where Fatture in Cloud sends the browser back: the hub when there is one.
	The agency writes exactly this address in the app's page."""
	return (_hub_url() + CALLBACK_PATH) if _hub_url() else get_url(CALLBACK_PATH)


def _segreto_dello_stato() -> str:
	return (
		frappe.conf.get("meta_relay_secret") or frappe.local.conf.get("encryption_key") or frappe.local.site
	)


def _firma(payload: str) -> str:
	return hmac.new(_segreto_dello_stato().encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def _stato_firmato(nonce: str) -> str:
	payload = json.dumps({"t": int(time.time()), "site": get_url().rstrip("/"), "n": nonce})
	return f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{_firma(payload)}"


def leggi_stato(stato: str | None) -> dict | None:
	"""The state the sign-in left with, or None: missing, forged or too old."""
	if not stato or "." not in stato:
		return None
	try:
		codificato, firma = stato.rsplit(".", 1)
		payload = base64.urlsafe_b64decode(codificato.encode()).decode()
		if not hmac.compare_digest(firma, _firma(payload)):
			return None
		letto = json.loads(payload)
	except Exception:
		return None
	if int(time.time()) - int(letto.get("t") or 0) > STATO_SECONDI:
		return None
	return letto


# ---------------------------------------------------------------------- who may


def _verifica() -> None:
	if not puo("fatture.configura"):
		frappe.throw(_("You are not allowed to set up invoicing"), frappe.PermissionError)


def _azienda(company: str | None) -> str:
	"""The issuing company asked for, or the default one."""
	nome = company or (
		frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
		or frappe.db.get_value(AZIENDA, {"is_default": 1, "enabled": 1}, "name")
		or frappe.db.get_value(AZIENDA, {"enabled": 1}, "name")
	)
	if not nome or not frappe.db.exists(AZIENDA, nome):
		frappe.throw(_("No issuing company: set it up in Settings > Invoicing > Issuing company first"))
	return nome


def connessione(company: str):
	"""The company's connection, or None."""
	if not frappe.db.exists(DOCTYPE, company):
		return None
	return frappe.get_doc(DOCTYPE, company)


def collegata(company: str | None) -> bool:
	"""Whether the company has an access to Fatture in Cloud and a company there."""
	if not company:
		return False
	riga = frappe.db.get_value(DOCTYPE, company, ["fic_company_id", "needs_reconnect"], as_dict=True)
	return bool(riga and riga.fic_company_id and not riga.needs_reconnect)


def emette_con_fic(company: str | None) -> bool:
	"""Whether the company's invoices are issued in Fatture in Cloud: switched on,
	and with a company there. Asked at every issue: one read."""
	if not company:
		return False
	riga = frappe.db.get_value(DOCTYPE, company, ["active", "fic_company_id"], as_dict=True)
	return bool(riga and riga.active and riga.fic_company_id)


# ------------------------------------------------------------------------- tokens


def _scadenza(risposta: dict):
	secondi = int(risposta.get("expires_in") or 86400)
	return add_to_date(now_datetime(), seconds=max(secondi - 60, 60))


def _salva_token(company: str, risposta: dict, collegata_ora: bool = False) -> None:
	access_token = risposta.get("access_token")
	if not access_token:
		raise ErroreFiC(_("Fatture in Cloud answered something unreadable."))
	doc = connessione(company)
	if not doc:
		doc = frappe.new_doc(DOCTYPE)
		doc.company = company
	doc.access_token = access_token
	if risposta.get("refresh_token"):
		doc.refresh_token = risposta["refresh_token"]
	doc.access_expires_on = _scadenza(risposta)
	doc.refreshed_on = now_datetime()
	doc.needs_reconnect = 0
	doc.last_error = None
	if collegata_ora:
		doc.connected_by = frappe.session.user
		doc.connected_on = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.clear_document_cache(DOCTYPE, company)


def _salva_dopo_rollback(company: str, risposta: dict) -> None:
	"""A renewed access is Fatture in Cloud's from the moment it is given: the old
	refresh token is spent. Kept even when what asked for it was undone - after
	the other undoings still waiting (an invoice to delete there), which the commit
	would forget: it resets `after_rollback`."""
	frappe.db.after_rollback.run()
	if frappe.flags.in_test:
		return
	try:
		_salva_token(company, risposta)
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — after a rollback: the renewed access must not be lost with it
	except Exception:
		frappe.log_error(
			title=f"Fatture in Cloud: renewed access of {company}", message=frappe.get_traceback()
		)


def _da_ricollegare(company: str, motivo: str) -> None:
	frappe.db.set_value(
		DOCTYPE, company, {"needs_reconnect": 1, "last_error": motivo[:500]}, update_modified=False
	)
	frappe.clear_document_cache(DOCTYPE, company)


def _rinnova(company: str) -> str:
	"""A new access, one renewal at a time: the row is held while it is asked, and
	somebody who waited finds it renewed already."""
	frappe.db.get_value(DOCTYPE, company, "name", for_update=True)
	doc = frappe.get_doc(DOCTYPE, company)
	if doc.access_expires_on and get_datetime(doc.access_expires_on) > add_to_date(
		now_datetime(), minutes=MARGINE_MINUTI
	):
		return doc.get_password("access_token", raise_exception=False) or ""
	refresh_token = doc.get_password("refresh_token", raise_exception=False)
	if not refresh_token:
		raise ErroreFiC(_("Fatture in Cloud no longer recognises the access: connect it again."), stato=401)
	try:
		risposta = chiedi_token(
			{
				"grant_type": "refresh_token",
				"client_id": client_id(),
				"client_secret": _client_secret(),
				"refresh_token": refresh_token,
			}
		)
	except ErroreFiC as errore:
		if errore.stato in (400, 401):
			_da_ricollegare(company, str(errore))
		raise
	_salva_token(company, risposta)
	frappe.db.after_rollback.add(partial(_salva_dopo_rollback, company, risposta))
	return risposta["access_token"]


def token(company: str) -> str:
	"""An access good for the next minutes."""
	doc = connessione(company)
	if not doc or doc.needs_reconnect:
		raise ErroreFiC(
			_("Fatture in Cloud is not connected: connect it in Settings > Invoicing > Fatture in Cloud."),
			stato=401,
		)
	if doc.access_expires_on and get_datetime(doc.access_expires_on) > add_to_date(
		now_datetime(), minutes=MARGINE_MINUTI
	):
		access_token = doc.get_password("access_token", raise_exception=False)
		if access_token:
			return access_token
	return _rinnova(company)


def chiama_per(company: str, metodo: str, percorso: str, **opzioni):
	"""A call on the company's behalf: its access, renewed once if Fatture in
	Cloud says it is gone. `{c}` in the path is the company there."""
	doc = connessione(company)
	if not doc or not doc.fic_company_id:
		raise ErroreFiC(
			_("Fatture in Cloud is not connected: connect it in Settings > Invoicing > Fatture in Cloud."),
			stato=401,
		)
	percorso = percorso.replace("{c}", str(doc.fic_company_id))
	try:
		return chiama(metodo, percorso, token(company), **opzioni)
	except ErroreFiC as errore:
		if errore.stato != 401:
			raise
		frappe.db.set_value(DOCTYPE, company, "access_expires_on", None, update_modified=False)
		frappe.clear_document_cache(DOCTYPE, company)
		try:
			return chiama(metodo, percorso, _rinnova(company), **opzioni)
		except ErroreFiC as ancora:
			if ancora.stato == 401:
				_da_ricollegare(company, str(ancora))
			raise


def rinnova_i_token() -> None:
	"""Hourly: every access near its end is renewed, so that an invoice never waits
	for it and a year without issuing never loses it."""
	if not configurata():
		return
	soglia = add_to_date(now_datetime(), hours=MARGINE_ORE)
	for company in frappe.get_all(
		DOCTYPE,
		filters={"needs_reconnect": 0, "access_expires_on": ["<", soglia]},
		pluck="name",
	):
		try:
			_rinnova(company)
		except ErroreFiC:
			# «to connect again» is kept, and said on the page
			pass
		except Exception:
			if not frappe.flags.in_test:
				frappe.db.rollback()
			frappe.log_error(title=f"Fatture in Cloud: renewing {company}", message=frappe.get_traceback())
			continue
		if not frappe.flags.in_test:
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — each company's access on its own


# ------------------------------------------------------------------- signing in


@frappe.whitelist(methods=["POST"])
def connect(company: str | None = None) -> dict:
	"""The address of Fatture in Cloud's sign-in, for the popup."""
	_verifica()
	nome = _azienda(company)
	if not configurata():
		frappe.throw(_("The agency has not set up the connection to Fatture in Cloud on this server yet."))
	nonce = secrets.token_urlsafe(16)
	frappe.cache.set_value(
		f"{CHIAVE_STATO}:{nonce}",
		{"company": nome, "user": frappe.session.user},
		expires_in_sec=STATO_SECONDI,
	)
	parametri = {
		"response_type": "code",
		"client_id": client_id(),
		"redirect_uri": redirect_uri(),
		"scope": " ".join(SCOPES),
		"state": _stato_firmato(nonce),
	}
	return {"url": f"{AUTORIZZA}?{urlencode(parametri, quote_via=quote)}"}


def _passa_al_sito(sito: str, code: str | None, stato: str, altro: dict) -> None:
	"""The hub hands the code to the site that asked, nothing else: the code is worth
	nothing without the app's secret, and the address comes from the signed state."""
	parametri = {"state": stato}
	if code:
		parametri["code"] = code
	for chiave in ("error", "error_description"):
		if altro.get(chiave):
			parametri[chiave] = altro[chiave]
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = f"{sito.rstrip('/')}{CALLBACK_PATH}?{urlencode(parametri)}"


def _torna(errore: str | None = None) -> None:
	destinazione = "/oauth_connected?provider=fic"
	if errore:
		destinazione += f"&error={quote(errore[:300])}"
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = destinazione


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep: guest-whitelisted-method
def callback(code: str | None = None, state: str | None = None, **kwargs):
	"""Where Fatture in Cloud sends the browser back.

	Open to guests because the hub receives it in the browser of somebody signed in
	to their own site, not to the hub. Nothing in the address is trusted: the state
	must carry the signature only our sites can make, and on the site that asked,
	the session must be the one that pressed «Connect»."""
	letto = leggi_stato(state)
	if letto and (letto.get("site") or "").rstrip("/") != get_url().rstrip("/"):
		_passa_al_sito(letto["site"], code, state, kwargs)
		return
	if not letto:
		_torna(_("The sign-in took too long or did not come from here: try again."))
		return
	richiesta = frappe.cache.get_value(f"{CHIAVE_STATO}:{letto.get('n')}")
	frappe.cache.delete_value(f"{CHIAVE_STATO}:{letto.get('n')}")
	if not richiesta or richiesta.get("user") != frappe.session.user:
		_torna(_("The sign-in took too long or did not come from here: try again."))
		return
	if kwargs.get("error") or not code:
		_torna(kwargs.get("error_description") or _("The connection was cancelled in Fatture in Cloud."))
		return
	try:
		_verifica()
		company = richiesta["company"]
		risposta = chiedi_token(
			{
				"grant_type": "authorization_code",
				"client_id": client_id(),
				"client_secret": _client_secret(),
				"redirect_uri": redirect_uri(),
				"code": code,
			}
		)
		_salva_token(company, risposta, collegata_ora=True)
		trovate = regole.aziende(chiama("GET", "/user/companies", risposta["access_token"]))
		doc = connessione(company)
		doc.companies = json.dumps(trovate)
		gia = next((azienda for azienda in trovate if azienda["id"] == doc.fic_company_id), None)
		if gia or len(trovate) == 1:
			_scegli(doc, gia or trovate[0])
		else:
			doc.fic_company_id = None
			doc.fic_company_name = None
			doc.fic_vat_number = None
			doc.active = 0
			doc.save(ignore_permissions=True)
		if not frappe.flags.in_test:
			# nosemgrep: whitelisted-side-effect-on-get — Fatture in Cloud's way back is a GET: the signed state, the nonce and the session are checked above
			frappe.db.commit()
		_torna()
	except ErroreFiC as errore:
		frappe.db.rollback()
		_torna(str(errore))
	except frappe.PermissionError:
		frappe.db.rollback()
		_torna(_("You are not allowed to set up invoicing"))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Fatture in Cloud: connecting", message=frappe.get_traceback())
		_torna(_("The connection did not work: try again, or tell the agency."))


# --------------------------------------------------------- the company there


def _scegli(doc, azienda: dict) -> None:
	"""The company in Fatture in Cloud, and what it has. What it has can be read
	again from the page: a failure here does not lose the access."""
	doc.fic_company_id = int(azienda["id"])
	doc.fic_company_name = azienda.get("name") or ""
	doc.fic_vat_number = azienda.get("vat_number") or ""
	doc.save(ignore_permissions=True)
	frappe.clear_document_cache(DOCTYPE, doc.name)
	try:
		leggi_info(doc.name)
	except ErroreFiC as errore:
		frappe.db.set_value(DOCTYPE, doc.name, "last_error", str(errore)[:500], update_modified=False)


def leggi_info(company: str) -> dict:
	"""What the company has in Fatture in Cloud for an invoice and for a credit note:
	VAT rates, accounts, numerations. Kept on the connection, read again on demand."""
	fatture = (
		chiama_per(company, "GET", "/c/{c}/issued_documents/info", params={"type": "invoice"}) or {}
	).get("data") or {}
	note = (
		chiama_per(company, "GET", "/c/{c}/issued_documents/info", params={"type": "credit_note"}) or {}
	).get("data") or {}
	info = {
		"vat_types": [
			{
				campo: tipo.get(campo)
				for campo in (
					"id",
					"value",
					"description",
					"ei_type",
					"ei_description",
					"is_disabled",
					"default",
					"e_invoice",
				)
			}
			for tipo in fatture.get("vat_types_list") or []
		],
		"payment_accounts": [
			{campo: conto.get(campo) for campo in ("id", "name", "type")}
			for conto in fatture.get("payment_accounts_list") or []
		],
		"numerations": fatture.get("numerations") or {},
		"credit_numerations": note.get("numerations") or {},
		"ts_by_default": bool((fatture.get("extra_data_default_values") or {}).get("ts_communication")),
	}
	frappe.db.set_value(
		DOCTYPE,
		company,
		{"info": json.dumps(info), "info_fetched_on": now_datetime()},
		update_modified=False,
	)
	frappe.clear_document_cache(DOCTYPE, company)
	return info


@frappe.whitelist(methods=["POST"])
def choose_fic_company(company: str, fic_company: int) -> dict:
	"""The company in Fatture in Cloud, where the person who connected has more."""
	_verifica()
	doc = connessione(_azienda(company))
	if not doc:
		frappe.throw(
			_("Fatture in Cloud is not connected: connect it in Settings > Invoicing > Fatture in Cloud.")
		)
	trovate = json.loads(doc.companies or "[]")
	azienda = next((voce for voce in trovate if str(voce["id"]) == str(fic_company)), None)
	if not azienda:
		frappe.throw(_("That company is not among the ones of whoever connected Fatture in Cloud."))
	try:
		_scegli(doc, azienda)
	except ErroreFiC as errore:
		frappe.throw(str(errore), title=_("Fatture in Cloud"))
	return get_fic(doc.name)


@frappe.whitelist(methods=["POST"])
def refresh_fic(company: str | None = None) -> dict:
	"""Read again what the company has in Fatture in Cloud (a VAT rate added there)."""
	_verifica()
	nome = _azienda(company)
	try:
		leggi_info(nome)
	except ErroreFiC as errore:
		frappe.throw(str(errore), title=_("Fatture in Cloud"))
	return get_fic(nome)


@frappe.whitelist(methods=["POST"])
def disconnect_fic(company: str | None = None) -> dict:
	"""Forget the access and what was matched. The invoices issued there stay there
	and here; the next ones are numbered here again."""
	_verifica()
	nome = _azienda(company)
	if frappe.db.exists(DOCTYPE, nome):
		frappe.delete_doc(DOCTYPE, nome, ignore_permissions=True, force=True)
		frappe.get_doc(AZIENDA, nome).add_comment(
			"Info", _("Fatture in Cloud disconnected: the invoices are numbered here again.")
		)
	return get_fic(nome)


# ----------------------------------------------------------------- the matching


def _json(valore, vuoto):
	try:
		return json.loads(valore) if valore else vuoto
	except ValueError:
		return vuoto


def chiavi_usate(company: str) -> list[str]:
	"""The VAT treatments the company meets: the ordinary rate, the healthcare
	exemption or the flat rate as the company is, the ones of its service cards and
	of the last year's invoices."""
	emittente = frappe.db.get_value(AZIENDA, company, ["sender_category", "tax_regime"], as_dict=True) or {}
	chiavi = {IVA_ORDINARIA}
	if emittente.get("sender_category") not in (None, "", "non_sanitario"):
		chiavi.add(IVA_SANITARIA)
	if emittente.get("tax_regime") == "RF19":
		chiavi.add(IVA_FORFETTARIA)
	for scheda in frappe.get_all(
		"CRM Billable Service", filters={"enabled": 1}, fields=["vat_exempt", "vat_rate", "vat_nature"]
	):
		if scheda.vat_exempt:
			chiavi.add(IVA_SANITARIA)
		elif scheda.vat_nature:
			chiavi.add(regole.chiave_iva(0, scheda.vat_nature))
		elif scheda.vat_rate:
			chiavi.add(regole.chiave_iva(scheda.vat_rate))
	anno_fa = add_to_date(now_datetime(), years=-1)
	for riga in frappe.db.sql(
		"""select distinct s.vat_rate, s.vat_nature
		from `tabCRM Invoice Tax Summary` s join `tabCRM Invoice` f on f.name = s.parent
		where f.company = %s and f.docstatus = 1 and f.creation > %s""",
		(company, anno_fa),
		as_dict=True,
	):
		chiavi.add(regole.chiave_iva(riga.vat_rate, riga.vat_nature))
	return sorted(
		chiavi,
		key=lambda chiave: (regole.dividi_chiave(chiave)[0] == 0, -regole.dividi_chiave(chiave)[0], chiave),
	)


def metodi_usati(company: str) -> list[str]:
	usati = frappe.get_all(
		"CRM Invoice",
		filters={
			"company": company,
			"docstatus": 1,
			"creation": [">", add_to_date(now_datetime(), years=-1)],
		},
		pluck="payment_method",
		distinct=True,
	)
	return list(dict.fromkeys([*METODI_DI_BASE, *(metodo for metodo in usati if metodo)]))


def iva_in_parole(chiave: str) -> str:
	aliquota, natura = regole.dividi_chiave(chiave)
	if aliquota == 0 and natura:
		return _(voci.etichetta("natura", natura))
	return _("VAT {0}%").format(f"{aliquota:g}")


def metodo_in_parole(metodo: str) -> str:
	return _(voci.etichetta("modalita_pagamento", metodo))


def mappa(doc) -> dict:
	"""Which of the company's VAT rates, accounts and numerations stand for ours:
	what the centre chose where it chose, else the only one that can be meant."""
	info = _json(doc.info, {})
	scelte_iva = _json(doc.vat_map, {})
	scelte_conti = _json(doc.accounts_map, {})
	tipi = info.get("vat_types") or []
	conti = info.get("payment_accounts") or []
	chiavi = set(scelte_iva) | set(chiavi_usate(doc.company))
	return {
		"iva": {chiave: regole.scegli_tipo(chiave, tipi, scelte_iva.get(chiave)) for chiave in chiavi},
		"conti": {
			metodo: regole.conto_suggerito(metodo, conti, scelte_conti.get(metodo))
			for metodo in set(scelte_conti) | set(metodi_usati(doc.company))
		},
		"numerazioni": {
			"sdi": doc.numeration_sdi or "",
			"carta": doc.numeration_paper or "",
			"note": doc.numeration_credit or "",
		},
	}


def _etichetta_tipo(tipo: dict) -> str:
	"""A VAT rate of Fatture in Cloud as the centre named it there."""
	parole = (tipo.get("description") or "").strip()
	valore = f"{float(tipo.get('value') or 0):g}%"
	if parole and valore not in parole:
		return f"{valore} · {parole}"
	return parole or valore


def _da_fare(doc, chiavi) -> list[str]:
	"""What keeps the company from issuing there, in words."""
	mancano = []
	if not doc.fic_company_id:
		mancano.append(_("Choose the company in Fatture in Cloud."))
		return mancano
	nostra = frappe.db.get_value(AZIENDA, doc.company, "tax_id")
	if not regole.stessa_partita_iva(nostra, doc.fic_vat_number):
		mancano.append(
			_(
				"The VAT number of the company in Fatture in Cloud ({0}) is not the issuing company's ({1})."
			).format(doc.fic_vat_number, nostra)
		)
	iva = mappa(doc)["iva"]
	for chiave in chiavi:
		if iva.get(chiave) is None:
			mancano.append(_("Choose the VAT rate that stands for {0}.").format(iva_in_parole(chiave)))
	return mancano


def da_fare(company: str) -> list[str]:
	"""What keeps a company from issuing in Fatture in Cloud, for the list of what is
	missing (`prova.mancanze`)."""
	doc = connessione(company)
	if not doc:
		return []
	return _da_fare(doc, chiavi_usate(company))


def _consigli(doc, metodi) -> list[str]:
	"""What is worth choosing and stops nothing yet: an invoice paid that way waits
	for it."""
	if not doc.fic_company_id:
		return []
	conti = mappa(doc)["conti"]
	return [
		_("Choose where the payments made by {0} go.").format(metodo_in_parole(metodo))
		for metodo in metodi
		if conti.get(metodo) is None
	]


@frappe.whitelist()
def get_fic(company: str | None = None) -> dict:
	"""The page: whether the agency set it up, whether it is connected and to which
	company, what stands for what, and what is still to choose."""
	_verifica()
	nome = _azienda(company)
	emittente = frappe.db.get_value(
		AZIENDA, nome, ["company_name", "first_name", "last_name", "tax_id", "sender_category"], as_dict=True
	)
	risposta = {
		"company": nome,
		"company_label": emittente.company_name
		or " ".join(p for p in (emittente.first_name, emittente.last_name) if p)
		or nome,
		"configured": configurata(),
		# what the agency writes in the app's page: the agency's to read
		"redirect_uri": redirect_uri() if puo("tecnico.integrazioni") else None,
		"connected": False,
		"healthcare": emittente.sender_category not in (None, "", "non_sanitario"),
	}
	doc = connessione(nome)
	if not doc:
		return risposta
	info = _json(doc.info, {})
	mappa_ = mappa(doc)
	chiavi = chiavi_usate(nome)
	metodi = metodi_usati(nome)
	tipi = info.get("vat_types") or []
	conti = info.get("payment_accounts") or []
	anno = now_datetime().year
	risposta.update(
		{
			"connected": True,
			"needs_reconnect": bool(doc.needs_reconnect),
			"last_error": doc.last_error,
			"connected_by": frappe.utils.get_fullname(doc.connected_by) if doc.connected_by else None,
			"connected_on": str(doc.connected_on) if doc.connected_on else None,
			"fic_company": {
				"id": doc.fic_company_id,
				"name": doc.fic_company_name,
				"vat_number": doc.fic_vat_number,
			}
			if doc.fic_company_id
			else None,
			"to_choose": _json(doc.companies, []) if not doc.fic_company_id else [],
			"active": bool(doc.active),
			"ts_by": doc.ts_by or "dottorcloud",
			"info_fetched_on": str(doc.info_fetched_on) if doc.info_fetched_on else None,
			"vat": [
				{
					"key": chiave,
					"label": iva_in_parole(chiave),
					"value": mappa_["iva"].get(chiave),
					"options": [
						{"value": int(tipo["id"]), "label": _etichetta_tipo(tipo)}
						for tipo in regole.candidati(chiave, tipi)
					],
				}
				for chiave in chiavi
			],
			"accounts": [
				{
					"method": metodo,
					"label": metodo_in_parole(metodo),
					"value": mappa_["conti"].get(metodo),
					"options": [
						{"value": int(conto["id"]), "label": conto.get("name") or str(conto["id"])}
						for conto in conti
					],
				}
				for metodo in metodi
			],
			"numerations": {
				"sdi": {"value": doc.numeration_sdi or "", "options": regole.numerazioni(info, anno)},
				"paper": {"value": doc.numeration_paper or "", "options": regole.numerazioni(info, anno)},
				"credit": {
					"value": doc.numeration_credit or "",
					"options": regole.numerazioni({"numerations": info.get("credit_numerations")}, anno),
				},
			},
			"missing": _da_fare(doc, chiavi),
			"advice": _consigli(doc, metodi),
			# Fatture in Cloud reports to the Sistema TS by default: the centre may be
			# doing it there already
			"fic_sends_ts": bool(info.get("ts_by_default")),
		}
	)
	return risposta


@frappe.whitelist(methods=["POST"])
def save_fic(company: str, settings: str | dict) -> dict:
	"""What the centre chose: the VAT rates, the accounts, the numerations, who
	reports to the Sistema TS, and whether invoices are issued there from now on."""
	_verifica()
	nome = _azienda(company)
	doc = connessione(nome)
	if not doc:
		frappe.throw(
			_("Fatture in Cloud is not connected: connect it in Settings > Invoicing > Fatture in Cloud.")
		)
	scelte = frappe.parse_json(settings) if isinstance(settings, str) else (settings or {})
	info = _json(doc.info, {})
	if "vat" in scelte:
		tipi = info.get("vat_types") or []
		valide = {}
		for chiave, scelto in (scelte.get("vat") or {}).items():
			if scelto in (None, ""):
				continue
			if not any(str(tipo["id"]) == str(scelto) for tipo in regole.candidati(chiave, tipi)):
				frappe.throw(
					_("That VAT rate of Fatture in Cloud does not say {0}.").format(iva_in_parole(chiave))
				)
			valide[chiave] = int(scelto)
		doc.vat_map = json.dumps(valide)
	if "accounts" in scelte:
		conti = {str(conto["id"]) for conto in info.get("payment_accounts") or []}
		valide = {}
		for metodo, scelto in (scelte.get("accounts") or {}).items():
			if scelto in (None, ""):
				continue
			if str(scelto) not in conti:
				frappe.throw(_("That account is not among the company's in Fatture in Cloud."))
			valide[metodo] = int(scelto)
		doc.accounts_map = json.dumps(valide)
	numerazioni = scelte.get("numerations") or {}
	for chiave, campo in (
		("sdi", "numeration_sdi"),
		("paper", "numeration_paper"),
		("credit", "numeration_credit"),
	):
		if chiave in numerazioni:
			doc.set(campo, (numerazioni.get(chiave) or "").strip())
	if scelte.get("ts_by") in ("dottorcloud", "fatture_in_cloud"):
		doc.ts_by = scelte["ts_by"]
	if "active" in scelte:
		attiva = bool(scelte.get("active"))
		if attiva:
			mancano = _da_fare(doc, chiavi_usate(nome))
			if mancano:
				frappe.throw("<br>".join(mancano), title=_("Not ready to issue in Fatture in Cloud"))
		if attiva != bool(doc.active):
			frappe.get_doc(AZIENDA, nome).add_comment(
				"Info",
				_("From now on the invoices are issued in Fatture in Cloud.")
				if attiva
				else _("From now on the invoices are numbered here again."),
			)
		doc.active = 1 if attiva else 0
	doc.save(ignore_permissions=True)
	frappe.clear_document_cache(DOCTYPE, nome)
	return get_fic(nome)
