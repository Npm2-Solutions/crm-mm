# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's invoicing (Invoices, a person's invoices, the dashboards), through
invoicing's own code.

Made only where the centre has no issuing company yet: then the demo's is the only
one, in test. Its invoices are test invoices on their own series, with the band on
the PDF, the Sistema TS report checked and never sent, nothing to the SdI, nobody a
client because of them. Its name says it is the demo's, so the centre's own, when it
comes, never meets it; a centre that invoices already gets no invoice from the demo,
never a number of its series.

The accountant's work, done as a centre does it: the manager sets the company up
with what the modules add to it - the Sistema TS registers the healthcare setup's
three questions (`registra_preparazione`), as it registers everything else into
invoicing - and a card is made for each of the demo's services as the services page
makes one; a service somebody performs who is not exempt - the osteopath, the
classes' kinesiologist - is taxed, through the SdI, as their qualification says (the
team are providers already, with their qualifications). Then the desk invoices, day by day, the visits as they were paid -
by card mostly, some in cash or by transfer, a few people opposed to the Sistema TS -
and the cycles paid as a whole on the day they were sold, leaving the last days still
to invoice; and one invoice is corrected by a credit note.

An invoice is dated on its visit's day, the oldest first, as the desk would have
issued it; its register (`CRM Invoice Log`) says when the demo issued it.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

import frappe
from frappe import _
from frappe.utils import flt, getdate

from crm.demo import dati
from crm.demo.contesto import Contesto, nome_libero
from crm.demo.simulazione import persone_della_demo

AZIENDA = "CRM Invoicing Company"
EROGATORE = "CRM Service Provider"
SCHEDA = "CRM Billable Service"
QUALIFICA = "CRM Professional Qualification"
FATTURA = "CRM Invoice"

#: Eleven digits with their check digit, from an office (890) that gives none: no
#: taxpayer has it.
PARTITA_IVA = "12345678903"

#: How people paid, and how often: by card, in cash, by bank transfer.
PAGAMENTI = (("MP08", 70), ("MP01", 18), ("MP05", 12))
#: How far back the visits are invoiced (the whole demo), and the last days left to
#: invoice.
GIORNI = 120
DA_FARE = 3
VIE = (
	"Via Garibaldi",
	"Corso Italia",
	"Via Mazzini",
	"Via Giuseppe Verdi",
	"Viale Monza",
	"Via Dante",
	"Via Alessandro Manzoni",
	"Via Cavour",
)
#: The month letters of a codice fiscale.
MESI = "ABCDEHLMPRST"

#: What other modules set up on the demo's company before its cards are made: each
#: ``prepara(azienda)`` returns what a new card of the company starts from.
_preparazioni: list[Callable[[str], dict]] = []


def registra_preparazione(prepara: Callable[[str], dict]) -> None:
	"""A module's share of the demo company's setup (the Sistema TS: the healthcare
	setup's three questions), made in the order registered."""
	if prepara not in _preparazioni:
		_preparazioni.append(prepara)


def crea(ctx: Contesto) -> None:
	from crm.demo import registro

	della_demo = sorted(registro.nomi_di_prova(AZIENDA))
	if set(frappe.get_all(AZIENDA, filters={"enabled": 1}, pluck="name")) - set(della_demo):
		# a centre that invoices already: never a number of its series
		return
	ctx.avanza(_("Invoicing"))
	manager = ctx.squadra("manager") or ctx.utente
	desk = ctx.squadra("desk") or ctx.utente
	with ctx.come(manager):
		# made again after a try that stopped half-way: the same company goes on
		azienda = della_demo[0] if della_demo else _azienda()
		_schede(ctx, _prepara(azienda))
	ctx.salva()
	fatture = []
	# one series, its numbers in the order of the days: visits and cycles together
	for giorno, fai in sorted(_visite(ctx, desk) + _cicli(ctx), key=lambda voce: voce[0]):
		with ctx.come(desk):
			fatta = fai(giorno)
		if fatta:
			fatture.append(fatta)
			if len(fatture) % 50 == 0:
				ctx.salva()
	_nota_di_credito(ctx, desk, fatture)


# -- who issues ------------------------------------------------------------------------------------


