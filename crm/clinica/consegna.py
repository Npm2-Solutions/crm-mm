# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Giving a report to the patient: by hand, or online for 45 days.

The Garante's guidelines on online reports (19/11/2009) and their FAQ, as the
design reads them:

- **By hand** is always possible: the delivery says to whom (the patient, or
  somebody on their behalf), who gave it and when.
- **Online** only with the patient's consent to online reports, and never for a
  document marked "never online" (genetic tests, HIV, or a single test the
  patient left out). The report stays online 45 days at most.
- The message carries no content: an email says a document is ready, with a
  link; the link opens only with a code the patient got **another way** - given
  at the centre, printed or read out - so a wrong address alone opens nothing.
- Every opening and download is in the audit log (who, when, from where); a
  delivery can be withdrawn at once, and five wrong codes lock it.

The patient area of phase 3 will show the same deliveries; the page
`/referto/<link>` is the way in until then.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, cint, get_datetime, get_fullname, get_url, now_datetime

from crm.moduli import traccia
from crm.permissions import livelli

CONSEGNA = "Clinic Report Delivery"
DOCUMENTO = "Clinic Document"
REFERTI_ONLINE = "online_reports"
A_MANO, ONLINE = "By hand", "Online"
CONSEGNATO, DISPONIBILE, SCARICATO, RITIRATO = "Delivered", "Available", "Downloaded", "Withdrawn"
#: The longest a report stays online (Garante, 2009).
GIORNI_ONLINE = 45
TENTATIVI = 5
MINUTI_SESSIONE = 10


def _segreto() -> str:
	return secrets.token_urlsafe(24)


def _codice() -> str:
	return f"{secrets.randbelow(10**6):06d}"


def _impronta(segreto: str) -> str:
	return hashlib.sha256(segreto.encode("utf-8")).hexdigest()


def _uguali(a: str | None, b: str | None) -> bool:
	return bool(a) and bool(b) and hmac.compare_digest(a, b)


def col_consenso(lead: str) -> bool:
	return bool(
		frappe.db.exists("CRM Consent", {"lead": lead, "consent_type": REFERTI_ONLINE, "status": "Given"})
	)


def _file(documento) -> str | None:
	from crm.clinica import archivio

	return archivio._file_di(documento)


def _documento(nome: str):
	livelli.verifica("clinica.consegna")
	documento = frappe.get_doc(DOCUMENTO, nome)
	documento.check_permission("read")
	if not _file(documento):
		frappe.throw(_("This document has no file to give"))
	return documento


def _stato(riga) -> str:
	if riga.channel == ONLINE and riga.status in (DISPONIBILE, SCARICATO):
		if get_datetime(riga.expires_on) <= now_datetime():
			return "Expired"
	return riga.status


def consegne(documento: str) -> list[dict]:
	"""How a document was given: for its row in the archive."""
	return [
		{
			"name": riga.name,
			"channel": riga.channel,
			"status": _stato(riga),
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


@frappe.whitelist()
def get_deliveries(document: str) -> dict:
	"""How a document was given, and how it can be given now."""
	documento = _documento(document)
	return {
		"deliveries": consegne(documento.name),
		"online_consent": col_consenso(documento.lead),
		"never_online": cint(documento.not_online),
		"email": _indirizzo(documento.lead),
	}


@frappe.whitelist(methods=["POST"])
def deliver_by_hand(document: str, delivered_to: str | None = None) -> dict:
	"""Printed and handed over: to the patient, or to whoever took it for them."""
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


def _indirizzo(lead: str) -> str | None:
	"""Where the link goes: whoever signs for the person (a parent), or the person."""
	from crm.moduli import richieste

	return richieste.destinatario(lead).get("email")


@frappe.whitelist(methods=["POST"])
def deliver_online(document: str, send_email: int = 1) -> dict:
	"""Online for 45 days. Returns the link and the code, shown once: the code is
	given to the patient here, and never travels with the link."""
	documento = _documento(document)
	if not col_consenso(documento.lead):
		frappe.throw(_("The patient has not asked for their reports online: give it by hand"))
	if cint(documento.not_online):
		frappe.throw(_("This document never goes online: give it by hand"))
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
			"expires_on": add_to_date(adesso, days=GIORNI_ONLINE),
			"email": email,
			"token_hash": _impronta(token),
			"code_hash": _impronta(token + codice),
		}
	).insert(ignore_permissions=True)
	link = get_url(f"/referto/{token}")
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

	centro = nome_del_centro() or _("your centre")
	frappe.sendmail(
		recipients=[email],
		subject=_("A document from {0} is ready").format(centro),
		message=_(
			"<p>A document from {0} is ready for you.</p>"
			'<p><a href="{1}">Open it here</a>, until {2}.</p>'
			"<p>You will need the code the centre gave you: it is not in this email.</p>"
		).format(frappe.utils.escape_html(centro), link, frappe.utils.format_date(scadenza)),
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


# ------------------------------------------------------------------ the patient's page


def _per_token(token: str):
	nome = frappe.db.get_value(CONSEGNA, {"token_hash": _impronta(token or "")}, "name")
	if not nome:
		frappe.throw(_("This link is not valid"), frappe.PermissionError)
	riga = frappe.get_doc(CONSEGNA, nome)
	if riga.channel != ONLINE or _stato(riga) not in (DISPONIBILE, SCARICATO):
		frappe.throw(_("This document is no longer online: ask the centre"), frappe.PermissionError)
	return riga


# nosemgrep: guest-whitelisted-method — the link and the code are the credentials, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="token", limit=20, seconds=60 * 60)
def open_report(token: str, code: str) -> dict:
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


# nosemgrep: guest-whitelisted-method — the link and its session are the credentials
@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(key="token", limit=30, seconds=60 * 60)
def download_report(token: str, session: str) -> None:
	"""The report, while the session lasts; every download is in the audit log."""
	riga = _per_token(token)
	if not (
		_uguali(_impronta(session or ""), riga.session_hash)
		and get_datetime(riga.session_expires_on) > now_datetime()
	):
		frappe.throw(_("Enter the code again"), frappe.PermissionError)
	documento = frappe.get_doc(DOCUMENTO, riga.document)
	file_url = _file(documento)
	contenuto = frappe.get_doc("File", {"file_url": file_url}).get_content(encodings=[])
	# a GET is not committed unless asked: the download is part of the register
	frappe.local.flags.commit = True
	riga.db_set(
		{
			"status": SCARICATO,
			"downloads": cint(riga.downloads) + 1,
			"last_download_on": now_datetime(),
		}
	)
	traccia.traccia(CONSEGNA, riga.name, "downloaded")
	frappe.local.response.filename = file_url.rsplit("/", 1)[-1]
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"
