# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote answered by the person in their client area: accepted and signed, or
declined (docs/verticali/clinica/design.md, "Tre strati": "Il preventivo").

- **Who answers**: the person, or a parent or guardian who enters their area;
  whoever only follows them reads the quote and does not answer it. Never the
  centre's preview: it changes nothing.
- **Accepted and signed**: the quote is read - its rows in the area, its PDF -
  the stroke drawn with the forms' pad, and confirmed. The area must have been
  entered by a code or its link in the last minutes (`accesso.verificato_da_poco`):
  that is how the signer is known. It goes the way the desk's yes goes
  (`api.accetta`): the quotes deal is won, the appointments booked take their
  rows. It keeps the evidence a signed form keeps (`crm.moduli.compilazioni`):
  the stroke, who as what, when by the server's clock, from which address and
  device, the SHA-256 of what was signed - the PDF as proposed - and the signed
  copy with its evidence page, sealed where the centre has a seal
  (`documento.fai_la_copia_firmata`); every step in the quote's register
  (`crm.moduli.traccia`).
- **Declined**, with a reason if the person writes one: the deal is lost, the
  reason in its notes.
- **Who hears of it**: whoever wrote the quote and the desk that handles quotes
  and reads this one (`avvisa`); the sentence names the person, never the quote,
  whose title may say what a care plan is about.
- **The desk sends it to sign** (`send_to_sign`): an email with the area's own
  link (`crm.area.collegamento`), which enters once and lands on the quotes; by
  SMS the same link, or by WhatsApp the area's news, only to the number of the
  person's that wrote to the centre (`crm.area.avvisi`). The words say only that
  there is a quote to read: nothing of what. The area opens for the person, or a
  parent or guardian, if it was not. Never to a person of the demo data.
"""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, escape_html, formatdate, get_fullname, getdate, now_datetime

from crm.area import accesso
from crm.area.api import _mia
from crm.moduli import compilazioni, traccia
from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli
from crm.preventivi import api, documento
from crm.preventivi import regole as R

DOCTYPE = api.DOCTYPE
#: Who answers a quote from the area: the person, or who answers for them.
RISPONDONO = (accesso.SE_STESSO, accesso.TUTORE)
EMAIL, SMS, WHATSAPP = "Email", "SMS", "WhatsApp"
CANALI = (EMAIL, SMS, WHATSAPP)


# ------------------------------------------------------------------ in the area


def _del_mio(person: str, quote: str, rispondere: bool = False):
	"""The area's row of the session for ``person``, and their quote. Never in the
	centre's preview."""
	riga = _mia(person)
	if not quote or frappe.db.get_value(DOCTYPE, quote, "lead") != person:
		frappe.throw(_("This quote is not yours"), frappe.PermissionError)
	if rispondere and riga.relation not in RISPONDONO:
		frappe.throw(_("Only the person, or a parent or guardian, answers a quote"), frappe.PermissionError)
	return riga, frappe.get_doc(DOCTYPE, quote)


def _ancora_da_rispondere(doc) -> None:
	problema = R.da_rispondere(doc.status, getdate(doc.valid_until) if doc.valid_until else None, getdate())
	if problema:
		frappe.throw(_(problema.messaggio).format(*(formatdate(a) for a in problema.argomenti)))


def _chi_firma(riga, doc) -> tuple[str, str]:
	"""Who signs, and as what: the person, or the parent or guardian in the area."""
	if riga.relation == accesso.SE_STESSO:
		return doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name") or doc.lead, "patient"
	utente = frappe.session.user
	nome = frappe.db.get_value("CRM Lead", {"email": utente}, "lead_name")
	return nome or get_fullname(utente) or utente, "guardian"


def impronta_di(doc) -> str:
	"""What the signature is put on: the PDF as it was proposed, or - if it could
	not be made - the quote's services and sums."""
	if doc.quote_pdf:
		nome = frappe.db.get_value("File", {"file_url": doc.quote_pdf}, "name")
		if nome:
			return hashlib.sha256(frappe.get_doc("File", nome).get_content(encodings=[])).hexdigest()
	return R.impronta(
		{
			"name": doc.name,
			"title": doc.title,
			"items": [api.leggi_voce(voce) for voce in doc.items],
			"total_net": doc.total_net,
			"currency": doc.currency,
			"valid_until": doc.valid_until,
			# paid in instalments: the plan is signed with the services
			**(
				{"instalments": [(r.kind, r.number, r.due_on, r.amount) for r in doc.instalments]}
				if doc.instalments
				else {}
			),
		}
	)


