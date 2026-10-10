# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions bought from the client area, and charged month by month on the
card saved for them (doc 60). The rules are `addebiti_regole`.

Stripe only collects: never Stripe Billing, its subscriptions or its invoices,
which are not Italian ones. The subscription is DottorCloud's, sold through its own
code (`abbonamenti.nuovo`), and each instalment is invoiced through the engine the
day its money arrives.

- **Bought from the area**: a type the centre marked «Sold online from the area»,
  with Stripe connected and «Sell subscriptions from the client area» on. A
  Checkout for the whole price, or - paid by the month, where the centre charges a
  saved card - for the first instalment with the card kept for the next ones
  (`setup_future_usage=off_session`, the person as a customer of the centre's
  account, the mandate's words on Stripe's page). Paid: sold from today, the
  instalment invoiced and collected; never paid, nothing is sold.
- **The monthly charge**: on an instalment's day the daily round of the
  subscriptions (`abbonamenti.ogni_giorno`) charges the card first, off session,
  with one idempotency key per try; only when the money arrived is the instalment
  invoiced, collected by card. A charge that does not go through: no invoice, the
  person told with the way to pay from the area, the centre told; tried again 3
  and 7 days after; then the instalment is invoiced as any other.
- **Stopped** by the person from the area, or by the desk: no further charge; the
  instalments stay owed as the subscription says.

Stripe keeps the card: DottorCloud keeps its id (`pm_…`), the brand, the last four
digits and the expiry it shows - never more. Never for the demo, never in the
area's preview.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, formatdate, get_fullname, getdate, now_datetime

from crm.notifiche import regole as NR
from crm.pagamenti import addebiti_regole as R
from crm.pagamenti import cliente, collegamento, fatture, pagamenti
from crm.pagamenti import regole as RP
from crm.permissions import livelli

ABBONAMENTO = "CRM Subscription"
TIPO = "CRM Subscription Type"
CLIENTE = "CRM Stripe Customer"
PAGAMENTO = pagamenti.PAGAMENTO
FATTURA = "CRM Invoice"


def _demo(*riferimenti) -> bool:
	return pagamenti._demo(*riferimenti)


def _giorno(valore) -> str:
	return formatdate(getdate(valore), "d MMMM yyyy")


# ------------------------------------------------------------------ what it costs


def lordo(persona: str | None, billable_service: str | None, importo, provider: str | None = None) -> float:
	"""What the person pays for ``importo`` of a service or a subscription: its
	invoice adds the fund, the VAT and the stamp duty on top, as the desk's would.
	The amount itself where the invoice cannot be added up yet."""
	if not billable_service or not flt(importo):
		return flt(importo)
	from crm.invoicing import documento, emissione, incassi

	try:
		with fatture.come_dottorcloud():
			fattura = frappe.new_doc(FATTURA)
			fattura.recipient_type = "persona_fisica"
			if persona:
				fattura.party_type, fattura.party = "CRM Lead", persona
			fattura.append(
				"items",
				{
					"billable_service": billable_service,
					"service_provider": provider
					or frappe.db.get_value("CRM Billable Service", billable_service, "default_provider"),
					"qty": 1,
					"rate": flt(importo),
				},
			)
			fatture.prepara(fattura)
			if emissione._da_completare(fattura):
				return flt(importo)
			documento.prepara(fattura)
			return round(incassi.da_pagare(fattura), 2) or flt(importo)
	except Exception:
		frappe.clear_last_message()
		return flt(importo)


def lordo_della_rata(doc, riga) -> float:
	"""What the person pays for an instalment: its invoice, added up in memory."""
	from crm.invoicing import api, documento, incassi

	fattura = api.fattura_della_rata(doc, riga)
	fatture.prepara(fattura)
	documento.prepara(fattura)
	return round(incassi.da_pagare(fattura), 2)


# ------------------------------------------------------------------ what the area sells


def _tipi() -> list[dict]:
	return frappe.get_all(
		TIPO,
		filters={"enabled": 1, "sold_online": 1},
		fields=[
			"name",
			"type_name",
			"description",
			"enabled",
			"sold_online",
			"months",
			"payment",
			"price",
			"currency",
			"billable_service",
			"entries",
			"entries_count",
			"auto_renew",
		],
		order_by="type_name asc",
	)


