# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Where a form is filled beyond the operator's screen (design.md, "La firma").

**At home.** The centre sends a link; the message says only that there are forms
to fill before the visit, never which: the title of a consent can say what the
visit is for. It goes to the person's email or, for somebody a parent or
guardian signs for, to theirs. Opening it asks for a code sent to the same
address; with the code the forms show, and are read, answered and signed. The
link and the code are the credentials, so the register says when the link was
sent, opened, the code sent and checked, and from where.

**At the desk, on a tablet.** The operator hands the tablet over: the CRM logs
them out on that device and opens the same page, with no code, for this person
and these forms only. The operator has seen who holds it. The first opening
binds the page to that browser: the address alone opens nothing afterwards.

One link opens one or more forms: the first request holds the link, the code
and the session, the others were sent with it (``via``). The page may do the
least: open its own forms, save them, sign them, download the signed copy while
the session lasts. Every secret is kept as a SHA-256 only, and every call is
rate limited.

A form whose signatures are not the person's own simple one - the operator's,
or an advanced one - is filled away from the desk and signed at it: the page
says so, and the form waits in the person's Forms tab.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, cint, escape_html, get_datetime, get_url, getdate, now_datetime

from crm.moduli import compilazioni, modelli, traccia
from crm.moduli import schema as S
from crm.permissions import livelli

RICHIESTA = compilazioni.RICHIESTA
#: How long a link stays good, and a tablet handed over.
GIORNI_LINK = 7
MINUTI_TABLET = 120
#: A code lasts ten minutes; a session an hour from the last thing done with it.
MINUTI_CODICE = 10
MINUTI_SESSIONE = 60
TENTATIVI_CODICE = 5
CODICI_ALL_ORA = 3
APERTE = ("Sent", "Opened")


def _segreto() -> str:
	"""A link or a session: 192 random bits, shown once and kept as a hash."""
	return secrets.token_urlsafe(24)


def _codice() -> str:
	return f"{secrets.randbelow(10**6):06d}"


def _impronta(segreto: str) -> str:
	return hashlib.sha256(segreto.encode("utf-8")).hexdigest()


def _uguali(a: str | None, b: str | None) -> bool:
	return bool(a) and bool(b) and hmac.compare_digest(a, b)


def firmabile_da_sola(schema: dict) -> list[str]:
	"""What keeps a form from being signed by the person alone: an operator's
	signature, or a level a finger cannot give. Empty when nothing does."""
	motivi = []
	for campo in S.campi(schema):
		if campo.get("type") != "signature":
			continue
		if (campo.get("signer") or "patient") == "operator":
			motivi.append(_("{0} is signed by the operator").format(campo.get("label")))
		elif (campo.get("level") or "simple") != "simple":
			motivi.append(_("{0} needs an {1} signature").format(campo.get("label"), _(campo.get("level"))))
	return motivi


def _nascosta(email: str) -> str:
	nome, _chiocciola, dominio = email.partition("@")
	return (nome[:1] + "•" * max(len(nome) - 1, 2)) + ("@" + dominio if dominio else "")


def nome_del_centro() -> str:
	"""The centre's name: the CRM's brand (Settings > Brand), never the booking
	page's own title nor Frappe's. Empty when there is none."""
	marchio = (frappe.db.get_single_value("FCRM Settings", "brand_name") or "").strip()
	if marchio:
		return marchio
	nome = (frappe.db.get_single_value("Website Settings", "app_name") or "").strip()
	return nome if nome.lower() not in ("", "frappe", "frappe crm") else ""


# ------------------------------------------------------------------ who it goes to


def _minorenne(lead: str) -> bool:
	from crm.persone import legami

	nascita = frappe.db.get_value(
		"CRM Billing Profile", {"party_type": "CRM Lead", "party": lead}, "birth_date"
	)
	return bool(legami.minorenne(getdate(nascita) if nascita else None, getdate()))


def _rappresentanti(lead: str) -> list[str]:
	from crm.persone import collegate

	return collegate.rappresentanti_di(lead)


