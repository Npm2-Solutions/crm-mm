# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Giving a document to the person: by hand, or online for the days chosen.

- **By hand** is always possible: the delivery says to whom (the person, or
  somebody on their behalf), who gave it and when.
- **Online** with a link and a code: the message carries no content - an email
  says a document is ready, with a link - and the link opens only with a code the
  person got **another way** (given at the centre, printed or read out), so a
  wrong address alone opens nothing. It stays online the days chosen
  (`regole.giorni_online`), every opening and download is in the audit log, a
  delivery can be withdrawn at once, and five wrong codes lock it.
- **What a module adds** (`registra_regola`): when one of its documents may not go
  online, and for how long at most. The clinic's reports: only with the patient's
  consent to online reports, never a document marked "never online", 45 days at
  most (the Garante's guidelines, 19/11/2009).

The person reads the same deliveries in their area (`crm.documenti.area`); the
page `/documento/<link>` is the way in for whoever has no area.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, cint, get_datetime, get_fullname, get_url, now_datetime

from crm.documenti import regole as R
from crm.moduli import traccia
from crm.permissions import livelli

CONSEGNA = "CRM Document Delivery"
DOCUMENTO = "CRM Document"
A_MANO, ONLINE = "By hand", "Online"
CONSEGNATO, DISPONIBILE, SCARICATO, RITIRATO = "Delivered", "Available", "Downloaded", "Withdrawn"
SCADUTO = "Expired"
TENTATIVI = 5
MINUTI_SESSIONE = 10


# ------------------------------------------------------------------ what a module adds


@dataclass(frozen=True)
class Regola:
	"""What a module says of its documents going online."""

	#: Why this document may not go online now; None: as far as the module is
	#: concerned, it may.
	ferma: Callable[[object], str | None]
	#: The days it stays online, unless fewer are chosen; None: the CRM's.
	giorni: Callable[[object], int | None] | None = None


_regole: list[Regola] = []


def registra_regola(regola: Regola) -> None:
	if regola not in _regole:
		_regole.append(regola)


def perche_non_online(documento) -> str | None:
	"""Why a document may not go online now, or None."""
	for regola in _regole:
		if motivo := regola.ferma(documento):
			return motivo
	return None


def giorni_del_modulo(documento) -> int | None:
	"""The days a module keeps its document online, unless fewer are chosen: the
	fewest any says; None when none says."""
	tetti = [g for regola in _regole if regola.giorni and (g := regola.giorni(documento))]
	return min(tetti) if tetti else None


# ------------------------------------------------------------------ the codes


def _segreto() -> str:
	return secrets.token_urlsafe(24)


def _codice() -> str:
	return f"{secrets.randbelow(10**6):06d}"


def _impronta(segreto: str) -> str:
	return hashlib.sha256(segreto.encode("utf-8")).hexdigest()


def _uguali(a: str | None, b: str | None) -> bool:
	return bool(a) and bool(b) and hmac.compare_digest(a, b)


# ------------------------------------------------------------------ on the person's page


def _documento(nome: str):
	livelli.verifica("documenti.consegna")
	documento = frappe.get_doc(DOCUMENTO, nome)
	documento.check_permission("read")
	if not documento.file:
		frappe.throw(_("This document has no file to give"))
	return documento


def stato(riga) -> str:
	if riga.channel == ONLINE and riga.status in (DISPONIBILE, SCARICATO):
		if get_datetime(riga.expires_on) <= now_datetime():
			return SCADUTO
	return riga.status


def consegne(documento: str) -> list[dict]:
	"""How a document was given: for its row on the person's page."""
	return [
		{
			"name": riga.name,
			"channel": riga.channel,
			"status": stato(riga),
			"delivered_to": riga.delivered_to,
			"given_by_name": get_fullname(riga.given_by) if riga.given_by else None,
			"given_on": riga.given_on,
			"expires_on": riga.expires_on,
			"downloads": cint(riga.downloads),
			"email": riga.email,
		}
		for riga in frappe.get_all(
			CONSEGNA,
			filters={"document": documento},
			fields=[
				"name",
				"channel",
				"status",
				"delivered_to",
				"given_by",
				"given_on",
				"expires_on",
				"downloads",
				"email",
			],
			order_by="given_on desc",
		)
	]


def _indirizzo(lead: str) -> str | None:
	"""Where the link goes: whoever signs for the person (a parent), or the person."""
	from crm.moduli import richieste

	return richieste.destinatario(lead).get("email")


@frappe.whitelist()
def get_deliveries(document: str) -> dict:
	"""How a document was given, and how it can be given now."""
	documento = _documento(document)
	del_modulo = giorni_del_modulo(documento)
	return {
		"deliveries": consegne(documento.name),
		"online": {
			# why not, when it may not: the module's words
			"reason": perche_non_online(documento),
			"days": R.giorni_online(None, del_modulo),
			"max_days": R.giorni_massimi(del_modulo),
		},
		"email": _indirizzo(documento.lead),
	}


@frappe.whitelist(methods=["POST"])
def deliver_by_hand(document: str, delivered_to: str | None = None) -> dict:
	"""Printed and handed over: to the person, or to whoever took it for them."""
	documento = _documento(document)
	chi = (delivered_to or "").strip() or frappe.db.get_value("CRM Lead", documento.lead, "lead_name")
	riga = frappe.get_doc(
		{
			"doctype": CONSEGNA,
			"document": documento.name,
			"lead": documento.lead,
			"channel": A_MANO,
			"status": CONSEGNATO,
			"delivered_to": chi,
			"given_by": frappe.session.user,
			"given_on": now_datetime(),
		}
	).insert(ignore_permissions=True)
	traccia.traccia(CONSEGNA, riga.name, "delivered", chi)
	return {"deliveries": consegne(documento.name)}


@frappe.whitelist(methods=["POST"])
def deliver_online(document: str, send_email: int = 1, days: int | None = None) -> dict:
	"""Online for the days chosen. Returns the link and the code, shown once: the
	code is given to the person here, and never travels with the link."""
	documento = _documento(document)
	if motivo := perche_non_online(documento):
		frappe.throw(motivo)
	giorni = R.giorni_online(days, giorni_del_modulo(documento))
	# a new delivery takes the place of one still open
	for aperta in frappe.get_all(
		CONSEGNA,
		filters={"document": documento.name, "channel": ONLINE, "status": ("in", (DISPONIBILE, SCARICATO))},
		pluck="name",
	):
		_ritira(aperta, _("Replaced by a new code"))
	token, codice = _segreto(), _codice()
	email = _indirizzo(documento.lead) if cint(send_email) else None
	adesso = now_datetime()
	riga = frappe.get_doc(
		{
			"doctype": CONSEGNA,
			"document": documento.name,
			"lead": documento.lead,
			"channel": ONLINE,
			"status": DISPONIBILE,
			"given_by": frappe.session.user,
			"given_on": adesso,
			"expires_on": add_to_date(adesso, days=giorni),
			"email": email,
			"token_hash": _impronta(token),
			"code_hash": _impronta(token + codice),
		}
	).insert(ignore_permissions=True)
	link = get_url(f"/documento/{token}")
	traccia.traccia(CONSEGNA, riga.name, "online", email)
	if email:
		try:
			_manda_il_link(email, link, riga.expires_on)
		except frappe.OutgoingEmailError:
			# no mail from this site: the link goes with the code, by hand
			frappe.clear_last_message()
			email = None
			riga.db_set("email", None)
	return {"link": link, "code": codice, "expires_on": riga.expires_on, "email": email}


def _manda_il_link(email: str, link: str, scadenza) -> None:
	from crm.moduli.richieste import nome_del_centro
	from crm.posta.aspetto import pulsante

	centro = nome_del_centro() or _("your centre")
	esc = frappe.utils.escape_html
	frappe.sendmail(
		recipients=[email],
		subject=_("A document from {0} is ready").format(centro),
		header=_("A document is ready for you"),
		with_container=True,
		message="".join(
			[
				"<p>{}</p>".format(
					esc(
						_("{0} has a document ready for you: you can open it until {1}.").format(
							centro, frappe.utils.format_date(scadenza)
						)
					)
				),
				pulsante(link, _("Open the document")),
				'<p class="text-muted text-small">{}</p>'.format(
					esc(_("You will need the code the centre gave you: it is not in this email."))
				),
			]
		),
		now=False,
	)


def _ritira(nome: str, motivo: str | None = None) -> None:
	frappe.db.set_value(
		CONSEGNA,
		nome,
		{"status": RITIRATO, "withdrawn_by": frappe.session.user, "withdrawn_on": now_datetime()},
	)
	traccia.traccia(CONSEGNA, nome, "withdrawn", motivo)


@frappe.whitelist(methods=["POST"])
def withdraw(delivery: str) -> dict:
	"""Online no more, at once: a lost code, a wrong address, a change of mind."""
	riga = frappe.get_doc(CONSEGNA, delivery)
	_documento(riga.document)
	if riga.channel != ONLINE or riga.status not in (DISPONIBILE, SCARICATO):
		frappe.throw(_("There is nothing online to withdraw"))
	_ritira(riga.name)
	return {"deliveries": consegne(riga.document)}


# ------------------------------------------------------------------ the person's page, /documento


def _per_token(token: str):
	nome = frappe.db.get_value(CONSEGNA, {"token_hash": _impronta(token or "")}, "name")
	if not nome:
		frappe.throw(_("This link is not valid"), frappe.PermissionError)
	riga = frappe.get_doc(CONSEGNA, nome)
	if riga.channel != ONLINE or stato(riga) not in (DISPONIBILE, SCARICATO):
		frappe.throw(_("This document is no longer online: ask the centre"), frappe.PermissionError)
	return riga


# nosemgrep: guest-whitelisted-method — the link and the code are the credentials, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=20, seconds=60 * 60)
def open_document(token: str, code: str) -> dict:
	"""The code the centre gave: right, it opens a session of ten minutes."""
	riga = _per_token(token)
	if cint(riga.attempts) >= TENTATIVI:
		frappe.throw(_("Too many wrong codes: ask the centre for a new one"), frappe.PermissionError)
	if not _uguali(_impronta(token + (code or "").strip()), riga.code_hash):
		riga.db_set("attempts", cint(riga.attempts) + 1)
		traccia.traccia(CONSEGNA, riga.name, "code_wrong")
		frappe.throw(_("The code is not right"))
	sessione = _segreto()
	riga.db_set(
		{
			"session_hash": _impronta(sessione),
			"session_expires_on": add_to_date(now_datetime(), minutes=MINUTI_SESSIONE),
		}
	)
	traccia.traccia(CONSEGNA, riga.name, "opened")
	documento = frappe.get_doc(DOCUMENTO, riga.document)
	return {"session": sessione, "title": documento.title, "expires_on": riga.expires_on}


def scarica(riga, documento, nota: str | None = None) -> None:
	"""The document's file as the response, the download counted and logged."""
	contenuto = frappe.get_doc("File", {"file_url": documento.file}).get_content(encodings=[])
	# a GET is not committed unless asked: the download is part of the register
	frappe.local.flags.commit = True
	frappe.db.set_value(
		CONSEGNA,
		riga.name,
		{
			"status": SCARICATO,
			"downloads": cint(riga.downloads) + 1,
			"last_download_on": now_datetime(),
		},
	)
	traccia.traccia(CONSEGNA, riga.name, "downloaded", nota)
	frappe.local.response.filename = documento.file.rsplit("/", 1)[-1]
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(key="token", limit=30, seconds=60 * 60)
def download_document(token: str, session: str) -> None:
	"""The document, while the session lasts; every download is in the audit log."""
	riga = _per_token(token)
	if not (
		_uguali(_impronta(session or ""), riga.session_hash)
		and get_datetime(riga.session_expires_on) > now_datetime()
	):
		frappe.throw(_("Enter the code again"), frappe.PermissionError)
	scarica(riga, frappe.get_doc(DOCUMENTO, riga.document))