def codice_fiscale_da_chiedere(persona: str, scheda: str | None) -> str:
	"""Whether «Buy» asks the person's codice fiscale, where their billing details
	lack it: the instalment's invoice is issued the day it is paid, and a healthcare
	one needs it (`regole.codice_fiscale_da_chiedere`)."""
	from crm.invoicing import anagrafica, scelte
	from crm.invoicing.engine import voci

	if anagrafica.ha_il_codice(persona):
		return RP.CF_NO
	sanitaria = frappe.db.get_value("CRM Billable Service", scheda, "is_healthcare") if scheda else None
	return RP.codice_fiscale_da_chiedere(
		True, None if sanitaria is None else bool(sanitaria), scelte.profilo() == voci.SANITARIO
	)


def in_vendita(persona: str) -> list[dict]:
	"""The subscriptions the area offers ``persona``, each with what they pay: at once,
	or the first instalment and how many; nothing for the demo, nor where the centre
	does not sell."""
	from crm.scheduling import abbonamenti_regole as AR

	vende, addebita = collegamento.vendite()
	if not vende or _demo(("CRM Lead", persona)):
		return []
	fatto = []
	for tipo in _tipi():
		# the demo's types are never paid online, as its services
		if R.perche_non_in_vendita(tipo, vende, addebita) or _demo((TIPO, tipo.name)):
			continue
		mesi = AR.entro(tipo.months, AR.MESI)
		rate = AR.rate(getdate(), mesi, flt(tipo.price), tipo.payment)
		prima = lordo(persona, tipo.billable_service, rate[0][1])
		totale = prima if len(rate) == 1 else lordo(persona, tipo.billable_service, tipo.price)
		fatto.append(
			{
				"name": tipo.name,
				"title": tipo.type_name or tipo.name,
				"description": tipo.description or "",
				"months": mesi,
				"monthly": len(rate) > 1,
				"instalments": len(rate),
				"first": prima,
				"total": totale,
				"currency": tipo.currency or "EUR",
				"formatted_first": pagamenti._soldi(prima, tipo.currency),
				"formatted_total": pagamenti._soldi(totale, tipo.currency),
				"until": str(AR.fine(getdate(), mesi)),
				# asked in the sheet where their billing details lack it
				"fiscal_code": codice_fiscale_da_chiedere(persona, tipo.billable_service),
				"entries": tipo.entries,
				"entries_count": cint(tipo.entries_count),
				"services": [
					frappe.db.get_value("CRM Service", s, "service_name") or s
					for s in frappe.get_all(
						"CRM Subscription Service",
						filters={"parenttype": TIPO, "parent": tipo.name},
						pluck="service",
					)
				],
			}
		)
	return fatto


def mandato(importo: str, fino: str) -> str:
	"""The words the person agrees to before a card is kept for the monthly charge."""
	return _(
		"You authorise the centre to charge {0} every month on the card until {1}; you can stop it from your area."
	).format(importo, fino)


def _cliente_di(persona: str) -> str:
	"""The person as a customer of the centre's Stripe account: the one made before
	on this account, else a new one."""
	from crm.utils import stored_value

	impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
	gia = frappe.db.get_value(
		CLIENTE, {"party": persona, "account_id": impostazioni.account_id}, "customer_id"
	)
	if gia:
		return gia
	risposta = cliente.chiama(
		"POST",
		"customers",
		collegamento.chiave(impostazioni),
		{
			"email": stored_value("CRM Lead", persona, "email") or None,
			"name": frappe.db.get_value("CRM Lead", persona, "lead_name") or None,
			"metadata": {"site": frappe.local.site, "person": persona},
		},
		idempotenza=f"{frappe.local.site}:customer:{persona}:{impostazioni.account_id}",
	)
	frappe.get_doc(
		{
			"doctype": CLIENTE,
			"party": persona,
			"customer_id": risposta.get("id"),
			"account_id": impostazioni.account_id,
			"mode": impostazioni.mode,
		}
	).insert(ignore_permissions=True)
	return risposta.get("id")