def destinatario(lead: str) -> dict:
	"""Where a link for this person goes: to whoever signs for them if somebody
	does (a parent, a guardian), else to their own email. ``reason`` says why it
	cannot go anywhere."""
	rappresentanti = _rappresentanti(lead)
	for chi in rappresentanti:
		email = frappe.db.get_value("CRM Lead", chi, "email")
		if email:
			return {"lead": chi, "email": email, "given_by": chi}
	if rappresentanti:
		return {"reason": _("Nobody who signs for them has an email: hand the tablet over at the desk")}
	if _minorenne(lead):
		return {
			"reason": _(
				"A minor's forms are answered by a parent or guardian: add them to the related people first"
			)
		}
	email = frappe.db.get_value("CRM Lead", lead, "email")
	if not email:
		return {"reason": _("This person has no email: hand the tablet over at the desk")}
	return {"lead": lead, "email": email, "given_by": None}


def _posta_in_uscita() -> bool:
	from frappe.email.doctype.email_account.email_account import EmailAccount

	return bool(EmailAccount.find_outgoing(match_by_doctype=RICHIESTA))


def _modelli_pubblicati() -> list[dict]:
	"""The published forms the session may send, and whether each is signed at the desk."""
	clinico = compilazioni.legge_dati_clinici()
	righe = []
	for riga in frappe.get_all(
		modelli.MODELLO,
		filters={"enabled": 1, "current_version": ("is", "set")},
		fields=["name", "title", "clinical", "current_version"],
		order_by="title asc",
	):
		if riga.clinical and not clinico:
			continue
		schema = frappe.db.get_value(modelli.VERSIONE, riga.current_version, "schema")
		motivi = firmabile_da_sola(modelli.carica_schema(schema))
		righe.append(
			{
				"name": riga.name,
				"title": riga.title,
				"clinical": riga.clinical,
				"sign_at_desk": bool(motivi),
				"why": "; ".join(motivi),
			}
		)
	return righe


@frappe.whitelist()
def get_send_options(lead: str) -> dict:
	"""What the operator chooses from: the forms, where a link would go, who may
	hold the tablet."""
	livelli.verifica("moduli.compila")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dove = destinatario(lead)
	if dove.get("email") and not _posta_in_uscita():
		dove = {"reason": _("The centre sends no email yet: set up the outgoing email first")}
	return {
		"templates": _modelli_pubblicati(),
		"link": {
			"to": frappe.db.get_value("CRM Lead", dove["lead"], "lead_name") if dove.get("lead") else None,
			"address": _nascosta(dove["email"]) if dove.get("email") else None,
			"for_them": bool(dove.get("given_by")),
			"reason": dove.get("reason"),
		},
		"representatives": [
			{"name": chi, "label": frappe.db.get_value("CRM Lead", chi, "lead_name") or chi}
			for chi in _rappresentanti(lead)
		],
		"minor": _minorenne(lead),
	}


# ------------------------------------------------------------------ the operator


def _elenco(templates) -> list[str]:
	valori = frappe.parse_json(templates) if isinstance(templates, str) else templates
	if isinstance(valori, str):
		valori = [valori]
	# the same form twice is one form
	return list(dict.fromkeys(t for t in (valori or []) if isinstance(t, str) and t))


