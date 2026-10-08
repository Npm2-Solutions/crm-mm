# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders of what a person still owes (Settings > Invoicing > Payments and
reminders, off to start with).

Every morning an invoice issued to a person and still to collect (`incassi`) that is
due and past the days the centre chose gets a polite reminder: an email in the
system's layout, with a button to their invoices in the area where they have one,
and an SMS too where the centre wants it, from the centre's sender. The rules
without a site are `solleciti_regole`.

- **Never** a credit note, a test invoice, one the SdI sent back, nor the demo's
  (`crm.demo.guardie.mai_fuori`); never an SMS to who wrote STOP.
- **Written before it leaves**, on the invoice's log (`CRM Invoice Log`, event
  ``reminded``): a reminder that broke half-way never leaves twice, and one that
  reached nobody waits for the next turn like any other.
- **Who reads it**: the person, or whoever signs for them (a parent for a minor,
  `richieste.destinatario`), as the forms' links go.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import add_days, cint, escape_html, flt, getdate, now_datetime, nowdate

from crm.invoicing import incassi
from crm.invoicing import solleciti_regole as R

IMPOSTAZIONI = "CRM Payment Reminder Settings"
FATTURA = "CRM Invoice"
LOG = "CRM Invoice Log"
EVENTO = "reminded"


def impostazioni() -> frappe._dict:
	"""The centre's choices, as the rules read them."""
	valori = frappe.db.get_singles_dict(IMPOSTAZIONI)
	primo, ogni, massimo, minimo = R.numeri(
		valori.get("first_after_days"),
		valori.get("every_days"),
		valori.get("max_reminders"),
		valori.get("minimum_amount"),
	)
	return frappe._dict(
		attivi=bool(cint(valori.get("enabled"))),
		email=bool(cint(valori.get("use_email", 1))),
		sms=bool(cint(valori.get("use_sms"))),
		primo=primo,
		ogni=ogni,
		massimo=massimo,
		minimo=minimo,
		come_pagare=(valori.get("how_to_pay") or "").strip(),
	)


def come_pagare() -> str:
	"""What the centre wrote on how to pay (the client area shows it), or ''."""
	return (frappe.db.get_single_value(IMPOSTAZIONI, "how_to_pay") or "").strip()


# ------------------------------------------------------------------ what each invoice had


def di_fatture(nomi: list[str]) -> dict[str, dict]:
	"""For each invoice, how many reminders reached the person and the last day one
	did: ``{"count": 2, "last": "2026-10-08"}``."""
	if not nomi:
		return {}
	righe: dict[str, list] = {}
	for riga in frappe.get_all(
		LOG,
		filters={"invoice": ["in", nomi], "event": EVENTO},
		fields=["invoice", "status", "occurred_on"],
	):
		righe.setdefault(riga.invoice, []).append(riga)
	return {nome: R.quanti(righe.get(nome, [])) for nome in nomi}


# ------------------------------------------------------------------ the round