def compra(persona: str, tipo: str, ritorno: str, codice_fiscale: str | None = None) -> dict:
	"""«Buy» in the area: the payment written, Stripe's page for the whole price or
	the first instalment. Nothing is sold until Stripe says paid. ``codice_fiscale``,
	asked where the billing details lack it, goes in them first: the instalment's
	invoice is issued with it."""
	from crm.invoicing import anagrafica
	from crm.scheduling import abbonamenti_regole as AR
	from crm.utils import stored_value

	codice = anagrafica.codice_scritto(codice_fiscale)

	vende, addebita = collegamento.vendite()
	riga = frappe.db.get_value(TIPO, tipo, ["*"], as_dict=True)
	motivo = R.perche_non_in_vendita(riga or {}, vende, addebita, collegamento.collegato())
	if motivo:
		frappe.throw(_(motivo))
	if _demo(("CRM Lead", persona), (TIPO, tipo)):
		frappe.throw(_("The demo's people never pay online."))
	if not codice and codice_fiscale_da_chiedere(persona, riga.billable_service) == RP.CF_OBBLIGATORIO:
		frappe.throw(_("Write the codice fiscale of whom the subscription is for: its invoice needs it"))
	anagrafica.scrivi_se_manca(persona, codice)
	mesi = AR.entro(riga.months, AR.MESI)
	rate = AR.rate(getdate(), mesi, flt(riga.price), riga.payment)
	importo = lordo(persona, riga.billable_service, rate[0][1])
	pagamento = frappe.get_doc(
		{
			"doctype": PAGAMENTO,
			"party": persona,
			"purpose": pagamenti.PER_ABBONAMENTO,
			"subscription_type": tipo,
			"amount": importo,
			"currency": riga.currency or "EUR",
			"status": pagamenti.ATTESA,
		}
	).insert(ignore_permissions=True)
	altro = {}
	if len(rate) > 1:
		# the card kept for the next instalments, on the person's own customer
		pagamento.db_set("customer", _cliente_di(persona))
		altro = {
			"customer": pagamento.customer,
			"payment_intent_data": {"setup_future_usage": "off_session"},
			"custom_text": {
				"submit": {
					"message": mandato(
						pagamenti._soldi(importo, riga.currency), _giorno(AR.fine(getdate(), mesi))
					)[:1000]
				}
			},
		}
	try:
		pagamenti._sessione(
			pagamento,
			_("Subscription {0} · {1}").format(riga.type_name or tipo, pagamenti._centro()),
			ritorno,
			stored_value("CRM Lead", persona, "email"),
			60,
			altro,
		)
	except cliente.ErroreStripe as errore:
		pagamento.db_set({"status": pagamenti.NON_RIUSCITO, "last_error": str(errore)})
		frappe.throw(errore.in_parole(), title=_("Stripe"))
	return pagamenti._il_link(pagamento.name)


# ------------------------------------------------------------------ paid


def pagato(pagamento) -> None:
	"""`pagamenti._pagato`: a subscription bought, or an instalment paid."""
	with fatture.come_dottorcloud():
		if pagamento.purpose == pagamenti.PER_ABBONAMENTO:
			_venduto(pagamento)
		elif pagamento.purpose == pagamenti.PER_RATA:
			_rata_pagata(pagamento)