def _crea(
	lead: str,
	templates,
	canale: str,
	*,
	scadenza,
	appointment: str | None = None,
	given_by: str | None = None,
	recipient: str | None = None,
	sent_to: str | None = None,
) -> tuple[list, str]:
	"""The requests for these forms, one link for all of them."""
	nomi = _elenco(templates)
	if not nomi:
		frappe.throw(_("Choose at least one form"))
	token = _segreto()
	richieste = []
	for nome in nomi:
		modello = frappe.get_doc(modelli.MODELLO, nome)
		if not modello.enabled or not modello.current_version:
			frappe.throw(_("{0} is not published").format(frappe.bold(modello.title)))
		versione = frappe.get_doc(modelli.VERSIONE, modello.current_version)
		if versione.clinical and not compilazioni.legge_dati_clinici():
			frappe.throw(_("This form records health data: it is for the care team"), frappe.PermissionError)
		richiesta = frappe.get_doc(
			{
				"doctype": RICHIESTA,
				"lead": lead,
				"given_by": given_by,
				"template": modello.name,
				"template_version": versione.name,
				"title": versione.title,
				"clinical": versione.clinical,
				"appointment": appointment,
				"channel": canale,
				"status": "Sent",
				"sign_at_desk": 1 if firmabile_da_sola(modelli.carica_schema(versione.schema)) else 0,
				"expires_on": scadenza,
				# the first holds the link; the others open with it
				"via": richieste[0].name if richieste else None,
				"token_hash": None if richieste else _impronta(token),
				"sent_by": frappe.session.user,
				"sent_on": now_datetime(),
				"recipient": recipient,
				"sent_to": sent_to,
			}
		)
		richiesta.insert(ignore_permissions=True)
		richieste.append(richiesta)
	return richieste, token


def _indirizzo(token: str) -> str:
	return get_url(f"/modulo/{token}")


@frappe.whitelist(methods=["POST"])
def send_form_link(lead: str, templates, appointment: str | None = None) -> dict:
	"""Email a link to fill and sign these forms at home. The message says there
	are forms to fill; which ones, only the person sees, once in with the code."""
	livelli.verifica("moduli.compila")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dove = destinatario(lead)
	if not dove.get("email"):
		frappe.throw(dove.get("reason") or _("There is no email to send the link to"))
	richieste, token = _crea(
		lead,
		templates,
		"Link",
		scadenza=add_to_date(now_datetime(), days=GIORNI_LINK),
		appointment=appointment,
		given_by=dove["given_by"],
		recipient=dove["lead"],
		sent_to=_nascosta(dove["email"]),
	)
	centro = escape_html(nome_del_centro() or _("The centre"))
	if dove["given_by"]:
		persona = escape_html(frappe.db.get_value("CRM Lead", lead, "first_name") or "")
		invito = _("{0} asks you to fill in some forms for {1} before the visit.").format(centro, persona)
	else:
		invito = _("{0} asks you to fill in some forms before your visit.").format(centro)
	avviso = _("To open them you will receive a code at this address. The link is valid for {0} days.")
	frappe.sendmail(
		recipients=[dove["email"]],
		subject=_("Forms to fill before your visit"),
		message="".join(
			[
				f"<p>{_('Hello,')}</p>",
				f"<p>{invito}</p>",
				f'<p><a href="{_indirizzo(token)}">{_("Open the forms")}</a></p>',
				f"<p>{avviso.format(GIORNI_LINK)}</p>",
			]
		),
		reference_doctype=RICHIESTA,
		reference_name=richieste[0].name,
	)
	traccia.traccia(
		RICHIESTA,
		richieste[0].name,
		"sent",
		_nascosta(dove["email"]),
		{"channel": "Link", "forms": [r.name for r in richieste]},
	)
	return {"requests": [_riga(r) for r in richieste]}


@frappe.whitelist(methods=["POST"])
def hand_over_tablet(
	lead: str, templates, given_by: str | None = None, appointment: str | None = None
) -> dict:
	"""The page for this person and these forms, with no code: the operator has
	seen who holds the tablet. The browser logs the operator out and opens it."""
	livelli.verifica("moduli.compila")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if given_by in ("", lead):
		given_by = None
	if given_by and given_by not in _rappresentanti(lead):
		frappe.throw(_("Only a parent or guardian among the related people answers for them"))
	if not given_by and _minorenne(lead):
		frappe.throw(_("A minor's forms are answered by a parent or guardian: say who holds the tablet"))
	richieste, token = _crea(
		lead,
		templates,
		"Tablet",
		scadenza=add_to_date(now_datetime(), minutes=MINUTI_TABLET),
		appointment=appointment,
		given_by=given_by,
	)
	traccia.traccia(
		RICHIESTA,
		richieste[0].name,
		"sent",
		_("Tablet at the desk"),
		{"channel": "Tablet", "forms": [r.name for r in richieste]},
	)
	return {"requests": [_riga(r) for r in richieste], "url": _indirizzo(token)}