def dovute(conf=None, oggi=None) -> list[frappe._dict]:
	"""The invoices whose reminder leaves today."""
	from crm.demo import guardie

	conf = conf or impostazioni()
	oggi = getdate(oggi or nowdate())
	righe = frappe.get_all(
		FATTURA,
		filters={
			"party_type": "CRM Lead",
			"party": ["is", "set"],
			"docstatus": 1,
			"collected_on": ["is", "not set"],
			"document_type": ["not in", incassi.NOTE_DI_CREDITO],
			"test_document": 0,
			"sdi_status": ["!=", "scartata"],
			# due at the earliest on its issue: nothing issued since is due yet
			"posting_date": ["<=", add_days(oggi, -conf.primo)],
		},
		fields=[
			"name",
			"company",
			"party",
			"document_number",
			"posting_date",
			"grand_total",
			"net_payable",
		],
		order_by="posting_date asc, creation asc",
		limit_page_length=0,
	)
	if not righe:
		return []
	nomi = [riga.name for riga in righe]
	scadenze: dict[str, list] = {}
	for riga in frappe.get_all(
		"CRM Invoice Payment",
		filters={"parenttype": FATTURA, "parent": ["in", nomi]},
		fields=["parent", "due_date"],
	):
		scadenze.setdefault(riga.parent, []).append(getdate(riga.due_date) if riga.due_date else None)
	# what reached the person counts towards the most; a try that reached nobody
	# only waits its days before the next
	inviati: dict[str, list] = {}
	tentati: dict[str, list] = {}
	for riga in frappe.get_all(
		LOG,
		filters={"invoice": ["in", nomi], "event": EVENTO},
		fields=["invoice", "occurred_on", "status"],
	):
		dove = inviati if riga.status == R.INVIATO else tentati
		dove.setdefault(riga.invoice, []).append(getdate(riga.occurred_on))
	dovute_ = []
	for riga in righe:
		# nothing about the demo leaves (crm/demo/guardie.py)
		if guardie.mai_fuori(FATTURA, riga.name) or guardie.mai_fuori("CRM Lead", riga.party):
			continue
		scade = R.scadenza(getdate(riga.posting_date), scadenze.get(riga.name, []))
		if R.da_sollecitare(
			oggi,
			scade,
			inviati.get(riga.name, []),
			incassi.da_pagare(riga),
			primo=conf.primo,
			ogni=conf.ogni,
			massimo=conf.massimo,
			minimo=conf.minimo,
			tentati=tentati.get(riga.name, []),
		):
			riga.scadenza = scade
			dovute_.append(riga)
	return dovute_


@contextmanager
def _nella_lingua_del_centro():
	"""What the person reads is in the centre's language, whoever's session it is."""
	from crm import lingue

	prima = getattr(frappe.local, "lang", None)
	frappe.local.lang = lingue.del_centro()
	try:
		yield
	finally:
		frappe.local.lang = prima


def _conferma() -> None:
	"""Each reminder on its own: one that fails takes nothing else with it."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — each reminder of the round on its own


def ogni_giorno() -> None:
	"""The daily round: each invoice due gets its reminder."""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	conf = impostazioni()
	if not conf.attivi:
		return
	with _nella_lingua_del_centro():
		for fattura in dovute(conf):
			try:
				manda(fattura, conf)
				_conferma()
			except Exception:
				if not frappe.flags.in_test:
					frappe.db.rollback()
				frappe.log_error(
					title=f"Payment reminder of {fattura.name} not sent",
					reference_doctype=FATTURA,
					reference_name=fattura.name,
				)


# ------------------------------------------------------------------ one reminder


def _dove(lead: str) -> frappe._dict:
	"""Who reads the reminder and where: the person, or whoever signs for them."""
	from crm.moduli import richieste
	from crm.telephony import sms
	from crm.utils import stored_value, to_e164

	dove = richieste.destinatario(lead)
	chi = dove.get("lead") or lead
	email = (dove.get("email") or "").strip() or None
	mobile = stored_value("CRM Lead", chi, "mobile_no")
	return frappe._dict(
		lead=chi,
		email=email,
		numero=to_e164(mobile) if mobile else None,
		nome=(frappe.db.get_value("CRM Lead", chi, "first_name") or "").strip(),
		fermato=sms.ha_fermato("CRM Lead", chi),
	)


def _registra(fattura, stato: str, messaggio: str = "", vie: list | None = None):
	return frappe.get_doc(
		{
			"doctype": LOG,
			"invoice": fattura.name,
			"company": fattura.company,
			"event": EVENTO,
			"status": stato,
			"actor": frappe.session.user,
			"occurred_on": now_datetime(),
			"message": messaggio,
			"payload": frappe.as_json({"channels": vie}) if vie else None,
		}
	).insert(ignore_permissions=True)


def manda(fattura, conf=None) -> str:
	"""The reminder of one invoice, by every way the centre wants that reaches the
	person; written on its log before it leaves. Returns how it went."""
	from crm.telephony import sms

	conf = conf or impostazioni()
	dove = _dove(fattura.party)
	da = sms.mittente() if conf.sms else None
	vie = R.canali(conf.email, bool(da), bool(dove.email), bool(dove.numero), dove.fermato)
	if not vie:
		_registra(fattura, R.NON_INVIATO, _perche_no(dove, conf, da))
		return R.NON_INVIATO
	registro = _registra(fattura, R.INVIATO, vie=vie)
	# written down before it leaves: whatever happens next, it never leaves twice
	_conferma()
	testo = _testo(fattura, dove, conf)
	partite, errori = [], []
	for via in vie:
		try:
			if via == R.EMAIL:
				_per_email(fattura, dove, testo)
			else:
				_per_sms(fattura, dove, testo, da)
			partite.append(via)
		except Exception as errore:
			frappe.clear_last_message()
			frappe.log_error(
				title=f"Payment reminder not sent by {via}",
				reference_doctype=FATTURA,
				reference_name=fattura.name,
			)
			errori.append(f"{via}: {errore}")
	registro.db_set(
		{
			"status": R.INVIATO if partite else R.FALLITO,
			"message": "; ".join(errori)[:500],
			"payload": frappe.as_json({"channels": partite}),
		},
		update_modified=False,
	)
	return R.INVIATO if partite else R.FALLITO


def _perche_no(dove, conf, da) -> str:
	if dove.fermato and dove.numero and not dove.email:
		return _("They wrote STOP to the centre's SMS and have no email on file: call them")
	if not (dove.email or dove.numero):
		return _("No email or mobile on file: call them")
	return _("None of the centre's ways reaches them: call them")


def _testo(fattura, dove, conf) -> dict:
	from crm.invoicing.documento import in_euro
	from crm.lingue import con_l_apostrofo
	from crm.moduli.richieste import nome_del_centro

	numero = fattura.document_number or fattura.name
	giorno = frappe.format(getdate(fattura.posting_date), "Date")
	importo = in_euro(Decimal(str(incassi.da_pagare(fattura))))
	return {
		"nome": dove.nome,
		"centro": nome_del_centro() or _("the centre"),
		"numero": numero,
		"frase": con_l_apostrofo(
			_("Invoice {0} of {1}, for {2}, is still to be paid.").format(numero, giorno, importo)
		),
		"come": conf.come_pagare,
	}


def _bottone(lead: str, email: str) -> str:
	"""Where the reader enters the person's area: the button to their invoices."""
	from crm.area import accesso, collegamento
	from crm.posta.aspetto import pulsante

	utenti = {(riga.user or "").lower() for riga in accesso.accessi_aperti(lead)}
	if email.lower() not in utenti:
		return ""
	indirizzo = collegamento.crea(email.lower(), lead, "payment_reminder", "documents")
	return pulsante(indirizzo, _("See your invoices"))