def _venduto(pagamento) -> None:
	"""Sold from today through the desk's own code, its first instalment invoiced and
	collected; the card kept where it is paid by the month."""
	from crm.scheduling import abbonamenti

	if pagamento.subscription:
		return
	frappe.db.savepoint("crm_abbonamento_comprato")
	try:
		doc = abbonamenti.nuovo(pagamento.party, pagamento.subscription_type, getdate(pagamento.paid_on))
	except Exception:
		# the type went off sale while the person paid: the money goes back
		frappe.db.rollback(save_point="crm_abbonamento_comprato")
		frappe.clear_last_message()
		frappe.log_error(title=f"Online payment {pagamento.name}: not sold", message=frappe.get_traceback())
		pagamento.db_set("last_error", "Not sold: the money goes back")
		pagamenti.rimborsa(pagamento.name)
		return
	pagamento.db_set("subscription", doc.name)
	if pagamento.customer:
		_tieni_la_carta(doc, pagamento)
	riga = doc.instalments[0] if doc.instalments else None
	if riga and doc.billable_service:
		nome = abbonamenti.fattura(doc, riga)
		fatture.emetti_pagata(frappe.get_doc(FATTURA, nome), pagamento)
		pagamento.db_set("invoice", nome)
	pagamenti._di_a_chi_fattura(
		NR.ABBONAMENTO_COMPRATO,
		[
			pagamenti._nome(pagamento.party),
			doc.subscription_type,
			pagamenti._soldi(pagamento.amount, pagamento.currency),
		],
		pagamento,
		oggetto=(ABBONAMENTO, doc.name),
	)


def _tieni_la_carta(doc, pagamento) -> None:
	"""The card the first instalment was paid with, kept for the next ones: Stripe's
	id, and what the page shows of it."""
	try:
		intento = cliente.chiama(
			"GET",
			RP.percorso("payment_intents", pagamento.payment_intent),
			collegamento.chiave(),
			{"expand": ["payment_method"]},
		)
	except cliente.ErroreStripe as errore:
		frappe.log_error(title=f"Online payment {pagamento.name}: the card", message=str(errore))
		return
	metodo = intento.get("payment_method") or {}
	if isinstance(metodo, str):
		metodo = {"id": metodo}
	carta = R.carta(metodo.get("card")) or {}
	doc.db_set(
		{
			"card_charges": 1 if metodo.get("id") else 0,
			"stripe_customer": pagamento.customer,
			"stripe_payment_method": metodo.get("id"),
			"card_brand": carta.get("brand"),
			"card_last4": carta.get("last4"),
			"card_expiry": carta.get("expiry"),
			"card_charges_from": now_datetime(),
			"card_charges_stopped_on": None,
			"card_charges_stopped_by": None,
		},
		update_modified=False,
	)
	pagamento.db_set("payment_method", metodo.get("id"))


def _rata_pagata(pagamento) -> None:
	"""An instalment paid - charged on the card, or from the area's link: invoiced
	now and collected by card."""
	from crm.invoicing import incassi
	from crm.scheduling import abbonamenti

	doc = frappe.get_doc(ABBONAMENTO, pagamento.subscription)
	riga = next((r for r in doc.instalments if r.name == pagamento.instalment), None)
	if not riga:
		return
	riga.db_set("charge_problem", None, update_modified=False)
	if abbonamenti._fattura_viva(riga.invoice):
		fattura = frappe.get_doc(FATTURA, riga.invoice)
		if fattura.docstatus == 0:
			fatture.emetti_pagata(fattura, pagamento)
		elif not fattura.collected_on and incassi.da_incassare(fattura):
			incassi.segna(
				fattura,
				getdate(pagamento.paid_on),
				_("Paid online by card on Stripe ({0})").format(pagamento.payment_intent or pagamento.name),
				payload={
					"payment_intent": pagamento.payment_intent,
					"payment_method": "MP08",
					"payment": pagamento.name,
				},
			)
		pagamento.db_set("invoice", fattura.name)
		return
	nome = abbonamenti.fattura(doc, riga)
	fatture.emetti_pagata(frappe.get_doc(FATTURA, nome), pagamento)
	pagamento.db_set("invoice", nome)


# ------------------------------------------------------------------ the monthly charge


def attivo(doc) -> bool:
	"""Whether a subscription's instalments are charged on its card now."""
	return bool(cint(doc.get("card_charges")) and doc.get("stripe_payment_method"))