def _stato(richiesta) -> str:
	if richiesta.status in APERTE and get_datetime(richiesta.expires_on) < now_datetime():
		return "Expired"
	return richiesta.status


def _riga(richiesta) -> dict:
	return {
		"name": richiesta.name,
		"title": richiesta.title,
		"template": richiesta.template,
		"channel": richiesta.channel,
		"status": _stato(richiesta),
		"sign_at_desk": richiesta.sign_at_desk,
		"sent_on": richiesta.sent_on,
		"sent_by_name": frappe.utils.get_fullname(richiesta.sent_by) if richiesta.sent_by else None,
		"sent_to": richiesta.sent_to,
		"expires_on": richiesta.expires_on,
		"opened_on": richiesta.opened_on,
		"form": richiesta.form,
		"via": richiesta.via,
	}


@frappe.whitelist()
def get_requests(lead: str) -> list[dict]:
	"""The person's requests, newest first: what was sent, and what came back."""
	livelli.verifica_nel_crm("moduli.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	return [
		_riga(frappe.get_doc(RICHIESTA, nome))
		for nome in frappe.get_list(RICHIESTA, filters={"lead": lead}, pluck="name", order_by="creation desc")
	]


@frappe.whitelist(methods=["POST"])
def cancel_request(name: str) -> dict:
	"""Withdraw a request still open: its form no longer opens from the link."""
	livelli.verifica("moduli.compila")
	richiesta = frappe.get_doc(RICHIESTA, name)
	richiesta.check_permission("read")
	if _stato(richiesta) not in APERTE:
		frappe.throw(_("Only a request still open can be withdrawn"))
	richiesta.db_set("status", "Cancelled")
	traccia.traccia(RICHIESTA, richiesta.name, "cancelled")
	return _riga(richiesta)