def riconoscimento() -> str:
	"""How the signer was known: the area, entered by a code or its link in the
	last minutes, at the address it was opened to."""
	from crm.moduli.richieste import _nascosta

	return _(
		"In the client area, entered as {0}: the address was checked by a code or the area's link in the last {1} minutes"
	).format(_nascosta(frappe.session.user), accesso.MINUTI_VERIFICA)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def accept_in_area(person: str, quote: str, signature: str) -> dict:
	"""Accepted and signed by the person in their area: the stroke, the evidence,
	the signed copy; the deal won as at the desk."""
	riga, doc = _del_mio(person, quote, rispondere=True)
	_ancora_da_rispondere(doc)
	if not accesso.verificato_da_poco():
		frappe.throw(_("Enter your code again to sign it"), frappe.PermissionError)
	tratto = compilazioni._png(signature, _("Your signature"))
	chi, veste = _chi_firma(riga, doc)
	ip, dispositivo = compilazioni._richiesta()
	impronta = impronta_di(doc)
	immagine = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}-signature.png",
			"attached_to_doctype": DOCTYPE,
			"attached_to_name": doc.name,
			"attached_to_field": "signature",
			"is_private": 1,
			"content": tratto,
		}
	).insert(ignore_permissions=True)
	doc.signature = immagine.file_url
	doc.signer_name = chi
	doc.signed_on = now_datetime()
	doc.signer_ip = ip
	doc.signer_device = dispositivo
	doc.signed_hash = impronta
	api.accetta(doc, frappe.session.user, dove=R.NELL_AREA)
	traccia.traccia(
		DOCTYPE, doc.name, "signed", chi, {"sha256": impronta, "signer": veste, "level": "simple"}
	)
	documento.fai_la_copia_firmata(frappe.get_doc(DOCTYPE, doc.name), veste, riconoscimento())
	_avvisa(doc, N.PREVENTIVO_FIRMATO)
	return _nell_area(person)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def decline_in_area(person: str, quote: str, reason: str | None = None) -> dict:
	"""Declined by the person in their area, and maybe why: the deal is lost."""
	riga, doc = _del_mio(person, quote, rispondere=True)
	_ancora_da_rispondere(doc)
	motivo = R.motivo(reason)
	chi, _veste = _chi_firma(riga, doc)
	api.rifiuta(doc, nota=motivo, dove=R.NELL_AREA)
	traccia.traccia(DOCTYPE, doc.name, "declined", chi, {"reason": bool(motivo)})
	_avvisa(doc, N.PREVENTIVO_RIFIUTATO)
	return _nell_area(person)


def _nell_area(person: str) -> dict:
	from crm.preventivi import area

	return area.area_quotes(person)


@frappe.whitelist(methods=["GET"])
def area_quote_pdf(person: str, quote: str) -> None:
	"""The quote's PDF, or its signed copy once signed. One with health data after
	a code verified in the last minutes, as a report."""
	from crm.preventivi import area

	_riga, doc = _del_mio(person, quote)
	if doc.status not in area.NELL_AREA:
		frappe.throw(_("This quote is not yours"), frappe.PermissionError)
	if cint(doc.clinical) and not accesso.verificato_da_poco():
		frappe.throw(_("Enter your code again to download it"), frappe.PermissionError)
	file_url = doc.signed_pdf or doc.quote_pdf
	nome = frappe.db.get_value("File", {"file_url": file_url}, "name") if file_url else None
	if not nome:
		frappe.throw(_("There is no PDF of this quote"), frappe.PermissionError)
	traccia.traccia(DOCTYPE, doc.name, "copy_downloaded", _("From the client area"))
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = frappe.get_doc("File", nome).get_content(encodings=[])
	frappe.local.response.type = "download"


# ------------------------------------------------------------------ who hears of it


def chi_sente(doc) -> list[str]:
	"""Whoever wrote the quote, and the desk that handles quotes and reads this one."""
	chi = [doc.practitioner] if doc.practitioner else []
	for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"):
		if utente in chi or utente in ("Administrator", "Guest"):
			continue
		if (
			livelli.nel_crm(utente)
			and not livelli.e_agenzia(utente)
			and api.gestisce(utente)
			and api.puo_leggere(doc, utente)
		):
			chi.append(utente)
	return chi


def _avvisa(doc, frase: str) -> None:
	nome = doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name") or doc.lead
	for utente in chi_sente(doc):
		avvisa(utente, "Area", frase, [nome], riguarda=("CRM Lead", doc.lead), oggetto=(DOCTYPE, doc.name))


# ------------------------------------------------------------------ the desk sends it


def _della_demo(lead: str) -> bool:
	from crm.area import collegamento

	return collegamento._della_demo(lead)


def _chi_risponde(lead: str) -> list[str]:
	"""The users who answer for this person in the area: the person, a parent or guardian."""
	return sorted({r.user for r in accesso.accessi_aperti(lead) if r.relation in RISPONDONO})


def _numero(lead: str, canale: str) -> tuple[str, str] | None:
	"""The area user and their number a message may go to on this channel: the
	person's own, that wrote to the centre from it."""
	from crm.area import avvisi
	from crm.telephony import sms

	if canale == WHATSAPP and not avvisi._modello_whatsapp():
		return None
	if canale == SMS and not avvisi._numero_sms():
		return None
	for utente in _chi_risponde(lead):
		numero = avvisi.numero_verificato(utente, canale)
		if not numero:
			continue
		if canale == SMS and sms.ha_fermato("CRM Lead", avvisi._persona_di(utente)):
			continue
		return utente, numero
	return None