def _conferma() -> None:
	"""A try kept before Stripe is asked, and its outcome after: money taken is never
	without its record."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — a charge is written before it leaves


def _pagamenti_della_rata(doc, riga) -> list:
	"""The payments of an instalment still waiting for Stripe, or paid."""
	return frappe.get_all(
		PAGAMENTO,
		filters={
			"subscription": doc.name,
			"instalment": riga.name,
			"purpose": pagamenti.PER_RATA,
			"status": ("in", (pagamenti.ATTESA, pagamenti.PAGATO)),
		},
		fields=["name", "status"],
	)


def ogni_giorno(oggi=None) -> None:
	"""Daily, before the subscriptions' own round (`abbonamenti.ogni_giorno`): the
	instalments due of the subscriptions charged on their card, charged - each try
	kept before Stripe is asked. One that fails leaves the others alone."""
	from crm.scheduling import abbonamenti_regole as AR

	_vende, addebita_si = collegamento.vendite()
	if not addebita_si:
		return
	oggi = getdate(oggi)
	nomi = frappe.get_all(
		ABBONAMENTO,
		filters={"card_charges": 1, "status": ("in", [AR.ATTIVO, AR.SOSPESO, AR.SCADUTO])},
		pluck="name",
	)
	for nome in nomi:
		try:
			doc = frappe.get_doc(ABBONAMENTO, nome)
			if attivo(doc) and not _demo((ABBONAMENTO, doc.name), ("CRM Lead", doc.lead)):
				with fatture.come_dottorcloud():
					_le_dovute(doc, oggi)
			_conferma()
		except Exception:
			frappe.db.rollback()
			frappe.clear_last_message()
			frappe.log_error(
				title="Subscription: the card charge", reference_doctype=ABBONAMENTO, reference_name=nome
			)


def _le_dovute(doc, oggi) -> None:
	from crm.scheduling import abbonamenti

	for riga in doc.instalments:
		if getdate(riga.due_on) > oggi or abbonamenti._fattura_viva(riga.invoice):
			continue
		gia = _pagamenti_della_rata(doc, riga)
		pagato_ = next((p for p in gia if p.status == pagamenti.PAGATO), None)
		if pagato_:
			# paid, its invoice not made yet (an error in between): made now
			pagato(frappe.get_doc(PAGAMENTO, pagato_.name))
			continue
		if gia:
			# Stripe has not said yet: never a second try meanwhile
			continue
		ultimo = getdate(riga.last_charge_on) if riga.last_charge_on else None
		if R.da_tentare(oggi, getdate(riga.due_on), cint(riga.charge_attempts), ultimo):
			addebita(doc, riga, oggi)


def tenute(doc, oggi) -> set[str]:
	"""The instalments due the subscriptions' round leaves alone today: charged on
	the card, or waiting for it to be tried again. The others are invoiced as ever."""
	from crm.scheduling import abbonamenti

	_vende, addebita_si = collegamento.vendite()
	fatto = set()
	for riga in doc.instalments:
		if getdate(riga.due_on) > oggi or abbonamenti._fattura_viva(riga.invoice):
			continue
		if _pagamenti_della_rata(doc, riga):
			fatto.add(riga.name)
		elif attivo(doc) and addebita_si and not R.esauriti(riga.charge_attempts):
			fatto.add(riga.name)
	return fatto


def addebita(doc, riga, oggi) -> str:
	"""One try at an instalment on the saved card: the payment written first, then
	Stripe asked off session with this try's own key, so a round run twice charges
	once. The answer is applied as the webhook's would be, whichever comes first."""
	tentativo = cint(riga.charge_attempts) + 1
	importo = lordo_della_rata(doc, riga)
	pagamento = frappe.get_doc(
		{
			"doctype": PAGAMENTO,
			"party": doc.lead,
			"purpose": pagamenti.PER_RATA,
			"subscription": doc.name,
			"subscription_type": doc.subscription_type,
			"instalment": riga.name,
			"amount": importo,
			"currency": riga.currency or doc.currency or "EUR",
			"status": pagamenti.ATTESA,
			"attempt": tentativo,
			"customer": doc.stripe_customer,
			"payment_method": doc.stripe_payment_method,
			"mode": RP.modalita(collegamento.chiave()),
		}
	).insert(ignore_permissions=True)
	riga.db_set({"charge_attempts": tentativo, "last_charge_on": oggi}, update_modified=False)
	_conferma()
	valuta = (pagamento.currency or "EUR").lower()
	try:
		intento = cliente.chiama(
			"POST",
			"payment_intents",
			collegamento.chiave(),
			{
				"amount": RP.in_centesimi(importo, valuta),
				"currency": valuta,
				"customer": doc.stripe_customer,
				"payment_method": doc.stripe_payment_method,
				"off_session": True,
				"confirm": True,
				"description": _("Subscription {0} · {1}").format(doc.subscription_type, pagamenti._centro())[
					:250
				],
				"metadata": {
					"site": frappe.local.site,
					"payment": pagamento.name,
					"subscription": doc.name,
					"instalment": riga.name,
					"charge": RP.ADDEBITO,
				},
			},
			idempotenza=R.chiave(frappe.local.site, doc.name, riga.name, tentativo),
		)
	except cliente.ErroreStripe as errore:
		if errore.della_carta:
			non_riuscito(pagamento, errore.rifiuto or errore.codice)
		else:
			# Stripe away: not a try, tomorrow's round asks again
			riga.db_set("charge_attempts", tentativo - 1, update_modified=False)
			pagamento.db_set({"status": pagamenti.NON_RIUSCITO, "last_error": str(errore)})
		return pagamento.name
	pagamento.db_set("payment_intent", intento.get("id"))
	_conferma()
	stato = intento.get("status")
	if stato == "succeeded":
		pagamenti.applica(
			RP.Significato(
				RP.PAGATO,
				intento=intento.get("id"),
				importo=RP.da_centesimi(intento.get("amount_received") or intento.get("amount"), valuta),
				pagamento=pagamento.name,
			)
		)
	elif stato in ("requires_action", "requires_payment_method", "canceled"):
		problema = intento.get("last_payment_error") or {}
		non_riuscito(
			pagamento,
			"authentication_required"
			if stato == "requires_action"
			else problema.get("decline_code") or problema.get("code"),
		)
	# processing: the webhook says how it went
	return pagamento.name