# ------------------------------------------------------------------ who sees them


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	"""A request follows the person, like the form it asks for."""
	return compilazioni.has_permission(doc, ptype, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	return compilazioni.condizioni_per(RICHIESTA, user)


# ------------------------------------------------------------------ the page


def _gruppo(capo) -> list:
	"""The requests one link opens, in the order they were sent."""
	return [capo] + [
		frappe.get_doc(RICHIESTA, nome)
		for nome in frappe.get_all(
			RICHIESTA, filters={"via": capo.name}, pluck="name", order_by="creation asc"
		)
	]


def _per_token(token: str | None):
	"""The request that holds this link. An unknown link gets the same answer
	whatever is wrong with it, so a guess learns nothing."""
	nome = None
	if isinstance(token, str) and 16 <= len(token) <= 120:
		nome = frappe.db.get_value(
			RICHIESTA, {"token_hash": _impronta(token), "via": ("is", "not set")}, "name"
		)
	if not nome:
		frappe.throw(_("This link is not valid"), frappe.PermissionError)
	capo = frappe.get_doc(RICHIESTA, nome)
	gruppo = _gruppo(capo)
	if get_datetime(capo.expires_on) < now_datetime():
		for richiesta in gruppo:
			if richiesta.status in APERTE:
				richiesta.db_set("status", "Expired")
		frappe.throw(_("This link has expired: ask the centre for a new one"), frappe.PermissionError)
	if all(richiesta.status == "Cancelled" for richiesta in gruppo):
		frappe.throw(_("This link has been withdrawn by the centre"), frappe.PermissionError)
	return capo


def _in_sessione(token: str, sessione: str | None):
	"""The link's request, if the session is the one the code (or the tablet) opened."""
	capo = _per_token(token)
	if (
		not _uguali(_impronta(sessione or ""), capo.session_hash)
		or get_datetime(capo.session_expires_on) < now_datetime()
	):
		frappe.throw(
			_("Open the forms again with a new code")
			if capo.channel == "Link"
			else _("Ask the desk to hand the tablet over again"),
			frappe.PermissionError,
		)
	# the session lasts while it is used
	capo.db_set("session_expires_on", add_to_date(now_datetime(), minutes=MINUTI_SESSIONE))
	return capo


def _della_sessione(token: str, sessione: str | None, request: str | None):
	"""One request of the link: only one the link opens."""
	capo = _in_sessione(token, sessione)
	for richiesta in _gruppo(capo):
		if richiesta.name == request:
			return capo, richiesta
	frappe.throw(_("This form is not among the ones of this link"), frappe.PermissionError)


def _apri_sessione(capo) -> str:
	sessione = _segreto()
	capo.db_set(
		{
			"code_hash": None,
			"session_hash": _impronta(sessione),
			"session_expires_on": add_to_date(now_datetime(), minutes=MINUTI_SESSIONE),
		}
	)
	return sessione


def _vista(capo) -> dict:
	"""What the page may show before the code: nothing about the forms."""
	return {
		"centre": nome_del_centro(),
		"channel": capo.channel,
		"needs_code": capo.channel == "Link",
		"sent_to": capo.sent_to,
		"done": all(_stato(r) not in APERTE for r in _gruppo(capo)),
		"lang": (frappe.local.lang or "it")[:2],
	}


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 300/h an address
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=300, seconds=60 * 60)
def open_request(token: str) -> dict:
	"""The first look at a link: a POST, since it writes (opened, and the tablet's
	session, given here once: opened again, the same address sends to the desk)."""
	capo = _per_token(token)
	vista = _vista(capo)
	if not capo.opened_on:
		adesso = now_datetime()
		for richiesta in _gruppo(capo):
			if richiesta.status == "Sent":
				richiesta.db_set({"status": "Opened", "opened_on": adesso})
		# the link was opened, whatever became of its own form
		if not capo.opened_on:
			capo.db_set("opened_on", adesso)
		traccia.traccia(RICHIESTA, capo.name, "opened")
		if capo.channel == "Tablet":
			vista["session"] = _apri_sessione(capo)
	return vista


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 10/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=10, seconds=60 * 60)
def send_code(token: str) -> dict:
	"""A six-digit code to the address the link went to, good for ten minutes."""
	capo = _per_token(token)
	if capo.channel != "Link":
		frappe.throw(_("This page does not use a code"))
	un_ora_fa = add_to_date(now_datetime(), hours=-1)
	mandati = frappe.db.count(
		traccia.REGISTRO,
		{
			"reference_doctype": RICHIESTA,
			"reference_name": capo.name,
			"event": "code_sent",
			"occurred_on": (">", un_ora_fa),
		},
	)
	if mandati >= CODICI_ALL_ORA:
		frappe.throw(_("Too many codes asked: try again in an hour"))
	email = frappe.db.get_value("CRM Lead", capo.recipient or capo.lead, "email")
	if not email:
		frappe.throw(_("There is no email to send the code to: ask the centre"))
	codice = _codice()
	capo.db_set(
		{
			# the code is tied to the link: the same digits open nothing else
			"code_hash": _impronta(capo.token_hash + codice),
			"code_expires_on": add_to_date(now_datetime(), minutes=MINUTI_CODICE),
			"code_attempts": 0,
		}
	)
	testo = _("Your code to open the forms is <b>{0}</b>. It is valid for {1} minutes.")
	posta = frappe.sendmail(
		recipients=[email],
		subject=_("Your code: {0}").format(codice),
		message=f"<p>{testo.format(codice, MINUTI_CODICE)}</p>",
		reference_doctype=RICHIESTA,
		reference_name=capo.name,
	)
	if posta:
		frappe.db.after_commit.add(lambda: _subito(posta))
	traccia.traccia(RICHIESTA, capo.name, "code_sent", _nascosta(email))
	return {"sent_to": _nascosta(email)}


