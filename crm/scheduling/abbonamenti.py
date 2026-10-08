# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions on the site (design.md, "Cosa si aggiunge al CRM": "gli
abbonamenti"). The rules are `abbonamenti_regole`; here, the appointments, the
invoices and the days.

- **Types** (`CRM Subscription Type`, Settings > Agenda > Services > Subscriptions,
  `agenda.configura`): months, price, at once or by the month, the services it
  comprises and its entries, suspensions, the reminder, renewing by itself, the
  fiscal card of its invoices.
- **Sold and followed** from the person's page by the desk, the manager, and the
  practitioner for their people (`agenda.abbonamenti`). The type's terms are copied
  on the subscription: a type changed later changes nothing sold.
- **Each person's place uses an entry by itself**: a person booked into a comprised
  service, within their subscription's days and not suspended, while an entry is
  left in its week or month - after a cycle, which comes first. In a class each
  person uses their own (the participant's ``subscription``), and the ones without
  one pay. It costs them nothing: the subscription is paid on its own. A new
  subscription takes the places already booked in its days; the appointment's
  panel moves one in or out by hand.
- **Paid at once or by the month**: on each instalment's day an invoice of the
  subscription opens by itself (issued, where the type says so); without a fiscal
  card the instalments are only a schedule.
- **Before the end** the person gets a reminder; a type that renews by itself
  starts the next subscription the day after the last one, and the desk renews by
  hand. **Suspended** from a day to a day where the type allows it, the end moves by
  those days.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import add_days, cint, escape_html, flt, formatdate, get_fullname, getdate, now_datetime

from crm.permissions import livelli
from crm.scheduling import abbonamenti_regole as R
from crm.scheduling import pricing

ABBONAMENTO = "CRM Subscription"
TIPO = "CRM Subscription Type"
APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"

#: How long after its end the daily round still looks at a subscription.
GIORNI_DOPO_LA_FINE = 31

#: The terms a subscription copies from its type when it is sold.
CONDIZIONI = (
	"months",
	"payment",
	"price",
	"currency",
	"billable_service",
	"issue_invoices",
	"entries",
	"entries_count",
	"missed_count",
	"can_suspend",
	"max_suspension_days",
	"remind_days",
	"auto_renew",
)


# ------------------------------------------------------------------ the days


def _sospensioni(doc) -> list[tuple[datetime.date, datetime.date]]:
	return [
		(getdate(riga.from_date), getdate(riga.to_date))
		for riga in doc.get("suspensions") or []
		if riga.from_date and riga.to_date
	]


def ultimo(doc) -> datetime.date:
	"""The subscription's last day: its months, later by the days suspended."""
	return R.fine(getdate(doc.starts_on), R.entro(doc.months, R.MESI), _sospensioni(doc))


def stato(doc, oggi: datetime.date | None = None) -> str:
	return R.stato(
		oggi or getdate(),
		getdate(doc.ends_on) if doc.ends_on else ultimo(doc),
		_sospensioni(doc),
		doc.status == R.CHIUSO,
	)


def prepara(doc) -> None:
	"""`validate` of a subscription: its last day and how it stands today."""
	doc.ends_on = ultimo(doc)
	if doc.status != R.CHIUSO:
		doc.status = stato(doc)


def _servizi(doc) -> set[str]:
	return {riga.service for riga in doc.get("services") or [] if riga.service}


# ------------------------------------------------------------------ the entries


def _righe(appuntamento, anche_annullati: bool = False) -> list:
	"""The places of the appointment's people, the ones let go too when asked."""
	return [
		riga
		for riga in appuntamento.get("participants") or []
		if riga.party_type == "CRM Lead" and riga.party and (anche_annullati or riga.status != "Cancelled")
	]


def _persone(appuntamento, anche_annullati: bool = False) -> list[str]:
	return [riga.party for riga in _righe(appuntamento, anche_annullati)]


def ingressi(nome: str, dal: datetime.date | None = None, al: datetime.date | None = None) -> list[dict]:
	"""The appointments of a subscription in the order they come, each with what it
	is for it: done, missed, booked, cancelled - from its person's place."""
	stati: dict[str, str] = {}
	for posto in frappe.get_all(
		PARTECIPANTE,
		filters={"parenttype": APPUNTAMENTO, "subscription": nome},
		fields=["parent", "status"],
		order_by="idx asc",
	):
		stati.setdefault(posto.parent, posto.status)
	if not stati:
		return []
	filtri = [["name", "in", list(stati)]]
	if dal:
		filtri.append(["starts_on", ">=", datetime.datetime.combine(dal, datetime.time.min)])
	if al:
		filtri.append(["starts_on", "<=", datetime.datetime.combine(al, datetime.time.max)])
	righe = frappe.get_all(
		APPUNTAMENTO,
		filters=filtri,
		fields=["name", "starts_on", "ends_on", "status", "service"],
		order_by="starts_on asc",
	)
	return [{**riga, "state": R.ingresso(riga.status, stati.get(riga.name))} for riga in righe]


def coperti(appuntamenti: list[str]) -> set[str]:
	"""Of ``appuntamenti``, the ones where everybody uses an entry of their
	subscription: nobody pays for them, the instalments do."""
	con, senza = set(), set()
	for posto in frappe.get_all(
		PARTECIPANTE,
		filters={"parenttype": APPUNTAMENTO, "parent": ("in", list(appuntamenti) or [""])},
		fields=["parent", "status", "subscription"],
	):
		if posto.subscription:
			con.add(posto.parent)
		elif posto.status != "Cancelled":
			senza.add(posto.parent)
	return con - senza


def usati_nel_periodo(doc, giorno: datetime.date, escluso: str | None = None) -> int | None:
	"""The entries used in ``giorno``'s week or month; ``None`` when they are not
	counted."""
	periodo = R.periodo(giorno, getdate(doc.starts_on), doc.entries)
	if not periodo:
		return None
	elenco = [s for s in ingressi(doc.name, *periodo) if s["name"] != escluso]
	return R.usati([s["state"] for s in elenco], bool(cint(doc.missed_count)))


def entra(doc, giorno: datetime.date, escluso: str | None = None) -> bool:
	"""Whether an appointment on ``giorno`` uses an entry of ``doc``."""
	return R.si_aggiunge(
		doc.status == R.CHIUSO,
		giorno,
		getdate(doc.starts_on),
		getdate(doc.ends_on) if doc.ends_on else ultimo(doc),
		_sospensioni(doc),
		usati_nel_periodo(doc, giorno, escluso) or 0,
		cint(doc.entries_count),
		doc.entries,
	)


def _per(persona: str, servizio: str, giorno: datetime.date) -> str | None:
	"""The subscription ``persona`` uses for a new place in ``servizio`` on ``giorno``:
	the oldest of theirs that comprises the service and has an entry left that day."""
	for nome in frappe.get_all(
		ABBONAMENTO,
		filters={
			"lead": persona,
			"status": ("!=", R.CHIUSO),
			"starts_on": ("<=", giorno),
			"ends_on": (">=", giorno),
		},
		pluck="name",
		order_by="creation asc",
	):
		doc = frappe.get_doc(ABBONAMENTO, nome)
		if servizio in _servizi(doc) and entra(doc, giorno):
			return nome
	return None


def _ci_sta(appuntamento, riga, nome: str) -> bool:
	"""Whether a person's place still belongs to their subscription: it comprises the
	service, is theirs and lasts that day, not suspended. Closed, it keeps what it
	had: only nothing new joins it."""
	if not frappe.db.exists(ABBONAMENTO, nome):
		return False
	doc = frappe.get_doc(ABBONAMENTO, nome)
	giorno = getdate(appuntamento.starts_on) if appuntamento.starts_on else None
	return bool(
		appuntamento.service in _servizi(doc)
		and riga.party_type == "CRM Lead"
		and riga.party == doc.lead
		and giorno
		and getdate(doc.starts_on) <= giorno <= getdate(doc.ends_on or ultimo(doc))
		and not R.sospesa(giorno, _sospensioni(doc))
	)


def _lascia(riga) -> None:
	"""A person's place out of their subscription: the price list prices it again."""
	riga.subscription = None
	riga.amount = 0


def aggancia(appuntamento) -> None:
	"""`validate` of an appointment, after its cycle and before its price: each person
	newly booked into a comprised service uses an entry of their own subscription; a
	place in a cycle, or whose service, person or day left the subscription, leaves
	it. One brought over from the previous software uses no entry."""
	if appuntamento.flags.get("importato"):
		return
	ciclo = appuntamento.get("session_cycle")
	giorno = getdate(appuntamento.starts_on) if appuntamento.starts_on else None
	for riga in _righe(appuntamento, anche_annullati=True):
		nome = riga.get("subscription")
		if nome:
			if ciclo or not _ci_sta(appuntamento, riga, nome):
				_lascia(riga)
			continue
		if (
			ciclo
			or riga.status == "Cancelled"
			or appuntamento.status == "Cancelled"
			or not appuntamento.service
			or not giorno
			# only a new booking takes an entry by itself: a place booked before
			# moves in by hand
			or not (appuntamento.is_new() or riga.is_new())
		):
			continue
		riga.subscription = _per(riga.party, appuntamento.service, giorno)


def prezzo(appuntamento) -> None:
	"""`validate` of an appointment, after the price list: an entry of a subscription
	costs its person nothing - the subscription is paid on its own."""
	attivi = [r for r in appuntamento.get("participants") or [] if r.status != "Cancelled"]
	coperti = [r for r in attivi if r.party_type == "CRM Lead" and r.get("subscription")]
	if not coperti:
		# whoever had one let their place go: the others pay as before
		return
	for r in coperti:
		r.amount = 0
	if cint(appuntamento.per_participant):
		appuntamento.total_amount = sum(flt(r.amount) for r in attivi)
	elif len(attivi) <= 1:
		appuntamento.unit_price = appuntamento.total_amount = 0
	else:
		# one price for a group: who has a subscription does not set it
		return
	if len(coperti) < len(attivi):
		appuntamento.price_source = (
			_("One of the {0} people uses their subscription").format(len(attivi))
			if len(coperti) == 1
			else _("{0} of the {1} people use their subscription").format(len(coperti), len(attivi))
		)
		return
	tipi = {frappe.db.get_value(ABBONAMENTO, r.subscription, "subscription_type") for r in coperti}
	appuntamento.price_source = (
		_("Comprised in the subscription {0}").format(tipi.pop())
		if len(tipi) == 1
		else _("Comprised in their subscriptions")
	)


def _metti(nome: str, persona: str, abbonamento: str | None) -> None:
	"""A person's place into a subscription or out of it without saving the
	appointment again: only the subscription changes, and the price with it."""
	from crm.scheduling import cicli

	doc = frappe.get_doc(APPUNTAMENTO, nome)
	riga = next((r for r in _righe(doc, anche_annullati=True) if r.party == persona), None)
	if not riga:
		return
	if riga.subscription and riga.subscription != abbonamento:
		_lascia(riga)
	riga.subscription = abbonamento
	pricing.apply_to(doc)
	cicli.prezzo(doc)
	prezzo(doc)
	frappe.db.set_value(
		APPUNTAMENTO,
		nome,
		{
			"unit_price": doc.unit_price,
			"total_amount": doc.total_amount,
			"currency": doc.currency,
			"per_participant": doc.per_participant,
			"price_source": doc.price_source,
		},
		update_modified=False,
	)
	for r in doc.participants:
		frappe.db.set_value(
			PARTECIPANTE,
			r.name,
			{"amount": r.amount, "subscription": r.get("subscription")},
			update_modified=False,
		)


def raccogli(doc) -> int:
	"""A new subscription takes its person's places in its services already booked in
	its days - not in a cycle nor in another subscription - in the order they come,
	while their week or month has an entry left."""
	prenotati = frappe.get_all(
		PARTECIPANTE,
		filters={
			"parenttype": APPUNTAMENTO,
			"party_type": "CRM Lead",
			"party": doc.lead,
			"status": ("!=", "Cancelled"),
			"subscription": ("is", "not set"),
		},
		pluck="parent",
	)
	servizi = _servizi(doc)
	if not prenotati or not servizi:
		return 0
	presi = 0
	for riga in frappe.get_all(
		APPUNTAMENTO,
		filters=[
			["name", "in", list(set(prenotati))],
			["service", "in", list(servizi)],
			["status", "!=", "Cancelled"],
			["session_cycle", "is", "not set"],
			["starts_on", ">=", datetime.datetime.combine(getdate(doc.starts_on), datetime.time.min)],
			["starts_on", "<=", datetime.datetime.combine(getdate(doc.ends_on), datetime.time.max)],
		],
		fields=["name", "starts_on"],
		order_by="starts_on asc",
	):
		if entra(doc, getdate(riga.starts_on)):
			_metti(riga.name, doc.lead, doc.name)
			presi += 1
	return presi


def _rivedi(doc) -> None:
	"""After a suspension or the days changed: the places now out of its days leave
	it."""
	ultimo_giorno = getdate(doc.ends_on)
	sospensioni = _sospensioni(doc)
	for s in ingressi(doc.name):
		giorno = getdate(s["starts_on"])
		if giorno < getdate(doc.starts_on) or giorno > ultimo_giorno or R.sospesa(giorno, sospensioni):
			_metti(s["name"], doc.lead, None)


# ------------------------------------------------------------------ the instalments


def piano(doc) -> None:
	"""The instalments of a subscription just sold: one, or one a month."""
	doc.set("instalments", [])
	for giorno, importo in R.rate(
		getdate(doc.starts_on), R.entro(doc.months, R.MESI), flt(doc.price), doc.payment
	):
		doc.append("instalments", {"due_on": giorno, "amount": importo, "currency": doc.currency})


def _ripianifica(doc) -> None:
	"""The price or the payment changed: the instalments not invoiced yet follow;
	an invoiced one stays as it was."""
	fatturate = [r for r in doc.instalments if _fattura_viva(r.invoice)]
	gia = sum(flt(r.amount) for r in fatturate)
	da_fare = [
		(giorno, importo)
		for giorno, importo in R.rate(
			getdate(doc.starts_on), R.entro(doc.months, R.MESI), flt(doc.price), doc.payment
		)
		if giorno not in {getdate(r.due_on) for r in fatturate}
	]
	resto = round(flt(doc.price) - gia, 2)
	if da_fare:
		quota = round(resto / len(da_fare), 2)
		da_fare = [(giorno, quota) for giorno, _importo in da_fare]
		da_fare[-1] = (da_fare[-1][0], round(resto - quota * (len(da_fare) - 1), 2))
	doc.set("instalments", [r.as_dict() for r in fatturate])
	for giorno, importo in da_fare:
		doc.append("instalments", {"due_on": giorno, "amount": importo, "currency": doc.currency})


def _fattura_viva(nome: str | None) -> bool:
	return bool(nome) and frappe.db.get_value("CRM Invoice", nome, "docstatus") in (0, 1)


def fattura(doc, riga, emetti: bool = False) -> str:
	"""An instalment's invoice: a draft of the subscription's, issued when asked to
	and it can be. Returns the invoice."""
	from crm.invoicing import api as fatture

	if _fattura_viva(riga.invoice):
		return riga.invoice
	nome = fatture.issue_from_subscription(doc.name, riga.name)
	riga.db_set({"invoice": nome, "problem": None}, update_modified=False)
	if emetti:
		bozza = frappe.get_doc("CRM Invoice", nome)
		frappe.db.savepoint("crm_rata_emessa")
		try:
			bozza.submit()
		except Exception as errore:
			# the draft stays: what stopped it is said on the instalment
			frappe.db.rollback(save_point="crm_rata_emessa")
			frappe.clear_last_message()
			riga.db_set("problem", _("Left as a draft: {0}").format(str(errore)[:400]), update_modified=False)
	return nome


# ------------------------------------------------------------------ the days go by


def ogni_giorno() -> None:
	"""Daily: how each subscription stands today; the instalments due; the reminders
	of the end; the renewals. One that fails leaves the others alone, and the
	scheduler commits what was done."""
	oggi = getdate()
	nomi = frappe.get_all(ABBONAMENTO, filters={"status": ("in", [R.ATTIVO, R.SOSPESO])}, pluck="name")
	# the ones just ended: their renewal, their last instalments
	nomi += frappe.get_all(
		ABBONAMENTO,
		filters={"status": R.SCADUTO, "ends_on": (">=", add_days(oggi, -GIORNI_DOPO_LA_FINE))},
		pluck="name",
	)
	for nome in nomi:
		frappe.db.savepoint("crm_abbonamento_del_giorno")
		try:
			_il_giorno(frappe.get_doc(ABBONAMENTO, nome), oggi)
		except Exception:
			frappe.db.rollback(save_point="crm_abbonamento_del_giorno")
			frappe.clear_last_message()
			frappe.log_error(
				title="Subscription: the day's work failed",
				reference_doctype=ABBONAMENTO,
				reference_name=nome,
			)


def _il_giorno(doc, oggi: datetime.date) -> None:
	nuovo = stato(doc, oggi)
	if nuovo != doc.status:
		doc.db_set("status", nuovo, update_modified=False)
	if doc.billable_service:
		for riga in doc.instalments:
			if getdate(riga.due_on) <= oggi and not _fattura_viva(riga.invoice):
				# an invoice that cannot open leaves nothing behind, and says why
				frappe.db.savepoint("crm_rata_del_giorno")
				try:
					fattura(doc, riga, emetti=bool(cint(doc.issue_invoices)))
				except Exception as errore:
					frappe.db.rollback(save_point="crm_rata_del_giorno")
					frappe.clear_last_message()
					riga.db_set("problem", str(errore)[:400], update_modified=False)
	if (
		nuovo in (R.ATTIVO, R.SOSPESO)
		and not doc.reminded_on
		and not doc.renewed_by
		and R.da_ricordare(oggi, getdate(doc.ends_on), R.entro(doc.remind_days, R.PROMEMORIA))
	):
		_ricorda(doc)
	if nuovo == R.SCADUTO and cint(doc.auto_renew) and not doc.renewed_by:
		tipo = frappe.db.get_value(TIPO, doc.subscription_type, ["enabled", "auto_renew"], as_dict=True)
		if tipo and cint(tipo.enabled) and cint(tipo.auto_renew):
			rinnova(doc)


def _ricorda(doc) -> None:
	"""The reminder of the end, to the person's email."""
	from crm.moduli.richieste import nome_del_centro
	from crm.utils import stored_value

	email = stored_value("CRM Lead", doc.lead, "email")
	doc.db_set("reminded_on", getdate(), update_modified=False)
	if not email:
		return
	esc = escape_html
	nome = frappe.db.get_value("CRM Lead", doc.lead, "first_name") or ""
	quando = formatdate(doc.ends_on, "d MMMM yyyy")
	righe = [
		f"<p>{esc(_('Hi {0},').format(nome))}</p>" if nome else "",
		f"<p>{esc(_('your subscription {0} at {1} ends soon. Last day: {2}.').format(doc.subscription_type, nome_del_centro(), quando))}</p>",
		f"<p>{esc(_('It renews by itself the day after.') if cint(doc.auto_renew) else _('To go on, renew it at the desk or answer this email.'))}</p>",
	]
	frappe.sendmail(
		recipients=[email],
		subject=_("Your subscription ends soon: {0}").format(quando),
		header=_("Your subscription ends soon"),
		with_container=True,
		message="".join(righe),
		reference_doctype=ABBONAMENTO,
		reference_name=doc.name,
	)


def nuovo(lead: str, tipo: str, dal, practitioner: str | None = None, note: str | None = None, **condizioni):
	"""A subscription of ``tipo`` sold to ``lead`` from ``dal``: the type's terms,
	maybe with another price or payment; its instalments; the appointments already
	booked in its days."""
	t = frappe.get_doc(TIPO, tipo)
	if not cint(t.enabled):
		frappe.throw(_("This type of subscription is not sold any more"))
	doc = frappe.new_doc(ABBONAMENTO)
	doc.lead = lead
	doc.subscription_type = tipo
	doc.starts_on = getdate(dal) if dal else getdate()
	for campo in CONDIZIONI:
		doc.set(campo, t.get(campo))
	for campo in ("price", "payment"):
		if condizioni.get(campo) not in (None, ""):
			doc.set(campo, condizioni[campo])
	doc.set("services", [{"service": r.service} for r in t.services])
	doc.practitioner = practitioner or None
	doc.notes = (note or "").strip() or None
	doc.status = R.ATTIVO
	prepara(doc)
	piano(doc)
	doc.flags.ignore_permissions = True
	doc.insert()
	raccogli(doc)
	return doc


def rinnova(doc):
	"""The next subscription, from the day after the last one, at the type's price
	of today."""
	if doc.renewed_by:
		frappe.throw(_("This subscription is renewed already: {0}").format(doc.renewed_by))
	dopo = nuovo(doc.lead, doc.subscription_type, R.rinnovo_da(getdate(doc.ends_on)), doc.practitioner)
	dopo.db_set("renewal_of", doc.name, update_modified=False)
	doc.db_set("renewed_by", dopo.name, update_modified=False)
	return dopo


# ------------------------------------------------------------------ who


def _la_persona(lead: str) -> None:
	if not (livelli.puo("agenda.vedi") or livelli.puo("agenda.abbonamenti")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _abbonamento(nome: str):
	doc = frappe.get_doc(ABBONAMENTO, nome)
	_la_persona(doc.lead)
	doc.check_permission("read")
	return doc


def _gestisce() -> None:
	livelli.verifica("agenda.abbonamenti")


# ------------------------------------------------------------------ reading


def riga(doc, oggi: datetime.date | None = None) -> dict:
	oggi = oggi or getdate()
	periodo = R.periodo(oggi, getdate(doc.starts_on), doc.entries)
	usati = usati_nel_periodo(doc, oggi) if periodo and getdate(doc.starts_on) <= oggi else None
	sospesa_fino = next((a for da, a in _sospensioni(doc) if da <= oggi <= a), None)
	return {
		"name": doc.name,
		"lead": doc.lead,
		"lead_name": doc.lead_name,
		"subscription_type": doc.subscription_type,
		"starts_on": str(doc.starts_on),
		"ends_on": str(doc.ends_on),
		"status": stato(doc, oggi),
		"months": cint(doc.months),
		"price": flt(doc.price) or None,
		"currency": doc.currency,
		"payment": doc.payment,
		"services": sorted(_servizi(doc)),
		"entries": doc.entries,
		"entries_count": cint(doc.entries_count),
		"period": [str(periodo[0]), str(periodo[1])] if periodo else None,
		"used": usati,
		"suspended_until": str(sospesa_fino) if sospesa_fino else None,
		"can_suspend": cint(doc.can_suspend),
		"auto_renew": cint(doc.auto_renew),
		"renewal_of": doc.renewal_of,
		"renewed_by": doc.renewed_by,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner) if doc.practitioner else None,
		"notes": doc.notes,
	}


def _potere() -> dict:
	return {"can_manage": livelli.puo("agenda.abbonamenti"), "can_invoice": livelli.puo("fatture.emetti")}


def _tipi_in_vendita() -> list[dict]:
	return [
		{
			**t,
			"services": frappe.get_all(
				"CRM Subscription Service", filters={"parenttype": TIPO, "parent": t.name}, pluck="service"
			),
		}
		for t in frappe.get_all(
			TIPO,
			filters={"enabled": 1},
			fields=[
				"name",
				"months",
				"payment",
				"price",
				"currency",
				"entries",
				"entries_count",
				"auto_renew",
			],
			order_by="type_name asc",
		)
	]


@frappe.whitelist()
def get_subscriptions(lead: str) -> dict:
	"""The person's subscriptions, the ones going on first, and the types to sell."""
	_la_persona(lead)
	righe = [
		riga(frappe.get_doc(ABBONAMENTO, nome))
		for nome in frappe.get_list(
			ABBONAMENTO, filters={"lead": lead}, pluck="name", order_by="starts_on desc"
		)
	]
	ordine = {R.ATTIVO: 0, R.SOSPESO: 1, R.SCADUTO: 2, R.CHIUSO: 3}
	righe.sort(key=lambda r: ordine.get(r["status"], 9))
	potere = _potere()
	return {"subscriptions": righe, "types": _tipi_in_vendita() if potere["can_manage"] else [], **potere}


@frappe.whitelist()
def get_subscription(name: str) -> dict:
	"""A subscription with its entries, suspensions and instalments."""
	doc = _abbonamento(name)
	fatture = {
		r.invoice: frappe.db.get_value(
			"CRM Invoice", r.invoice, ["docstatus", "document_number"], as_dict=True
		)
		for r in doc.instalments
		if r.invoice
	}
	return {
		**riga(doc),
		"appointments": [
			{
				"name": s["name"],
				"starts_on": str(s["starts_on"]),
				"service": s["service"],
				"state": s["state"],
				"status": s["status"],
			}
			for s in ingressi(doc.name)
		],
		"suspensions": [
			{"name": r.name, "from_date": str(r.from_date), "to_date": str(r.to_date), "reason": r.reason}
			for r in doc.suspensions
		],
		"instalments": [
			{
				"name": r.name,
				"due_on": str(r.due_on),
				"amount": flt(r.amount),
				"invoice": r.invoice if _fattura_viva(r.invoice) else None,
				"issued": bool(fatture.get(r.invoice) and fatture[r.invoice].docstatus == 1),
				"number": fatture[r.invoice].document_number if fatture.get(r.invoice) else None,
				"problem": r.problem,
			}
			for r in doc.instalments
		],
		"billable": bool(doc.billable_service),
		**_potere(),
	}


def della_persona(persona: str) -> list[dict]:
	"""For the person's own area: the subscriptions going on, in the words they read
	- no price, no notes, no invoices."""
	fatto = []
	for nome in frappe.get_all(
		ABBONAMENTO,
		filters={"lead": persona, "status": ("in", [R.ATTIVO, R.SOSPESO])},
		pluck="name",
		order_by="starts_on asc",
	):
		dati = riga(frappe.get_doc(ABBONAMENTO, nome))
		fatto.append(
			{
				"name": dati["name"],
				"type": dati["subscription_type"],
				"description": frappe.db.get_value(TIPO, dati["subscription_type"], "description"),
				"starts_on": dati["starts_on"],
				"ends_on": dati["ends_on"],
				"status": dati["status"],
				"entries": dati["entries"],
				"entries_count": dati["entries_count"],
				"period": dati["period"],
				"used": dati["used"],
				"suspended_until": dati["suspended_until"],
				"auto_renew": dati["auto_renew"],
			}
		)
	return fatto


def del_appuntamento(appuntamento) -> dict | None:
	"""For the appointment's panel: each person's place with the subscription whose
	entry it uses, and the ones of theirs that comprise the service and could."""
	if not livelli.puo("agenda.vedi") or not appuntamento.service or not appuntamento.starts_on:
		return None
	righe = _righe(appuntamento, anche_annullati=True)
	if not righe:
		return None
	giorno = getdate(appuntamento.starts_on)
	persone = []
	for riga in righe:
		opzioni = []
		for nome in frappe.get_list(
			ABBONAMENTO,
			filters={
				"lead": riga.party,
				"status": ("!=", R.CHIUSO),
				"starts_on": ("<=", giorno),
				"ends_on": (">=", giorno),
			},
			pluck="name",
			order_by="creation asc",
		):
			doc = frappe.get_doc(ABBONAMENTO, nome)
			if appuntamento.service not in _servizi(doc):
				continue
			suo = nome == riga.subscription
			if not suo and (riga.status == "Cancelled" or not entra(doc, giorno, escluso=appuntamento.name)):
				continue
			opzioni.append(
				{
					"name": nome,
					"type": doc.subscription_type,
					"entries": doc.entries,
					"entries_count": cint(doc.entries_count),
					"used": usati_nel_periodo(doc, giorno),
				}
			)
		if opzioni or riga.subscription:
			persone.append(
				{
					"party": riga.party,
					"participant_name": riga.participant_name or riga.party,
					"subscription": riga.subscription,
					"options": opzioni,
				}
			)
	if not persone:
		return None
	return {"people": persone, "can_manage": livelli.puo("agenda.abbonamenti")}


# ------------------------------------------------------------------ writing


def _dati(data) -> dict:
	return frappe.parse_json(data) if isinstance(data, str) else (data or {})


@frappe.whitelist(methods=["POST"])
def sell_subscription(lead: str, data: dict | str) -> dict:
	"""A subscription sold: its type, from when, maybe another price or payment."""
	_gestisce()
	_la_persona(lead)
	frappe.has_permission(ABBONAMENTO, "create", throw=True)
	dati = _dati(data)
	if not dati.get("subscription_type"):
		frappe.throw(_("Choose the type of subscription"))
	doc = nuovo(
		lead,
		dati["subscription_type"],
		dati.get("starts_on"),
		dati.get("practitioner"),
		dati.get("notes"),
		price=dati.get("price"),
		payment=dati.get("payment"),
	)
	return get_subscription(doc.name)


@frappe.whitelist(methods=["POST"])
def save_subscription(name: str, data: dict | str) -> dict:
	"""Put right: who follows it, the notes; the price and the payment while nothing
	is invoiced of what changes; the first day while no entry is used."""
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	dati = _dati(data)
	doc.practitioner = dati.get("practitioner") or None
	doc.notes = (dati.get("notes") or "").strip() or None
	prima = (flt(doc.price), doc.payment, str(doc.starts_on))
	if dati.get("starts_on") and str(getdate(dati["starts_on"])) != str(doc.starts_on):
		if any(s["state"] in (R.FATTA, R.PERSA) for s in ingressi(doc.name)) or any(
			_fattura_viva(r.invoice) for r in doc.instalments
		):
			frappe.throw(_("The first day does not change once entries are used or instalments invoiced"))
		doc.starts_on = getdate(dati["starts_on"])
	if dati.get("price") not in (None, ""):
		doc.price = flt(dati["price"])
	if dati.get("payment") in R.PAGAMENTI:
		doc.payment = dati["payment"]
	prepara(doc)
	if prima != (flt(doc.price), doc.payment, str(doc.starts_on)):
		_ripianifica(doc)
	doc.save()
	_rivedi(doc)
	return get_subscription(doc.name)


def _perche(problema: str) -> str:
	"""Why a suspension cannot be, in the user's words."""
	return {
		"Both days are needed": _("Both days are needed"),
		"The suspension ends before it starts": _("The suspension ends before it starts"),
		"The suspension starts outside the subscription": _("The suspension starts outside the subscription"),
		"It overlaps another suspension": _("It overlaps another suspension"),
		"More days than the type allows": _("More days than the type allows"),
	}.get(problema, problema)


@frappe.whitelist(methods=["POST"])
def suspend_subscription(name: str, from_date: str, to_date: str, reason: str | None = None) -> dict:
	"""Suspended from a day to a day, where its type allows it: the end moves by
	those days, and the appointments booked in them leave it."""
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	if not cint(doc.can_suspend):
		frappe.throw(_("This subscription cannot be suspended"))
	if doc.status == R.CHIUSO:
		frappe.throw(_("A closed subscription is not suspended"))
	problema = R.problema_della_sospensione(
		getdate(from_date) if from_date else None,
		getdate(to_date) if to_date else None,
		getdate(doc.starts_on),
		getdate(doc.ends_on),
		_sospensioni(doc),
		cint(doc.max_suspension_days),
	)
	if problema:
		frappe.throw(_perche(problema))
	doc.append(
		"suspensions", {"from_date": from_date, "to_date": to_date, "reason": (reason or "").strip() or None}
	)
	prepara(doc)
	doc.save()
	_rivedi(doc)
	return get_subscription(doc.name)


@frappe.whitelist(methods=["POST"])
def remove_suspension(name: str, row: str) -> dict:
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	doc.set("suspensions", [r for r in doc.suspensions if r.name != row])
	prepara(doc)
	doc.save()
	return get_subscription(doc.name)


@frappe.whitelist(methods=["POST"])
def close_subscription(name: str) -> dict:
	"""Closed by hand: what was booked keeps its entry, nothing new uses one."""
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	doc.status = R.CHIUSO
	doc.closed_on = now_datetime()
	doc.save()
	return get_subscription(doc.name)


@frappe.whitelist(methods=["POST"])
def reopen_subscription(name: str) -> dict:
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	if doc.status == R.CHIUSO:
		doc.status = R.ATTIVO
		doc.closed_on = None
		prepara(doc)
		doc.save()
	return get_subscription(doc.name)


@frappe.whitelist(methods=["POST"])
def renew_subscription(name: str) -> dict:
	"""The next one, from the day after the last: renewed at the desk."""
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	frappe.has_permission(ABBONAMENTO, "create", throw=True)
	return get_subscription(rinnova(doc).name)


@frappe.whitelist(methods=["POST"])
def delete_subscription(name: str) -> None:
	"""Sold by mistake: gone while no entry is used and no instalment invoiced."""
	_gestisce()
	doc = _abbonamento(name)
	doc.check_permission("write")
	if any(_fattura_viva(r.invoice) for r in doc.instalments):
		frappe.throw(_("An instalment is invoiced: close it instead"))
	if any(s["state"] in (R.FATTA, R.PERSA) for s in ingressi(doc.name)):
		frappe.throw(_("Entries are used already: close it instead"))
	# its appointments leave it before it goes (`CRMSubscription.on_trash`)
	frappe.delete_doc(ABBONAMENTO, doc.name, ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def invoice_instalment(name: str, row: str) -> dict:
	"""An instalment invoiced now, by hand: its draft opens."""
	_gestisce()
	doc = _abbonamento(name)
	riga_rata = next((r for r in doc.instalments if r.name == row), None)
	if not riga_rata:
		frappe.throw(_("No such instalment"))
	if not doc.billable_service:
		frappe.throw(_("This subscription has no fiscal card: its instalments are not invoiced"))
	return {"invoice": fattura(doc, riga_rata), **get_subscription(doc.name)}


@frappe.whitelist(methods=["POST"])
def attach(appointment: str, subscription: str | None = None, party: str | None = None) -> dict:
	"""A person's place into one of their subscriptions, or out of it
	(``subscription`` empty), by hand. ``party`` is whose place: the subscription's
	person when one is given, else the only person booked."""
	_gestisce()
	appuntamento = frappe.get_doc(APPUNTAMENTO, appointment)
	appuntamento.check_permission("write")
	doc = _abbonamento(subscription) if subscription else None
	righe = _righe(appuntamento, anche_annullati=True)
	if not party:
		party = doc.lead if doc else (righe[0].party if len(righe) == 1 else None)
	riga = next((r for r in righe if r.party == party), None)
	if not riga:
		frappe.throw(_("This person is not booked in this appointment"))
	if doc and subscription != riga.subscription:
		if appuntamento.get("session_cycle"):
			frappe.throw(_("This appointment is a session of a cycle"))
		if appuntamento.service not in _servizi(doc) or doc.lead != riga.party or riga.status == "Cancelled":
			frappe.throw(_("The subscription does not comprise this service, or is of somebody else"))
		if not entra(doc, getdate(appuntamento.starts_on), escluso=appuntamento.name):
			frappe.throw(_("No entry is left that day"))
	_metti(appointment, riga.party, subscription or None)
	return del_appuntamento(frappe.get_doc(APPUNTAMENTO, appointment)) or {}


# ------------------------------------------------------------------ the types


def _tipo_da(data: dict, doc) -> None:
	doc.type_name = (data.get("type_name") or "").strip()
	doc.enabled = 1 if cint(data.get("enabled", 1)) else 0
	doc.description = (data.get("description") or "").strip() or None
	doc.months = R.entro(data.get("months"), R.MESI)
	doc.payment = data.get("payment") if data.get("payment") in R.PAGAMENTI else R.SUBITO
	doc.price = flt(data.get("price")) or 0
	doc.currency = data.get("currency") or doc.currency or frappe.db.get_default("currency") or "EUR"
	doc.billable_service = data.get("billable_service") or None
	doc.issue_invoices = 1 if cint(data.get("issue_invoices")) else 0
	doc.entries = data.get("entries") if data.get("entries") in R.INGRESSI else R.ILLIMITATI
	doc.entries_count = 0 if doc.entries == R.ILLIMITATI else max(cint(data.get("entries_count")), 1)
	doc.missed_count = 1 if cint(data.get("missed_count", 1)) else 0
	doc.can_suspend = 1 if cint(data.get("can_suspend")) else 0
	doc.max_suspension_days = max(cint(data.get("max_suspension_days")), 0) if doc.can_suspend else 0
	doc.remind_days = (
		R.entro(data.get("remind_days"), R.PROMEMORIA) if data.get("remind_days") not in (0, "0") else 0
	)
	doc.auto_renew = 1 if cint(data.get("auto_renew")) else 0
	doc.set("services", [{"service": s} for s in dict.fromkeys(data.get("services") or []) if s])
	if not doc.type_name:
		frappe.throw(_("Give the type a name"))
	if not doc.services:
		frappe.throw(_("Choose the services it comprises"))


def _tipo(doc) -> dict:
	return {
		**{campo: doc.get(campo) for campo in ("name", "type_name", "description", *CONDIZIONI)},
		"enabled": cint(doc.enabled),
		"services": [r.service for r in doc.services],
		"sold": frappe.db.count(ABBONAMENTO, {"subscription_type": doc.name}),
	}


@frappe.whitelist()
def get_types() -> list[dict]:
	livelli.verifica("agenda.configura")
	return [
		_tipo(frappe.get_doc(TIPO, nome))
		for nome in frappe.get_all(TIPO, pluck="name", order_by="type_name asc")
	]


@frappe.whitelist()
def get_fiscal_cards() -> list[dict]:
	"""The fiscal cards a type's invoices may say: the enabled ones."""
	livelli.verifica("agenda.configura")
	return [
		{"value": riga.name, "label": riga.service_name or riga.name}
		for riga in frappe.get_all(
			"CRM Billable Service",
			filters={"enabled": 1},
			fields=["name", "service_name"],
			order_by="service_name asc",
		)
	]


@frappe.whitelist(methods=["POST"])
def save_type(data: dict | str, name: str | None = None) -> dict:
	livelli.verifica("agenda.configura")
	dati = _dati(data)
	doc = frappe.get_doc(TIPO, name) if name else frappe.new_doc(TIPO)
	_tipo_da(dati, doc)
	if not name and frappe.db.exists(TIPO, doc.type_name):
		frappe.throw(_("A type called {0} exists already").format(doc.type_name))
	doc.save() if name else doc.insert()
	return _tipo(doc)


@frappe.whitelist(methods=["POST"])
def delete_type(name: str) -> None:
	"""A type nobody bought goes; one sold is switched off instead."""
	livelli.verifica("agenda.configura")
	if frappe.db.exists(ABBONAMENTO, {"subscription_type": name}):
		frappe.throw(_("This type is sold already: switch it off instead"))
	frappe.delete_doc(TIPO, name)