def non_riuscito(pagamento, codice: str | None) -> None:
	"""A charge that did not go through, applied once: no invoice; the person told
	with the way to pay from the area, and when the card is tried again; the centre
	told. After the last try the instalment is invoiced as any other."""
	pagamento.reload()
	if pagamento.status != pagamenti.ATTESA:
		return
	with fatture.come_dottorcloud():
		_non_riuscito(pagamento, codice)


def _non_riuscito(pagamento, codice: str | None) -> None:
	motivo = R.motivo(codice)
	pagamento.db_set({"status": pagamenti.NON_RIUSCITO, "last_error": motivo})
	doc = frappe.get_doc(ABBONAMENTO, pagamento.subscription)
	riga = next((r for r in doc.instalments if r.name == pagamento.instalment), None)
	if not riga:
		return
	riga.db_set("charge_problem", motivo, update_modified=False)
	esauriti = R.esauriti(riga.charge_attempts)
	prossimo = None if esauriti else R.prossimo(getdate(riga.due_on), cint(riga.charge_attempts))
	try:
		_scrivi_alla_persona(doc, pagamento, motivo, prossimo)
	except Exception:
		frappe.clear_last_message()
		frappe.log_error(
			title=f"Online payment {pagamento.name}: the message", message=frappe.get_traceback()
		)
	soldi = pagamenti._soldi(pagamento.amount, pagamento.currency)
	pagamenti._di_a_chi_fattura(
		NR.ADDEBITO_NON_RIUSCITO,
		[soldi, pagamenti._nome(doc.lead), _(motivo)],
		pagamento,
		oggetto=(ABBONAMENTO, doc.name),
	)
	if esauriti:
		pagamenti._di_a_chi_fattura(
			NR.ADDEBITI_ESAURITI,
			[pagamenti._nome(doc.lead), doc.subscription_type],
			pagamento,
			oggetto=(ABBONAMENTO, doc.name),
		)