def _subito(posta) -> None:
	"""A code lasts ten minutes: out now, not at the queue's next turn. If the mail
	server says no, the queue tries again; the page does not fail for it."""
	try:
		posta.send()
	except Exception:
		frappe.log_error(
			title="Form code not sent at once", reference_doctype="Email Queue", reference_name=posta.name
		)


# nosemgrep: guest-whitelisted-method — the link and the code are the credentials, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=20, seconds=60 * 60)
def verify_code(token: str, code: str) -> dict:
	capo = _per_token(token)
	if not capo.code_hash or get_datetime(capo.code_expires_on) < now_datetime():
		frappe.throw(_("The code has expired: ask for a new one"))
	if cint(capo.code_attempts) >= TENTATIVI_CODICE:
		frappe.throw(_("Too many wrong codes: ask for a new one"))
	if not _uguali(_impronta(capo.token_hash + (code or "").strip()), capo.code_hash):
		capo.db_set("code_attempts", cint(capo.code_attempts) + 1)
		traccia.traccia(RICHIESTA, capo.name, "code_wrong")
		frappe.throw(_("The code is not right"))
	sessione = _apri_sessione(capo)
	traccia.traccia(RICHIESTA, capo.name, "code_verified")
	return {"session": sessione}


def _modulo(richiesta):
	"""The form a request fills: started the first time it is opened, on the
	version the request was sent with."""
	if richiesta.form:
		return frappe.get_doc(compilazioni.MODULO, richiesta.form)
	versione = frappe.get_doc(modelli.VERSIONE, richiesta.template_version)
	doc = frappe.get_doc(
		{
			"doctype": compilazioni.MODULO,
			"lead": richiesta.lead,
			"given_by": richiesta.given_by,
			"template": richiesta.template,
			"template_version": versione.name,
			"version": versione.version,
			"title": versione.title,
			"clinical": versione.clinical,
			"channel": richiesta.channel,
			"appointment": richiesta.appointment,
			"request": richiesta.name,
			# filled by the person: nobody from the centre holds the pen
			"filled_by": None,
			"schema_hash": versione.schema_hash,
			"answers": "{}",
		}
	)
	doc.insert(ignore_permissions=True)
	richiesta.db_set("form", doc.name)
	traccia.traccia(
		compilazioni.MODULO,
		doc.name,
		"created",
		_("From a link") if richiesta.channel == "Link" else _("On the tablet at the desk"),
	)
	return doc


def _voce(richiesta) -> dict:
	return {
		"id": richiesta.name,
		"title": richiesta.title,
		"status": _stato(richiesta),
		"sign_at_desk": bool(richiesta.sign_at_desk),
	}


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=120, seconds=60 * 60)
def get_request_forms(token: str, session: str | None = None) -> dict:
	"""The forms of the link, once in: their titles, and where each one is."""
	capo = _in_sessione(token, session)
	return {
		**_vista(capo),
		"person": frappe.db.get_value("CRM Lead", capo.given_by or capo.lead, "first_name"),
		"for_whom": frappe.db.get_value("CRM Lead", capo.lead, "first_name") if capo.given_by else None,
		"forms": [_voce(r) for r in _gruppo(capo) if r.status != "Cancelled"],
	}


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=240, seconds=60 * 60)
def get_request_form(token: str, request: str, session: str | None = None) -> dict:
	_capo, richiesta = _della_sessione(token, session, request)
	stato = _stato(richiesta)
	if stato in ("Cancelled", "Expired"):
		frappe.throw(_("This form is no longer asked"), frappe.PermissionError)
	doc = _modulo(richiesta)
	versione = frappe.get_cached_doc(modelli.VERSIONE, richiesta.template_version)
	return {
		**_voce(richiesta),
		"schema": modelli.carica_schema(versione.schema),
		"answers": compilazioni._risposte(doc),
		"signed": doc.docstatus == 1,
		"pdf": bool(doc.docstatus == 1 and doc.pdf_file),
	}