def _azienda() -> str:
	from crm.moduli.richieste import nome_del_centro

	doc = frappe.get_doc(
		{
			"doctype": AZIENDA,
			"company_name": nome_libero(AZIENDA, f"{nome_del_centro() or 'Centro'} (dati di prova)"),
			"tax_id": PARTITA_IVA,
			"fiscal_code": PARTITA_IVA,
			"tax_regime": "RF01",
			"address_line": "Via Garibaldi",
			"civic_number": "12",
			"postal_code": "20121",
			"city": "Milano",
			"province": "MI",
			"email": f"amministrazione@{dati.DOMINIO}",
		}
	).insert()
	return doc.name


def _prepara(azienda: str) -> dict:
	"""The company set up as the modules set it up, then made the one that issues.
	Returns what a new card of it starts from."""
	# the default by hand, once its controller has saved it: the controller would
	# take the flag from the centre's switched-off companies, which must find it as
	# they left it when the demo goes
	_predefinita(azienda, 0)
	scheda: dict = {}
	for prepara in _preparazioni:
		scheda.update(prepara(azienda) or {})
	_predefinita(azienda, 1)
	return scheda


def _predefinita(azienda: str, valore: int) -> None:
	frappe.db.set_value(AZIENDA, azienda, "is_default", valore, update_modified=False)
	frappe.clear_document_cache(AZIENDA, azienda)


def _schede(ctx: Contesto, predefinita: dict) -> None:
	"""A card for each of the demo's services, as the services page makes a new one
	(``predefinita``: what the company's setup gives a new card): never a card of the
	centre's tied to them. A service somebody performs who is not exempt - the
	osteopath, the classes' kinesiologist - is taxed at their rate: the engine refuses
	an exemption to who is not a health profession, never a tax."""
	from crm.invoicing import registro as qualifiche

	for servizio in sorted(ctx.con_chiave("service.").values()):
		if frappe.db.exists(SCHEDA, {"crm_service": servizio}):
			continue
		nome, prezzo = frappe.db.get_value("CRM Service", servizio, ["service_name", "default_price"])
		erogatori = qualifiche.erogatori_del_servizio(servizio)
		frappe.get_doc(
			{
				**predefinita,
				"doctype": SCHEDA,
				"service_name": nome_libero(SCHEDA, nome),
				"fiscal_description": nome,
				"crm_service": servizio,
				"default_rate": flt(prezzo),
				"default_provider": erogatori[0].name if len(erogatori) == 1 else None,
				# the osteopath's, the classes' kinesiologist's: taxed at their rate
				**(qualifiche.scheda_tassata(erogatori) or {}),
			}
		).insert()


# -- who pays ---------------------------------------------------------------------------------------


def _profilo(ctx: Contesto, persona: str) -> None:
	"""The person's billing details, as the desk asks them the first time: the codice
	fiscale and the address. The codice is coherent with their name, but born in a
	place no code is given to (a «Y»): it can be nobody's."""
	from crm.invoicing import anagrafica

	if anagrafica.nome_del_profilo("CRM Lead", persona):
		return
	nome, cognome, genere = frappe.db.get_value("CRM Lead", persona, ["first_name", "last_name", "gender"])
	sesso = "F" if (genere or "").lower().startswith("f") else "M"
	nascita = ctx.oggi.replace(year=ctx.oggi.year - ctx.rng.randint(22, 74)) - datetime.timedelta(
		days=ctx.rng.randint(0, 364)
	)
	anagrafica.save_billing_profile(
		"CRM Lead",
		persona,
		{
			"fiscal_code": codice_fiscale(nome, cognome, nascita, sesso, ctx.rng.randint(100, 999)),
			"birth_date": str(nascita),
			"sex": sesso,
			"address_line": ctx.rng.choice(VIE),
			"civic_number": str(ctx.rng.randint(1, 140)),
			"postal_code": "20121",
			"city": "Milano",
			"province": "MI",
			"country": "IT",
		},
	)


def codice_fiscale(nome: str, cognome: str, nascita: datetime.date, sesso: str, luogo: int) -> str:
	"""A codice fiscale coherent with a name, a birth date and a sex, born at «Y» and
	``luogo``: a place letter no town nor country has. Pure."""
	from crm.invoicing.engine import codice_fiscale as cf

	giorno = nascita.day + (40 if sesso == "F" else 0)
	primi = (
		f"{cf._tripletta_cognome(cognome)}{cf._tripletta_nome(nome)}"
		f"{nascita.year % 100:02d}{MESI[nascita.month - 1]}{giorno:02d}Y{luogo:03d}"
	)
	return primi + cf.carattere_controllo(primi)