def _scrivi_alla_persona(doc, pagamento, motivo: str, prossimo) -> None:
	"""«The payment did not go through»: by email with the way into the area, and by
	SMS where the centre's payment reminders go by SMS too (never to who wrote STOP)."""
	from frappe.utils import escape_html

	from crm.invoicing import solleciti
	from crm.lingue import con_l_apostrofo
	from crm.moduli.richieste import nome_del_centro

	dove = solleciti._dove(doc.lead)
	centro = nome_del_centro() or _("the centre")
	soldi = pagamenti._soldi(pagamento.amount, pagamento.currency)
	frase = _("The monthly charge of {0} for your subscription {1} did not go through: {2}").format(
		soldi, doc.subscription_type, _(motivo)
	)
	dopo = (
		con_l_apostrofo(_("We will try the card again on {0}.").format(_giorno(prossimo)))
		if prossimo
		else _("The card will not be tried again: the instalment stays to pay.")
	)
	if dove.email:
		from crm.area import accesso
		from crm.area import collegamento as porta
		from crm.posta.aspetto import pulsante

		bottone = ""
		if dove.email.lower() in {(r.user or "").lower() for r in accesso.accessi_aperti(dove.lead)}:
			bottone = pulsante(
				porta.crea(dove.email.lower(), dove.lead, "card_charge", "appointments"),
				_("Pay from your area"),
			)
		esc = escape_html
		frappe.sendmail(
			recipients=[dove.email],
			subject=_("Your payment did not go through"),
			header=_("Your payment did not go through"),
			with_container=True,
			message="".join(
				[
					f"<p>{esc(_('Hi {0},').format(dove.nome))}</p>" if dove.nome else "",
					f"<p>{esc(frase)}</p>",
					f"<p>{esc(dopo)}</p>",
					f"<p>{esc(_('You can pay it now from your area, by card.'))}</p>",
					bottone,
					f'<p class="text-muted text-small">{esc(centro)}</p>',
				]
			),
			reference_doctype=ABBONAMENTO,
			reference_name=doc.name,
		)
	conf = solleciti.impostazioni()
	if conf.sms and dove.numero and not dove.fermato:
		from crm.api.sms import create_sms, deliver_sms
		from crm.telephony import sms

		da = sms.mittente()
		if da:
			messaggio = create_sms(
				type="Outgoing",
				from_number=da,
				to=dove.numero,
				message=f"{centro}: {frase} {dopo} {_('You can pay it from your area.')}",
				reference_doctype="CRM Lead",
				reference_name=dove.lead,
			)
			deliver_sms(messaggio)


# ------------------------------------------------------------------ paid from the area, stopped


def link_della_rata(doc, nome_rata: str, ritorno: str) -> dict:
	"""«Pay now» on a subscription whose card was not charged: Stripe's page for that
	instalment; paid, it is invoiced the same way. One already invoiced is paid by its
	invoice's own link."""
	from crm.scheduling import abbonamenti

	riga = next((r for r in doc.instalments if r.name == nome_rata), None)
	if not riga or getdate(riga.due_on) > getdate():
		frappe.throw(_("Nothing is left to pay on this subscription."))
	if abbonamenti._fattura_viva(riga.invoice):
		if frappe.db.get_value(FATTURA, riga.invoice, "docstatus") == 1:
			return pagamenti.link_della_fattura(riga.invoice, ritorno)
		frappe.throw(_("Nothing is left to pay on this subscription."))
	if _demo((ABBONAMENTO, doc.name), ("CRM Lead", doc.lead)):
		frappe.throw(_("The demo's people never pay online."))
	importo = lordo_della_rata(doc, riga)
	pagamento = frappe.get_doc(
		{
			"doctype": PAGAMENTO,
			"party": doc.lead,
			"purpose": pagamenti.PER_RATA,
			"subscription": doc.name,
			"subscription_type": doc.subscription_type,
			"instalment": riga.name,
			"amount": importo,
			"currency": riga.currency or doc.currency or "EUR",
			"status": pagamenti.ATTESA,
		}
	).insert(ignore_permissions=True)
	from crm.utils import stored_value

	try:
		pagamenti._sessione(
			pagamento,
			_("Subscription {0} · {1}").format(doc.subscription_type, pagamenti._centro()),
			ritorno,
			stored_value("CRM Lead", doc.lead, "email"),
			RP.ORE_FATTURA * 60 - 5,
		)
	except cliente.ErroreStripe as errore:
		pagamento.db_set({"status": pagamenti.NON_RIUSCITO, "last_error": str(errore)})
		frappe.throw(errore.in_parole(), title=_("Stripe"))
	return pagamenti._il_link(pagamento.name)