def _da_compilare(token: str, session: str | None, request: str):
	capo, richiesta = _della_sessione(token, session, request)
	if _stato(richiesta) not in APERTE:
		frappe.throw(_("This form is no longer open here"))
	doc = _modulo(richiesta)
	if doc.docstatus != 0:
		frappe.throw(_("This form is signed"))
	return capo, richiesta, doc


def _dizionario(valore) -> dict:
	valori = json.loads(valore or "{}") if isinstance(valore, str) else (valore or {})
	return valori if isinstance(valori, dict) else {}


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=240, seconds=60 * 60)
def save_request_answers(token: str, request: str, answers: str, session: str | None = None) -> dict:
	"""Keep the answers so far: the link opens them again, until it expires."""
	_capo, _richiesta, doc = _da_compilare(token, session, request)
	schema = modelli.carica_schema(frappe.get_cached_doc(modelli.VERSIONE, doc.template_version).schema)
	puliti, errori, _stato_modulo = S.pulisci(schema, compilazioni._senza_firme(schema, _dizionario(answers)))
	doc.answers = json.dumps(puliti, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	traccia.traccia(compilazioni.MODULO, doc.name, "answers_saved")
	return {"answers": puliti, "problems": [e.come_dict(_) for e in errori]}


def _chiudi_se_finito(capo) -> bool:
	"""The tablet's session ends with its last form: nothing is left to see on it."""
	capo.reload()
	finito = all(_stato(r) not in APERTE for r in _gruppo(capo))
	if finito and capo.channel == "Tablet":
		capo.db_set({"session_hash": None, "session_expires_on": None})
	return finito


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=60, seconds=60 * 60)
def sign_request(token: str, request: str, answers: str, signatures: str, session: str | None = None) -> dict:
	"""Sign one form of the link: the same checks and the same evidence as at the desk."""
	capo, richiesta, doc = _da_compilare(token, session, request)
	if richiesta.sign_at_desk:
		frappe.throw(_("This form is signed at the desk: finish it here, and sign it there"))
	compilazioni.firma(doc, _dizionario(answers), _dizionario(signatures), da_solo=True)
	traccia.traccia(RICHIESTA, richiesta.name, "signed", doc.name)
	return {"signed": True, "pdf": bool(doc.pdf_file), "done": _chiudi_se_finito(capo)}


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=60, seconds=60 * 60)
def finish_request(token: str, request: str, answers: str, session: str | None = None) -> dict:
	"""A form signed at the desk: every answer given and checked now; it waits
	there, in the person's forms, for its signatures."""
	capo, richiesta, doc = _da_compilare(token, session, request)
	if not richiesta.sign_at_desk:
		frappe.throw(_("This form is signed here"))
	compilazioni.completa(doc, _dizionario(answers))
	richiesta.db_set({"status": "Filled", "filled_on": now_datetime()})
	traccia.traccia(RICHIESTA, richiesta.name, "filled", doc.name)
	return {"filled": True, "done": _chiudi_se_finito(capo)}


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(key="token", limit=30, seconds=60 * 60)
def signed_copy(token: str, request: str, session: str | None = None) -> None:
	"""The signed PDF, for the person to keep, while their session lasts."""
	capo, richiesta = _della_sessione(token, session, request)
	doc = frappe.get_doc(compilazioni.MODULO, richiesta.form) if richiesta.form else None
	if capo.channel != "Link" or not doc or doc.docstatus != 1 or not doc.pdf_file:
		frappe.throw(_("There is no copy to download here"), frappe.PermissionError)
	contenuto = frappe.get_doc("File", {"file_url": doc.pdf_file}).get_content(encodings=[])
	# a GET is not committed unless asked: the download is part of the register
	frappe.local.flags.commit = True
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"
	traccia.traccia(compilazioni.MODULO, doc.name, "copy_downloaded")