# -- the invoices -------------------------------------------------------------------------------------


def _visite(ctx: Contesto, desk: str) -> list[tuple]:
	"""The visits people came to, each to be invoiced on its day as it was paid; the
	last days are still to invoice."""
	from crm.invoicing import api

	persone = set(persone_della_demo(ctx))
	ultimo = ctx.giorno(-DA_FARE)
	with ctx.come(desk):
		da_fare = api.appointments_to_invoice(days=GIORNI, limit=100000)
	voci = []
	for riga in da_fare:
		giorno = getdate(riga["starts_on"])
		if riga.get("status") != "Completed" or giorno > ultimo:
			continue
		voci.append(
			(giorno, lambda giorno, appuntamento=riga["name"]: _visita(ctx, appuntamento, persone, giorno))
		)
	return voci


def _visita(ctx: Contesto, appuntamento: str, persone: set, giorno: datetime.date) -> str | None:
	from crm.invoicing import api

	proposta = api.appointment_invoice_proposal(appuntamento)
	if proposta.get("party") not in persone or not all(
		voce["service_provider"] for voce in proposta["items"]
	):
		return None
	_profilo(ctx, proposta["party"])
	return _emetti(ctx, giorno, proposta=proposta)


def _cicli(ctx: Contesto) -> list[tuple]:
	"""The cycles paid as a whole, each to be invoiced on the day it was sold."""
	from crm.invoicing import api

	persone = persone_della_demo(ctx)
	if not persone:
		return []
	cicli = frappe.get_all(
		"CRM Session Cycle",
		filters={"lead": ["in", persone], "billing": api.CICLO_INTERO, "price": [">", 0]},
		fields=["name", "lead", "creation"],
	)
	return [
		(getdate(ciclo.creation), lambda giorno, ciclo=ciclo: _ciclo(ctx, ciclo, giorno)) for ciclo in cicli
	]


def _ciclo(ctx: Contesto, ciclo, giorno: datetime.date) -> str | None:
	from crm.invoicing import api

	_profilo(ctx, ciclo.lead)
	try:
		bozza = api.issue_from_cycle(ciclo.name)
	except frappe.ValidationError:
		frappe.clear_last_message()
		return None
	return _emetti(ctx, giorno, bozza=bozza, pagamento="MP05")


def _emetti(
	ctx: Contesto,
	giorno: datetime.date,
	proposta: dict | None = None,
	bozza: str | None = None,
	pagamento: str | None = None,
) -> str | None:
	"""Issue as the invoice dialog does - the proposal with how it was paid - dated on
	``giorno``. Returns the invoice, or None when the engine said no: then the draft
	goes, as the dialog's «Delete» would."""
	from crm.invoicing import emissione

	dati_pagamento = {
		"payment_method": pagamento or ctx.scegli_pesato(PAGAMENTI),
		"payment_date": str(giorno),
		# a few people do not want their expenses sent to the Sistema TS
		"privacy_opposition": int(ctx.rng.random() < 0.06),
	}
	try:
		if bozza is None:
			bozza = emissione.save({**proposta, **dati_pagamento})["name"]
		else:
			emissione.save(dati_pagamento, invoice=bozza)
		# the day of the visit, as the desk would have issued it then
		doc = frappe.get_doc(FATTURA, bozza)
		doc.posting_date = giorno
		doc.save()
		return emissione.issue({}, invoice=bozza)["name"]
	except frappe.ValidationError:
		frappe.clear_last_message()
		frappe.log_error(title=f"Demo data: invoice not issued ({bozza or proposta.get('appointment')})")
		if bozza and frappe.db.get_value(FATTURA, bozza, "docstatus") == 0:
			# a draft is deleted by the manager
			with ctx.come(ctx.squadra("manager") or ctx.utente):
				emissione.delete_draft(bozza)
		return None


def _nota_di_credito(ctx: Contesto, desk: str, fatture: list[str]) -> None:
	"""One invoice corrected: the visit was paid twice, the money given back."""
	from crm.invoicing import emissione

	if not fatture:
		return
	with ctx.come(desk):
		nota = emissione.credit_note(fatture[len(fatture) // 2])
		try:
			emissione.issue({}, invoice=nota["name"])
		except frappe.ValidationError:
			frappe.clear_last_message()
			frappe.log_error(title="Demo data: credit note not issued")