def _mascherato(numero: str) -> str:
	return "•••• " + numero[-3:]


def _vie(doc) -> list[dict]:
	"""Each way the quote may go to sign, where to, or why not."""
	from crm.moduli import richieste

	vie = []
	dove = richieste.destinatario(doc.lead)
	if dove.get("email") and not richieste._posta_in_uscita():
		dove = {"reason": _("The centre sends no email yet: set up the outgoing email first")}
	vie.append(
		{
			"channel": EMAIL,
			"to": richieste._nascosta(dove["email"]) if dove.get("email") else None,
			"reason": None if dove.get("email") else dove.get("reason"),
		}
	)
	for canale in (SMS, WHATSAPP):
		trovato = _numero(doc.lead, canale)
		vie.append(
			{
				"channel": canale,
				"to": _mascherato(trovato[1]) if trovato else None,
				"reason": None
				if trovato
				else _(
					"Only to the number of the person's that wrote to the centre on {0}, once their area is open"
				).format(canale),
			}
		)
	return vie


@frappe.whitelist()
def sign_options(name: str) -> dict:
	"""Where the desk may send the quote to sign."""
	doc = api._decide(name)
	return {"channels": _vie(doc), "demo": _della_demo(doc.lead)}


def _email(utente: str, doc, centro: str) -> None:
	from crm.area import collegamento
	from crm.posta.aspetto import pulsante

	indirizzo = collegamento.crea(utente, doc.lead, "quote", "plans")
	frappe.sendmail(
		recipients=[utente],
		subject=_("A quote to read in your area at {0}").format(centro),
		header=_("A quote to read"),
		with_container=True,
		message="".join(
			[
				"<p>{}</p>".format(
					escape_html(
						_(
							"{0} sent you a quote. Read it in your area: there you accept and sign it, or say you do not accept it."
						).format(centro)
					)
				),
				pulsante(indirizzo, _("Read the quote")),
				'<p class="text-muted text-small">{}</p>'.format(
					escape_html(
						_(
							"The button enters your area without a code, once, within {0} days. Then you enter with your email, as always."
						).format(collegamento.GIORNI)
					)
				),
			]
		),
		reference_doctype=DOCTYPE,
		reference_name=doc.name,
	)


def _sms(utente: str, numero: str, lead: str, centro: str) -> None:
	from crm.api.sms import create_sms, deliver_via_twilio
	from crm.area import avvisi, collegamento

	indirizzo = collegamento.crea(utente, lead, "quote", "plans")
	doc = create_sms(
		type="Outgoing",
		from_number=avvisi._numero_sms(),
		to=numero,
		message=_("{0} sent you a quote to read in your area: {1}").format(centro, indirizzo),
		reference_doctype="CRM Lead",
		reference_name=avvisi._persona_di(utente) or lead,
	)
	deliver_via_twilio(doc)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def send_to_sign(name: str, channel: str = EMAIL) -> dict:
	"""The quote to the person, to read and sign in their area: the area opened if
	it was not, the link by email or SMS, the area's news by WhatsApp."""
	from crm.area import avvisi, collegamento
	from crm.moduli import richieste
	from crm.moduli.richieste import _nascosta, nome_del_centro

	doc = api._decide(name)
	if channel not in CANALI:
		frappe.throw(_("{0} is not a way to send it").format(channel))
	if _della_demo(doc.lead):
		frappe.throw(_("This is a person of the demo data: nothing is sent to them"))
	_ancora_da_rispondere(doc)
	centro = nome_del_centro() or _("your centre")
	if channel == EMAIL:
		if not richieste._posta_in_uscita():
			frappe.throw(_("The centre sends no email yet: set up the outgoing email first"))
		utenti = [u for u in collegamento.apri_se_serve(doc.lead) if u in _chi_risponde(doc.lead)]
		if not utenti:
			frappe.throw(_("There is no email to send it to: open the person's area first"))
		for utente in utenti:
			_email(utente, doc, centro)
		destinazione = ", ".join(_nascosta(u) for u in utenti)
	else:
		trovato = _numero(doc.lead, channel)
		if not trovato:
			frappe.throw(
				_(
					"Only to the number of the person's that wrote to the centre on {0}, once their area is open"
				).format(channel)
			)
		utente, numero = trovato
		if channel == SMS:
			_sms(utente, numero, doc.lead, centro)
		else:
			avvisi._manda_whatsapp(avvisi._persona_di(utente) or doc.lead, numero, centro)
		destinazione = _mascherato(numero)
	doc.db_set(
		{"sent_to_sign_on": now_datetime(), "sent_to_sign_to": f"{channel} · {destinazione}"},
		update_modified=False,
	)
	traccia.traccia(DOCTYPE, doc.name, "sent", destinazione, {"channel": channel})
	return api._dettaglio(frappe.get_doc(DOCTYPE, doc.name))