def interrompi(doc, dalla_persona: bool) -> None:
	"""No further charge on the card: Stripe forgets it for the centre too. The
	instalments stay owed as the subscription says."""
	if not cint(doc.card_charges):
		return
	if doc.stripe_payment_method and collegamento.collegato():
		try:
			cliente.chiama(
				"POST",
				RP.percorso("payment_methods", doc.stripe_payment_method, "detach"),
				collegamento.chiave(),
			)
		except cliente.ErroreStripe as errore:
			frappe.log_error(title=f"Subscription {doc.name}: the card", message=str(errore))
	chi = frappe.session.user
	doc.db_set(
		{
			"card_charges": 0,
			"card_charges_stopped_on": now_datetime(),
			"card_charges_stopped_by": _("The person, from their area")
			if dalla_persona
			else get_fullname(chi),
		},
		update_modified=False,
	)
	if dalla_persona:
		finto = frappe._dict(name=doc.name, party=doc.lead)
		pagamenti._di_a_chi_fattura(
			NR.ADDEBITI_INTERROTTI,
			[pagamenti._nome(doc.lead), doc.subscription_type],
			finto,
			oggetto=(ABBONAMENTO, doc.name),
		)


@frappe.whitelist(methods=["POST"])
def stop_card_charges(name: str) -> dict:
	"""The desk's «Stop the charges»."""
	from crm.scheduling import abbonamenti

	livelli.verifica("agenda.abbonamenti")
	doc = abbonamenti._abbonamento(name)
	doc.check_permission("write")
	interrompi(doc, dalla_persona=False)
	return abbonamenti.get_subscription(name)


# ------------------------------------------------------------------ in words


def della_carta(doc, con_importi: bool = False) -> dict | None:
	"""The card of a subscription as its card shows it: whether it is charged, the
	card, the next charge (when and, asked, how much), the last that did not go
	through and the instalment to pay; or how the charges were stopped."""
	if not doc.get("stripe_payment_method") and not doc.get("card_charges_stopped_on"):
		return None
	from crm.scheduling import abbonamenti

	oggi = getdate()
	aperte = [
		r
		for r in sorted(doc.instalments, key=lambda r: getdate(r.due_on))
		if not abbonamenti._fattura_viva(r.invoice)
	]
	fallita = next((r for r in aperte if r.charge_problem and getdate(r.due_on) <= oggi), None)
	prossima = next((r for r in aperte if not (fallita and r.name == fallita.name)), None)
	quando = None
	if prossima:
		quando = getdate(prossima.due_on)
	if fallita and not R.esauriti(fallita.charge_attempts):
		quando = R.prossimo(getdate(fallita.due_on), cint(fallita.charge_attempts))
	importo = None
	if con_importi and attivo(doc) and (prossima or fallita):
		try:
			importo = lordo_della_rata(doc, fallita or prossima)
		except Exception:
			frappe.clear_last_message()
	return {
		"active": attivo(doc),
		"brand": doc.card_brand or "",
		"last4": doc.card_last4 or "",
		"expiry": doc.card_expiry or "",
		"expired": R.scaduta(doc.card_expiry, oggi),
		"next_on": str(quando) if quando and attivo(doc) else None,
		"next_amount": pagamenti._soldi(importo, doc.currency) if importo else None,
		"failed": {
			"on": str(fallita.last_charge_on) if fallita.last_charge_on else None,
			"reason": _(fallita.charge_problem),
			"instalment": fallita.name,
			"retries": not R.esauriti(fallita.charge_attempts),
		}
		if fallita
		else None,
		"stopped_on": str(getdate(doc.card_charges_stopped_on))
		if doc.get("card_charges_stopped_on")
		else None,
		"stopped_by": doc.get("card_charges_stopped_by") or "",
		# a subscription of a fixed length: its instalments stay owed when the charges stop
		"fixed_term": True,
	}
