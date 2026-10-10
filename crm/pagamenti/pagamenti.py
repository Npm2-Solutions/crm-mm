# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Payments asked online through the centre's own Stripe account (doc 60).

Two things are paid online:

- **an invoice** to a person still to collect: a Stripe Checkout link made on
  demand - from the client area's «Pay online», or the desk's «Payment link» to
  copy and send - and kept until it expires (a day). Paid, the invoice is
  collected through the same door the desk uses (`incassi.segna`), its log says
  by card on Stripe with the payment intent, whoever manages invoicing is told.
- **a deposit** at online booking, for a service that asks one: the place is held
  as an online request waiting for the payment (half an hour, Stripe's least),
  the booking confirmed when Stripe says paid, the place freed when the link
  expires. A cancellation in time gives the deposit back where the centre wants it.

Every payment is a `CRM Online Payment` of the person's, written before anything
leaves for Stripe; what Stripe says comes back through `webhook`, which applies
each event once. A refund made on Stripe is recorded and said, and never takes a
collection back by itself: whoever manages invoicing decides.

Never for a test invoice, a credit note, the demo's records, nor the area's preview.
"""

from __future__ import annotations

import time
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime, get_url, getdate, now_datetime

from crm.notifiche import regole as NR
from crm.pagamenti import cliente, collegamento, fatture
from crm.pagamenti import regole as R

PAGAMENTO = "CRM Online Payment"
FATTURA = "CRM Invoice"
APPUNTAMENTO = "CRM Appointment"

ATTESA, PAGATO, SCADUTO, NON_RIUSCITO = "Waiting", "Paid", "Expired", "Failed"
RIMBORSATO, RIMBORSATO_IN_PARTE, ANNULLATO = "Refunded", "Partly refunded", "Cancelled"
PER_FATTURA, PER_ACCONTO = "Invoice", "Deposit"
#: a subscription bought from the area, an instalment of one (`addebiti`)
PER_ABBONAMENTO, PER_RATA = "Subscription", "Instalment"


def _soldi(importo, valuta: str | None = None) -> str:
	return frappe.utils.fmt_money(flt(importo), currency=(valuta or "EUR").upper())


def _centro() -> str:
	from crm import marchio

	return frappe.db.get_single_value("FCRM Settings", "brand_name") or marchio.nome()


def _demo(*riferimenti: tuple[str, str | None]) -> bool:
	from crm.demo import guardie

	return guardie.mai_a_stripe(*riferimenti)


# ------------------------------------------------------------------ a Checkout session


def _sessione(
	pagamento, descrizione: str, ritorno: str, email: str | None, minuti: int, altro: dict | None = None
) -> None:
	"""Stripe's Checkout session for ``pagamento``, its link kept on it for ``minuti``
	(Stripe takes 30 minutes to 24 hours). ``altro``: what a purchase adds (the
	customer, the card kept for the monthly charge, the mandate's words)."""
	# Stripe reads a Unix time; the payment keeps the server's clock
	scade = add_to_date(now_datetime(), minutes=minuti)
	stripe_secret = collegamento.chiave()
	valuta = (pagamento.currency or "EUR").lower()
	metadati = {"site": frappe.local.site, "payment": pagamento.name}
	if pagamento.invoice:
		metadati["invoice"] = pagamento.invoice
	if pagamento.appointment:
		metadati["appointment"] = pagamento.appointment
	if pagamento.get("subscription"):
		metadati["subscription"] = pagamento.subscription
	altro = dict(altro or {})
	intento = {"description": descrizione[:250], "metadata": metadati, **altro.pop("payment_intent_data", {})}
	unisci = "&" if "?" in ritorno else "?"
	sessione = cliente.chiama(
		"POST",
		"checkout/sessions",
		stripe_secret,
		{
			"mode": "payment",
			"client_reference_id": pagamento.name,
			# a customer of the centre's (a card kept for the monthly charge) has their own email
			"customer_email": None if altro.get("customer") else (email or None),
			"line_items": [
				{
					"quantity": 1,
					"price_data": {
						"currency": valuta,
						"unit_amount": R.in_centesimi(pagamento.amount, valuta),
						"product_data": {"name": descrizione[:250]},
					},
				}
			],
			"metadata": metadati,
			# a refund on the charge finds the payment by its own metadata too
			"payment_intent_data": intento,
			"success_url": f"{ritorno}{unisci}pagamento=fatto",
			"cancel_url": f"{ritorno}{unisci}pagamento=annullato",
			"expires_at": int(time.time()) + minuti * 60,
			"locale": "auto",
			**altro,
		},
		idempotenza=f"{frappe.local.site}:{pagamento.name}:{pagamento.modified}",
	)
	pagamento.db_set(
		{
			"checkout_session": sessione.get("id"),
			"checkout_url": sessione.get("url"),
			"expires_at": scade,
			"mode": R.modalita(stripe_secret),
		}
	)


# ------------------------------------------------------------------ an invoice


def perche_non_pagabile(doc) -> str | None:
	"""Why an invoice is not paid online, in the catalogue's words; None when it is."""
	from crm.invoicing import incassi

	if not collegamento.collegato():
		return "Online payments are not connected: Settings > Invoicing > Online payments."
	if not incassi.da_incassare(doc):
		return "Only an issued invoice is paid online, never a credit note."
	if cint(doc.test_document):
		return "A test invoice is never paid."
	if doc.party_type != "CRM Lead" or not doc.party:
		return "Only an invoice to a person is paid online."
	if doc.collected_on:
		return "This invoice is already collected."
	if doc.sdi_status == "scartata":
		return "The SdI sent this invoice back: correct it first."
	if incassi.da_pagare(doc) <= 0:
		return "Nothing is left to pay on this invoice."
	if _demo((FATTURA, doc.name), ("CRM Lead", doc.party)):
		return "The demo's invoices are never paid online."
	return None


def link_della_fattura(invoice: str, ritorno: str) -> dict:
	"""The link that pays ``invoice``: the one made before while it holds, else a
	new one. What is left to pay, in the invoice's currency."""
	from crm.invoicing import incassi

	doc = frappe.get_doc(FATTURA, invoice)
	motivo = perche_non_pagabile(doc)
	if motivo:
		frappe.throw(_(motivo))
	importo = round(incassi.da_pagare(doc), 2)
	adesso = now_datetime()
	for vecchio in frappe.get_all(
		PAGAMENTO,
		filters={"invoice": invoice, "status": ATTESA, "purpose": PER_FATTURA},
		fields=["name", "amount", "checkout_url", "expires_at"],
		order_by="creation desc",
	):
		# a link with an hour still to go, for the same amount, is the link
		if (
			vecchio.checkout_url
			and flt(vecchio.amount) == importo
			and vecchio.expires_at
			and get_datetime(vecchio.expires_at) > adesso + timedelta(hours=1)
		):
			return _il_link(vecchio.name)
	pagamento = frappe.get_doc(
		{
			"doctype": PAGAMENTO,
			"party": doc.party,
			"purpose": PER_FATTURA,
			"invoice": doc.name,
			"amount": importo,
			"currency": "EUR",
			"status": ATTESA,
		}
	).insert(ignore_permissions=True)
	from crm.utils import stored_value

	email = stored_value("CRM Lead", doc.party, "email")
	numero = doc.document_number or doc.name
	try:
		_sessione(
			pagamento,
			_("Invoice {0} · {1}").format(numero, _centro()),
			ritorno,
			email,
			R.ORE_FATTURA * 60 - 5,
		)
	except cliente.ErroreStripe as errore:
		pagamento.db_set({"status": NON_RIUSCITO, "last_error": str(errore)})
		frappe.throw(errore.in_parole(), title=_("Stripe"))
	return _il_link(pagamento.name)


def _il_link(nome: str) -> dict:
	riga = frappe.db.get_value(
		PAGAMENTO, nome, ["name", "checkout_url", "amount", "currency", "expires_at"], as_dict=True
	)
	return {
		"payment": riga.name,
		"url": riga.checkout_url,
		"amount": flt(riga.amount),
		"formatted_amount": _soldi(riga.amount, riga.currency),
		"expires_at": str(riga.expires_at) if riga.expires_at else None,
	}


@frappe.whitelist(methods=["POST"])
def payment_link(invoice: str) -> dict:
	"""The desk's «Payment link», to copy and send to the person."""
	from crm.permissions.livelli import verifica_nel_crm

	verifica_nel_crm("fatture.incassi", messaggio=_("You are not allowed to record payments"))
	frappe.get_doc(FATTURA, invoice).check_permission("read")
	return link_della_fattura(invoice, get_url("/area/documents"))


def pagate_online(fatture: list[str]) -> dict[str, str]:
	"""When each invoice was paid online, by its name: the area's «Paid online on…»."""
	if not fatture:
		return {}
	return {
		riga.invoice: str(getdate(riga.paid_on))
		for riga in frappe.get_all(
			PAGAMENTO,
			filters={"invoice": ["in", fatture], "status": ["in", (PAGATO, RIMBORSATO_IN_PARTE)]},
			fields=["invoice", "paid_on"],
			order_by="paid_on asc",
		)
		if riga.paid_on
	}


def per_la_fattura(doc) -> dict:
	"""What the invoice dialog says of online payments: whether a link can be made,
	what was paid online for it, and the deposit its appointment had."""
	pagati = (
		frappe.get_all(
			PAGAMENTO,
			filters={"invoice": doc.name, "status": ["in", (PAGATO, RIMBORSATO, RIMBORSATO_IN_PARTE)]},
			fields=["amount", "currency", "paid_on", "refunded_amount", "status"],
		)
		if doc.name and not doc.is_new()
		else []
	)
	# deposits paid before the advance invoice was (doc 60): the old path, said
	acconti = (
		frappe.get_all(
			PAGAMENTO,
			filters={
				"appointment": doc.appointment,
				"purpose": PER_ACCONTO,
				"status": ["in", (PAGATO, RIMBORSATO_IN_PARTE)],
				"invoice": ["is", "not set"],
			},
			fields=["amount", "currency", "paid_on", "refunded_amount"],
		)
		if doc.appointment
		else []
	)
	acconto = round(sum(flt(r.amount) - flt(r.refunded_amount) for r in acconti), 2)
	return {
		"can_link": cint(doc.docstatus) == 1 and not perche_non_pagabile(doc),
		"paid": [
			{
				"amount": flt(r.amount),
				"formatted_amount": _soldi(r.amount, r.currency),
				"paid_on": str(getdate(r.paid_on)) if r.paid_on else None,
				"refunded": flt(r.refunded_amount),
				"formatted_refunded": _soldi(r.refunded_amount, r.currency) if flt(r.refunded_amount) else "",
			}
			for r in pagati
		],
		"deposit": {"amount": acconto, "formatted_amount": _soldi(acconto)} if acconto > 0 else None,
		# the advance invoices of its appointment: this one is their balance
		"advances": fatture.per_la_fattura(doc.appointment)
		if (doc.document_type or "TD01") not in fatture.NOTE
		else [],
	}


# ------------------------------------------------------------------ a deposit at booking


def acconto_da_chiedere(servizio, prezzo, *persone: str | None) -> float:
	"""What a booking of ``servizio`` asks online before it is confirmed: nothing
	while Stripe is not connected, for the demo, or a service that asks nothing.
	The whole price is what its invoice would add up to - the fund, the VAT, the
	stamp duty on top - so the advance invoice of it is the whole invoice."""
	modo = servizio.get("online_payment")
	if not modo or not collegamento.collegato():
		return 0.0
	if _demo(("CRM Service", servizio.name), *(("CRM Lead", p) for p in persone)):
		return 0.0
	if modo == R.TUTTO and flt(prezzo) > 0:
		from crm.pagamenti import addebiti

		scheda = frappe.db.get_value(
			"CRM Billable Service", {"crm_service": servizio.name, "enabled": 1}, "name"
		)
		prezzo = addebiti.lordo(next((p for p in persone if p), None), scheda, prezzo) if scheda else prezzo
	return R.acconto(modo, servizio.get("online_deposit"), prezzo)


def chiedi_acconto(
	appuntamento, token: str, persona: str, importo: float, stato_dopo: str, email: str | None
) -> dict:
	"""The place is held: the payment written, its link made. Returns the link."""
	from crm import lingue

	valuta = appuntamento.get("currency") or lingue.valuta() or "EUR"
	pagamento = frappe.get_doc(
		{
			"doctype": PAGAMENTO,
			"party": persona,
			"purpose": PER_ACCONTO,
			"appointment": appuntamento.name,
			"access_token": token,
			"status_when_paid": stato_dopo,
			"amount": importo,
			"currency": valuta,
			"status": ATTESA,
		}
	).insert(ignore_permissions=True)
	servizio = (
		frappe.db.get_value("CRM Service", appuntamento.service, "service_name") or appuntamento.service
	)
	_sessione(
		pagamento,
		_("Deposit · {0} · {1}").format(servizio, _centro()),
		get_url(f"/prenota?token={token}"),
		email,
		R.MINUTI_ACCONTO + 1,
	)
	return _il_link(pagamento.name)


def per_la_pagina(appuntamento, token: str) -> dict | None:
	"""The deposit of a booking as /prenota shows it."""
	riga = frappe.db.get_value(
		PAGAMENTO,
		{"appointment": appuntamento.name, "access_token": token, "purpose": PER_ACCONTO},
		["name", "status", "amount", "currency", "paid_on", "checkout_url", "expires_at", "refunded_amount"],
		as_dict=True,
		order_by="creation desc",
	)
	if not riga:
		return None
	aperto = riga.status == ATTESA and riga.expires_at and get_datetime(riga.expires_at) > now_datetime()
	return {
		"state": {
			ATTESA: "waiting",
			PAGATO: "paid",
			RIMBORSATO: "refunded",
			RIMBORSATO_IN_PARTE: "paid",
			SCADUTO: "expired",
			NON_RIUSCITO: "waiting",
			ANNULLATO: "cancelled",
		}.get(riga.status, "waiting"),
		"amount": flt(riga.amount),
		"formatted_amount": _soldi(riga.amount, riga.currency),
		"paid_on": str(riga.paid_on) if riga.paid_on else None,
		"refunded": _soldi(riga.refunded_amount, riga.currency) if flt(riga.refunded_amount) else "",
		"checkout_url": riga.checkout_url if aperto else None,
	}


def in_attesa(appuntamento, token: str) -> bool:
	"""Whether a booking still waits for its deposit: nothing is told about it yet."""
	return bool(
		frappe.db.exists(
			PAGAMENTO,
			{
				"appointment": appuntamento.name,
				"access_token": token,
				"purpose": PER_ACCONTO,
				"status": ATTESA,
			},
		)
	)


# ------------------------------------------------------------------ what Stripe says


def _trova(significato: R.Significato):
	"""The payment an event is about: by its name, its session, its payment intent."""
	for campo, valore in (
		("name", significato.pagamento),
		("checkout_session", significato.sessione),
		("payment_intent", significato.intento),
	):
		if valore:
			nome = frappe.db.get_value(PAGAMENTO, {campo: valore}, "name")
			if nome:
				return frappe.get_doc(PAGAMENTO, nome, for_update=True)
	return None


def applica(significato: R.Significato) -> str | None:
	"""Apply what an event means; the payment's name, or None when it is not ours."""
	pagamento = _trova(significato)
	if not pagamento:
		return None
	if significato.cosa == R.PAGATO:
		_pagato(pagamento, significato)
	elif significato.cosa == R.SCADUTO:
		_scaduto(pagamento)
	elif significato.cosa == R.RIMBORSATO:
		_rimborsato(pagamento, significato.importo)
	elif significato.cosa == R.NON_RIUSCITO:
		if pagamento.purpose == PER_RATA and cint(pagamento.attempt):
			from crm.pagamenti import addebiti

			addebiti.non_riuscito(pagamento, significato.codice)
		else:
			# the person may try again on the same page while the link holds
			pagamento.db_set("last_error", (significato.errore or "")[:500])
	return pagamento.name


def _pagato(pagamento, significato: R.Significato) -> None:
	# a link closed at a cancellation, paid all the same, is given back below
	if pagamento.status in (PAGATO, RIMBORSATO, RIMBORSATO_IN_PARTE):
		return
	pagamento.db_set(
		{
			"status": PAGATO,
			"paid_on": now_datetime(),
			"payment_intent": significato.intento or pagamento.payment_intent,
			"checkout_session": significato.sessione or pagamento.checkout_session,
			"last_error": "",
		}
	)
	if pagamento.purpose == PER_FATTURA and pagamento.invoice:
		_fattura_pagata(pagamento)
	elif pagamento.purpose == PER_ACCONTO and pagamento.appointment:
		_acconto_pagato(pagamento)
	elif pagamento.purpose in (PER_ABBONAMENTO, PER_RATA):
		from crm.pagamenti import addebiti

		addebiti.pagato(pagamento)


def _fattura_pagata(pagamento) -> None:
	from crm.invoicing import incassi

	doc = frappe.get_doc(FATTURA, pagamento.invoice)
	if not doc.collected_on:
		incassi.segna(
			doc,
			getdate(pagamento.paid_on),
			_("Paid online by card on Stripe ({0})").format(pagamento.payment_intent or pagamento.name),
			payload={
				"payment_intent": pagamento.payment_intent,
				"payment_method": "MP08",
				"payment": pagamento.name,
			},
		)
	_di_a_chi_fattura(
		NR.PAGATA_ONLINE,
		[
			_nome(pagamento.party),
			doc.document_number or doc.name,
			_soldi(pagamento.amount, pagamento.currency),
		],
		pagamento,
	)


def _acconto_pagato(pagamento) -> None:
	from crm.api import service_booking

	appuntamento = frappe.get_doc(APPUNTAMENTO, pagamento.appointment)
	miei = [r for r in appuntamento.participants if r.access_token == pagamento.access_token]
	if not miei or all(r.status == "Cancelled" for r in miei) or appuntamento.status == "Cancelled":
		# paid after the place was freed: the money goes back at once
		pagamento.db_set("last_error", "Paid after the place was freed")
		rimborsa(pagamento.name)
		return
	if (
		appuntamento.status == "Scheduled"
		and pagamento.status_when_paid
		and pagamento.status_when_paid != "Scheduled"
	):
		appuntamento.status = pagamento.status_when_paid
		appuntamento.flags.ignore_permissions = True
		# told once, below, as /prenota tells it: never a second time as the
		# centre's yes to a request (`service_booking.on_appointment_status_change`)
		prima = frappe.flags.in_service_booking_api
		frappe.flags.in_service_booking_api = True
		try:
			appuntamento.save(ignore_permissions=True)
		finally:
			frappe.flags.in_service_booking_api = prima
	# now the booking is one: told as /prenota tells it
	service_booking.send_client_email(appuntamento, pagamento.access_token, "booked")
	service_booking.notify_staff(appuntamento, _("New online booking, deposit paid"))
	# paid before the service: invoiced the day it is paid (art. 6 DPR 633/72)
	fatture.acconto_pagato(pagamento)


def _scaduto(pagamento) -> None:
	if pagamento.status != ATTESA:
		return
	pagamento.db_set("status", SCADUTO)
	if pagamento.purpose == PER_ACCONTO and pagamento.appointment:
		libera(pagamento)


def libera(pagamento) -> None:
	"""The place a deposit held, freed: the link expired without a payment."""
	from crm.api import service_booking

	appuntamento = frappe.get_doc(APPUNTAMENTO, pagamento.appointment)
	miei = [r for r in appuntamento.participants if r.access_token == pagamento.access_token]
	if not miei or all(r.status == "Cancelled" for r in miei):
		return
	frappe.flags.in_service_booking_api = True
	try:
		service_booking._cancel_rows(
			appuntamento, pagamento.access_token, _("The deposit was not paid in time")
		)
	finally:
		frappe.flags.in_service_booking_api = False


def _rimborsato(pagamento, importo: float) -> None:
	importo = round(flt(importo), 2)
	if importo <= round(flt(pagamento.refunded_amount), 2):
		return
	stato = RIMBORSATO if importo >= round(flt(pagamento.amount), 2) else RIMBORSATO_IN_PARTE
	pagamento.db_set({"status": stato, "refunded_amount": importo, "refunded_on": now_datetime()})
	soldi = _soldi(importo, pagamento.currency)
	if pagamento.purpose != PER_ACCONTO and pagamento.invoice:
		from crm.invoicing import documento

		doc = frappe.get_doc(FATTURA, pagamento.invoice)
		documento.registra(
			doc,
			"refunded",
			_("Stripe gave back {0} of the online payment").format(soldi),
			payload={"payment_intent": pagamento.payment_intent, "payment": pagamento.name},
		)
		# never un-collected in silence: whoever manages invoicing decides
		_di_a_chi_fattura(
			NR.RIMBORSO_FATTURA,
			[soldi, _nome(pagamento.party), doc.document_number or doc.name],
			pagamento,
		)
	else:
		# a refund DottorCloud asked was recorded already, and returned above
		_di_a_chi_fattura(
			NR.RIMBORSO_ACCONTO,
			[soldi, _nome(pagamento.party)],
			pagamento,
		)
		fatture.acconto_rimborsato(pagamento)


def _nome(persona: str | None) -> str:
	return (frappe.db.get_value("CRM Lead", persona, "lead_name") if persona else None) or persona or ""


def _di_a_chi_fattura(frase: str, nomi: list, pagamento, oggetto: tuple[str, str] | None = None) -> None:
	"""Whoever manages invoicing is told. Never raises: a payment recorded is worth
	more than the notification about it."""
	try:
		from crm.notifiche.avvisi import avvisa

		for utente in frappe.get_all(
			"Has Role",
			filters={"role": "Invoicing Manager", "parenttype": "User"},
			pluck="parent",
			distinct=True,
		):
			avvisa(
				utente,
				"Invoicing",
				frase,
				nomi,
				riguarda=("CRM Lead", pagamento.party) if pagamento.party else None,
				oggetto=oggetto or (PAGAMENTO, pagamento.name),
				una_volta=True,
			)
	except Exception:
		frappe.log_error(
			title=f"Online payment {pagamento.name}: notification", message=frappe.get_traceback()
		)


# ------------------------------------------------------------------ refunds


def rimborsa(nome: str, da: str | None = None) -> bool:
	"""Give a payment's money back on Stripe: what is left of it. The webhook's
	``charge.refunded`` confirms it; this records it already. ``da``: the person who
	asked it at the desk (a courtesy, `give_back_deposit`), told in words when Stripe
	refuses; nobody for what DottorCloud gives back by itself."""
	pagamento = frappe.get_doc(PAGAMENTO, nome)
	resta = round(flt(pagamento.amount) - flt(pagamento.refunded_amount), 2)
	if resta <= 0 or not pagamento.payment_intent:
		return False
	valuta = (pagamento.currency or "EUR").lower()
	try:
		cliente.chiama(
			"POST",
			"refunds",
			collegamento.chiave(),
			{
				"payment_intent": pagamento.payment_intent,
				"amount": R.in_centesimi(resta, valuta),
				"metadata": {"site": frappe.local.site, "payment": pagamento.name},
			},
			idempotenza=f"{frappe.local.site}:{pagamento.name}:refund:{R.in_centesimi(resta, valuta)}",
		)
	except cliente.ErroreStripe as errore:
		if da:
			frappe.throw(errore.in_parole(), title=_("Online payment"))
		pagamento.db_set("last_error", f"Refund: {errore}")
		return False
	totale = round(flt(pagamento.amount), 2)
	pagamento.db_set(
		{"status": RIMBORSATO, "refunded_amount": totale, "refunded_on": now_datetime(), "refunded_by": da}
	)
	if pagamento.purpose == PER_ACCONTO:
		# its advance invoice: a credit note for what went back
		fatture.acconto_rimborsato(pagamento)
	return True


def alla_disdetta(doc, method=None) -> None:
	"""`CRM Appointment` on_update: a booking whose deposit was paid, cancelled in
	time, gets it back where the centre wants it - after the commit, in a job."""
	if doc.flags.get("importato"):
		return
	prima = doc.get_doc_before_save()
	if not prima:
		return
	_chiudi_i_link_della_disdetta(doc, prima)
	pagati = frappe.get_all(
		PAGAMENTO,
		filters={"appointment": doc.name, "purpose": PER_ACCONTO, "status": PAGATO},
		fields=["name", "access_token"],
	)
	if not pagati:
		return
	rimborsa_si, ore = collegamento.regola_dei_rimborsi()
	if not rimborsa_si:
		return
	stati_prima = {r.name: r.status for r in prima.participants}
	for riga in pagati:
		miei = [r for r in doc.participants if r.access_token == riga.access_token]
		if not miei:
			continue
		ora = doc.status == "Cancelled" or all(r.status == "Cancelled" for r in miei)
		prima_era = prima.status == "Cancelled" or all(stati_prima.get(r.name) == "Cancelled" for r in miei)
		if not ora or prima_era:
			continue
		if not R.rimborsabile(get_datetime(doc.starts_on), now_datetime(), rimborsa_si, ore):
			continue
		frappe.enqueue(
			"crm.pagamenti.pagamenti.rimborsa",
			nome=riga.name,
			enqueue_after_commit=True,
			now=frappe.in_test,
			queue="short",
		)


def _disdetti(doc, token: str) -> bool:
	miei = [r for r in doc.participants if r.access_token == token]
	return bool(miei) and (doc.status == "Cancelled" or all(r.status == "Cancelled" for r in miei))


def _chiudi_i_link_della_disdetta(doc, prima) -> None:
	"""A booking cancelled while its deposit waits: its link closes, here and on
	Stripe, so nobody pays for a place that is gone."""
	for riga in frappe.get_all(
		PAGAMENTO,
		filters={"appointment": doc.name, "purpose": PER_ACCONTO, "status": ATTESA},
		fields=["name", "access_token", "checkout_session"],
	):
		if not _disdetti(doc, riga.access_token) or _disdetti(prima, riga.access_token):
			continue
		frappe.db.set_value(PAGAMENTO, riga.name, "status", ANNULLATO, update_modified=False)
		if riga.checkout_session:
			frappe.enqueue(
				"crm.pagamenti.pagamenti.chiudi_su_stripe",
				sessione=riga.checkout_session,
				enqueue_after_commit=True,
				now=frappe.in_test,
				queue="short",
			)


def chiudi_su_stripe(sessione: str) -> None:
	"""Expire a Checkout session nobody should pay any more. One already paid is
	given back by its event (`_acconto_pagato`)."""
	try:
		cliente.chiama("POST", R.percorso("checkout", "sessions", sessione, "expire"), collegamento.chiave())
	except cliente.ErroreStripe:
		pass


# ------------------------------------------------------------------ on the appointment

#: What a deposit says on its appointment, by its status: a link that expired or
#: closed says nothing, its place went with it.
STATI_DEL_DEPOSITO = {
	ATTESA: "waiting",
	PAGATO: "paid",
	RIMBORSATO_IN_PARTE: "partly_refunded",
	RIMBORSATO: "refunded",
}


def acconti_di(appuntamenti: list[str]) -> dict[tuple[str, str], dict]:
	"""The deposit each person of these appointments was asked online - the last
	one - by (appointment, person): its state, how much, its advance invoice. The
	invoice's number and whether it is a draft only to whoever reads invoices."""
	from crm.permissions import livelli

	if not appuntamenti:
		return {}
	righe = frappe.get_all(
		PAGAMENTO,
		filters={
			"appointment": ["in", list(appuntamenti)],
			"purpose": PER_ACCONTO,
			"status": ["in", list(STATI_DEL_DEPOSITO)],
		},
		fields=[
			"name",
			"appointment",
			"party",
			"access_token",
			"status",
			"amount",
			"currency",
			"refunded_amount",
			"refunded_by",
			"invoice",
			"credit_note",
		],
		order_by="creation asc",
	)
	if not righe:
		return {}
	nomi = [n for r in righe for n in (r.invoice, r.credit_note) if n]
	fatture_viste = (
		{
			f.name: f
			for f in frappe.get_all(
				FATTURA,
				filters={"name": ["in", nomi]},
				fields=["name", "document_number", "docstatus", "test_document"],
			)
		}
		if nomi
		else {}
	)
	legge = livelli.puo("fatture.vedi")
	fuori = {}
	for riga in righe:
		fattura, nota = fatture_viste.get(riga.invoice), fatture_viste.get(riga.credit_note)
		fuori[(riga.appointment, riga.party)] = {
			"payment": riga.name,
			"party": riga.party,
			"access_token": riga.access_token,
			"state": STATI_DEL_DEPOSITO[riga.status],
			"amount": flt(riga.amount),
			"formatted_amount": _soldi(riga.amount, riga.currency),
			"formatted_refunded": _soldi(riga.refunded_amount, riga.currency)
			if flt(riga.refunded_amount)
			else "",
			"invoice": fattura.document_number if legge and fattura and fattura.docstatus == 1 else None,
			"invoice_draft": bool(legge and fattura and fattura.docstatus == 0),
			"credit_note": nota.document_number if legge and nota and nota.docstatus == 1 else None,
			"refunded_by": frappe.utils.get_fullname(riga.refunded_by) if riga.refunded_by else "",
			# a test invoice and the demo's are never given back by hand
			"test": bool(fattura and cint(fattura.test_document)),
		}
	return fuori


def nelle_righe(righe: list[dict]) -> None:
	"""The reception desk's rows: each person's deposit paid online, or waiting."""
	acconti = acconti_di([r["name"] for r in righe if r.get("name")])
	if not acconti:
		return
	for riga in righe:
		for persona in riga.get("participants") or []:
			acconto = acconti.get((riga["name"], persona.get("party")))
			if acconto and persona.get("party_type") == "CRM Lead":
				persona["deposit"] = _per_la_pagina(acconto)


def _per_la_pagina(acconto: dict) -> dict:
	return {chiave: valore for chiave, valore in acconto.items() if chiave not in ("access_token", "test")}


def del_appuntamento(doc, righe: list[dict]) -> None:
	"""The appointment's panel: each person's deposit on their row, kept when their
	place was cancelled without its refund, and whether the desk may give it back
	(`give_back_deposit`)."""
	acconti = acconti_di([doc.name])
	if not acconti:
		return
	for riga in righe:
		acconto = acconti.get((doc.name, riga.get("party")))
		if not acconto or riga.get("party_type") != "CRM Lead":
			continue
		pagato = acconto["state"] in ("paid", "partly_refunded")
		trattenuto = pagato and _disdetti(doc, acconto["access_token"])
		riga["deposit"] = {
			**_per_la_pagina(acconto),
			"kept": trattenuto,
			"can_give_back": trattenuto and not _perche_non_restituibile(acconto, doc),
		}


def _perche_non_restituibile(acconto: dict, doc) -> str | None:
	"""Why the desk cannot give this deposit back by hand; None when it can."""
	from crm.permissions import livelli

	if not livelli.puo("fatture.incassi"):
		return _("Giving a deposit back is for whoever records the payments")
	if acconto["state"] not in ("paid", "partly_refunded"):
		return _("This deposit is not paid, or was given back already")
	if not _disdetti(doc, acconto["access_token"]):
		return _("The deposit is given back once the place is cancelled")
	if acconto["test"] or _demo((APPUNTAMENTO, doc.name), ("CRM Lead", acconto.get("party"))):
		return _("A test or demo deposit is never given back on Stripe")
	if not collegamento.collegato():
		return _("Stripe is not connected")
	return None


@frappe.whitelist(methods=["POST"])
def give_back_deposit(payment: str) -> dict:
	"""«Give the deposit back», a courtesy: the deposit somebody who cancelled late
	leaves to the centre, given back on Stripe with its credit note - the path a
	cancellation in time takes - and recorded with who did it."""
	from crm.permissions import livelli

	livelli.verifica("fatture.incassi")
	pagamento = frappe.get_doc(PAGAMENTO, payment)
	pagamento.check_permission("read")
	if pagamento.purpose != PER_ACCONTO or not pagamento.appointment:
		frappe.throw(_("This payment is not a booking's deposit"))
	doc = frappe.get_doc(APPUNTAMENTO, pagamento.appointment)
	acconto = acconti_di([doc.name]).get((doc.name, pagamento.party))
	if not acconto or acconto["payment"] != pagamento.name:
		frappe.throw(_("This deposit is not paid, or was given back already"))
	motivo = _perche_non_restituibile(acconto, doc)
	if motivo:
		frappe.throw(motivo)
	if not rimborsa(pagamento.name, da=frappe.session.user):
		frappe.throw(_("This deposit is not paid, or was given back already"))
	righe = [r.as_dict() for r in doc.participants]
	del_appuntamento(doc, righe)
	return {
		"deposit": next(
			(r["deposit"] for r in righe if (r.get("deposit") or {}).get("payment") == pagamento.name), None
		)
	}


# ------------------------------------------------------------------ every ten minutes


def ogni_dieci_minuti() -> None:
	"""The links nobody paid, past their time: asked of Stripe (a payment may have
	come while its event did not), then expired there and here - a deposit's place
	freed."""
	if not collegamento.collegato():
		return
	adesso = now_datetime()
	stripe_secret = collegamento.chiave()
	for riga in frappe.get_all(
		PAGAMENTO,
		filters={"status": ATTESA, "expires_at": ["<", adesso]},
		fields=["name", "checkout_session", "expires_at"],
		limit=200,
	):
		if not R.scaduto(get_datetime(riga.expires_at), adesso):
			continue
		frappe.db.savepoint("pagamento_scaduto")
		try:
			_chiudi(riga, stripe_secret)
			if not frappe.flags.in_test:
				frappe.db.commit()  # nosemgrep: frappe-manual-commit — each link on its own
		except Exception:
			frappe.db.rollback(save_point="pagamento_scaduto")
			frappe.log_error(title=f"Online payment {riga.name}: expiry", message=frappe.get_traceback())


def _chiudi(riga, stripe_secret: str) -> None:
	sessione = {}
	if riga.checkout_session:
		try:
			sessione = cliente.chiama(
				"GET", R.percorso("checkout", "sessions", riga.checkout_session), stripe_secret
			)
			if sessione.get("status") == "open":
				sessione = cliente.chiama(
					"POST", R.percorso("checkout", "sessions", riga.checkout_session, "expire"), stripe_secret
				)
		except cliente.ErroreStripe as errore:
			# Stripe away: the next round asks again, for two hours at most
			if errore.stato != 404 and get_datetime(riga.expires_at) > now_datetime() - timedelta(hours=2):
				return
			sessione = {}
	if sessione.get("payment_status") == "paid":
		applica(
			R.Significato(
				R.PAGATO,
				sessione=sessione.get("id"),
				intento=sessione.get("payment_intent"),
				importo=R.da_centesimi(sessione.get("amount_total"), sessione.get("currency") or "eur"),
				pagamento=riga.name,
			)
		)
		return
	_scaduto(frappe.get_doc(PAGAMENTO, riga.name, for_update=True))


# ------------------------------------------------------------------ with the person


def cancella_con_la_persona(doc, method=None) -> None:
	"""A person's online payments go with them, and their customer on Stripe's
	account here (the customer there stays the centre's: Stripe keeps its records)."""
	for doctype in (PAGAMENTO, "CRM Stripe Customer"):
		for nome in frappe.get_all(doctype, filters={"party": doc.name}, pluck="name"):
			frappe.delete_doc(doctype, nome, ignore_permissions=True, force=True)


def get_permission_query_conditions(user: str | None = None) -> str:
	"""A payment is listed to whoever sees its person."""
	return della_persona(PAGAMENTO, user)


def get_customer_permission_query_conditions(user: str | None = None) -> str:
	"""A person's customer on Stripe is listed to whoever sees them."""
	return della_persona("CRM Stripe Customer", user)


def della_persona(doctype: str, user: str | None = None) -> str:
	"""A record of a person's (a payment, a customer) is listed to whoever sees them."""
	from crm.permissions import org_hierarchy

	visibili = org_hierarchy.visible_leads(user)
	if visibili is None:
		return ""
	riga = frappe.qb.DocType(doctype)
	return riga.party.isin(visibili or [""]).get_sql(
		with_namespace=True, quote_char="`", secondary_quote_char="'"
	)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if (ptype or "read") not in ("read", "print", "export", "report"):
		# written by DottorCloud as Stripe answers, never by hand
		return "System Manager" in frappe.get_roles(user)
	return not doc.get("party") or bool(frappe.has_permission("CRM Lead", "read", doc=doc.party, user=user))