def _per_email(fattura, dove, testo: dict) -> None:
	esc = escape_html
	righe = [
		f"<p>{esc(_('Hi {0},').format(testo['nome']))}</p>" if testo["nome"] else "",
		f"<p>{esc(_('a kind reminder from {0}.').format(testo['centro']))}</p>",
		f"<p><b>{esc(testo['frase'])}</b></p>",
		# a few lines the centre wrote: an IBAN, «at the desk»
		f"<p>{esc(_('How to pay:'))}<br>{esc(testo['come']).replace(chr(10), '<br>')}</p>"
		if testo["come"]
		else "",
		_bottone(fattura.party, dove.email),
		f'<p class="text-muted text-small">{esc(_("If you have already paid, please ignore this message, and thank you."))}</p>',
	]
	frappe.sendmail(
		recipients=[dove.email],
		subject=_("Payment reminder: invoice {0}").format(testo["numero"]),
		header=_("A payment reminder"),
		with_container=True,
		message="".join(righe),
		reference_doctype=FATTURA,
		reference_name=fattura.name,
	)


def _per_sms(fattura, dove, testo: dict, da: str) -> None:
	from crm.api.sms import create_sms, deliver_via_twilio

	parole = [f"{testo['centro']}: {testo['frase']}"]
	if testo["come"]:
		parole.append(_("How to pay: {0}").format(" ".join(testo["come"].split())))
	parole.append(_("If you have already paid, please ignore this message."))
	doc = create_sms(
		type="Outgoing",
		from_number=da,
		to=dove.numero,
		message=" ".join(parole),
		reference_doctype="CRM Lead",
		reference_name=dove.lead,
	)
	deliver_via_twilio(doc)
	if doc.status == "Failed":
		raise frappe.ValidationError(doc.error_message or _("The SMS did not leave"))
