# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The base's share of the demo: what every centre has, whatever its plan.

A centre of physiotherapy, osteopathy, nutrition and movement that opened three
months ago: its team and their shifts, the rooms and the services with their
prices, the people who came and keep coming with their cycles and quotes
(`crm.demo.simulazione`), the companies it has agreements with, and the day-to-day -
things to do, notes, calls.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import add_days, getdate

from crm.demo import abbonati, dati, registro, simulazione
from crm.demo.contesto import Contesto, indirizzo, nome_libero
from crm.demo.registro import Parte, registra_parte


def registra() -> None:
	registra_parte(
		Parte(
			"squadra",
			"The team",
			crea_squadra,
			descrizione="Six colleagues with their levels: a manager, the front desk, a physiotherapist, "
			"an osteopath, a dietitian and a kinesiologist, with their shifts and holidays.",
		)
	)
	registra_parte(
		Parte(
			"agenda",
			"Rooms and services",
			crea_agenda,
			dopo=("squadra",),
			descrizione="Four rooms and ten services with their prices, group classes and an "
			"agreement's price list.",
		)
	)
	registra_parte(
		Parte(
			"clienti",
			"People and appointments",
			simulazione.crea,
			dopo=("squadra", "agenda"),
			descrizione="Three months of the centre's life: a few hundred people, their requests, the "
			"appointments they came to and the ones booked, today's reception desk; the cycles of "
			"sessions and the quotes agreed at the first visit.",
		)
	)
	registra_parte(
		Parte(
			"aziende",
			"Companies and agreements",
			crea_aziende,
			dopo=("clienti",),
			descrizione="Five companies and the agreements being discussed with them.",
		)
	)
	registra_parte(
		Parte(
			"lavoro",
			"Tasks, notes and calls",
			crea_lavoro,
			dopo=("clienti", "aziende"),
			descrizione="Things to do for everybody (you too), notes on people, the calls of the "
			"last weeks with the ones to call back.",
		)
	)
	registra_parte(
		Parte(
			"abbonamenti",
			"Subscriptions",
			abbonati.crea,
			dopo=("clienti",),
			descrizione="Three kinds of subscription to the classes and the regulars who bought them: "
			"months renewed by themselves, a suspension, the reminders of the end.",
		)
	)


# -- the team ----------------------------------------------------------------------------


def crea_squadra(ctx: Contesto) -> None:
	from crm.permissions import utenti

	festivita = _festivita(ctx)
	for chiave, nome, cognome, livelli, qualifica, titolo, cellulare in dati.SQUADRA:
		ctx.avanza(f"{nome} {cognome}")
		email = indirizzo(nome, cognome)
		if frappe.db.exists("User", email):
			# a colleague of a demo taken away by hand, without the register: theirs
			email = indirizzo(nome, cognome, 2)
		utente = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": nome,
				"last_name": cognome,
				"mobile_no": cellulare,
				"user_type": "System User",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		utente.flags.no_welcome_mail = True
		utente.insert(ignore_permissions=True)
		utenti.assegna_livelli(utente.name, list(livelli))
		ctx.ricorda("User", utente.name, f"team.{chiave}")

		if qualifica and frappe.db.exists("CRM Professional Qualification", qualifica):
			frappe.get_doc(
				{
					"doctype": "CRM Service Provider",
					"provider_name": nome_libero("CRM Service Provider", f"{nome} {cognome}"),
					"qualification": qualifica,
					"user": utente.name,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)

		turni = dati.TURNI.get(chiave)
		if turni:
			frappe.get_doc(
				{
					"doctype": "CRM Staff Schedule",
					"user": utente.name,
					"enabled": 1,
					"bookable_online": 1,
					"public_title": titolo,
					"holiday_list": festivita,
					"availability": [
						{"workday": giorno, "start_time": inizio, "end_time": fine}
						for giorno, fasce in turni.items()
						for inizio, fine in fasce
					],
					"exceptions": _assenze(ctx, chiave),
				}
			).insert(ignore_permissions=True)
		ctx.retrodata("User", utente.name, ctx.giorno(-simulazione.GIORNI_INDIETRO - 20), "Administrator")


def _festivita(ctx: Contesto) -> str:
	"""The holidays of the months the demo covers."""
	dal = getdate(f"{ctx.giorno(-simulazione.GIORNI_INDIETRO - 30).year}-01-01")
	al = getdate(f"{ctx.giorno(simulazione.GIORNI_AVANTI + 30).year}-12-31")
	giorni = []
	for anno in range(dal.year, al.year + 1):
		for mese_giorno, descrizione in dati.FESTIVITA:
			giorni.append({"date": getdate(f"{anno}-{mese_giorno}"), "description": descrizione})
	doc = frappe.get_doc(
		{
			"doctype": "CRM Holiday List",
			"holiday_list_name": nome_libero("CRM Holiday List", "Festività del centro"),
			"from_date": dal,
			"to_date": al,
			"holidays": giorni,
		}
	).insert(ignore_permissions=True)
	ctx.ricorda("CRM Holiday List", doc.name, "agenda.festivita")
	return doc.name


def _assenze(ctx: Contesto, chiave: str) -> list[dict]:
	"""A colleague away for a day: the agenda shows it, and books around it."""
	if chiave == "elena":
		giorno = simulazione.prossimo(ctx.giorno(9), "Friday")
		return [{"date": giorno, "unavailable": 1, "reason": "Congresso di nutrizione sportiva"}]
	if chiave == "luca":
		giorno = simulazione.prossimo(ctx.giorno(-24), "Wednesday")
		return [{"date": giorno, "unavailable": 1, "reason": "Corso di aggiornamento"}]
	return []


# -- rooms and services --------------------------------------------------------------------


def crea_agenda(ctx: Contesto) -> None:
	from crm import lingue

	valuta = lingue.valuta()
	stanze = {}
	for chiave, nome, tipo, posti, colore, descrizione in dati.STANZE:
		doc = frappe.get_doc(
			{
				"doctype": "CRM Resource",
				"resource_name": nome_libero("CRM Resource", nome),
				"resource_type": tipo,
				"capacity": 1,
				"seats": posti,
				"color": colore,
				"description": descrizione,
				"currency": valuta,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		stanze[chiave] = doc.name
		ctx.ricorda("CRM Resource", doc.name, f"room.{chiave}")

	for (
		chiave,
		nome,
		categoria,
		minuti,
		prezzo,
		staff,
		stanza,
		massimo,
		a_persona,
		online,
		colore,
		descrizione,
	) in dati.SERVIZI:
		ctx.avanza(nome)
		doc = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": nome_libero("CRM Service", nome),
				"category": categoria,
				"enabled": 1,
				"color": colore,
				"description": descrizione,
				"duration": minuti,
				"default_price": prezzo,
				"price_per_participant": 1 if a_persona else 0,
				"currency": valuta,
				"min_participants": 1,
				"max_participants": massimo,
				"online_max_participants": 1,
				"bookable_online": 1 if online else 0,
				"staff_selection": "Any one",
				"staff": [
					{"user": ctx.squadra(persona), "bookable_online": 1 if online else 0}
					for persona in staff
					if ctx.squadra(persona)
				],
				# shared by colleagues in their own rooms: any room; else the service's
				"resources": [{"resource_type": "Room", "quantity": 1, "required": 1}]
				if len(staff) > 1
				else [{"resource": stanze[stanza], "quantity": 1, "required": 1}],
			}
		).insert(ignore_permissions=True)
		ctx.ricorda("CRM Service", doc.name, f"service.{chiave}")

	nome, prezzi = dati.CONVENZIONE
	listino = frappe.get_doc(
		{
			"doctype": "CRM Price List",
			"price_list_name": nome_libero("CRM Price List", nome),
			"enabled": 1,
			"is_default": 0,
			"currency": valuta,
			"description": "Prezzi riservati agli iscritti dell'assicurazione sanitaria Salute+.",
		}
	).insert(ignore_permissions=True)
	ctx.ricorda("CRM Price List", listino.name, "agenda.convenzione")
	for chiave, prezzo in prezzi.items():
		servizio = ctx.trova(f"service.{chiave}")
		if servizio:
			frappe.get_doc(
				{
					"doctype": "CRM Service Price",
					"price_list": listino.name,
					"service": servizio,
					"price": prezzo,
					"currency": valuta,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)


# -- companies and agreements ------------------------------------------------------------------


def crea_aziende(ctx: Contesto) -> None:
	from crm.clienti import pipeline as nuovi_clienti

	pipeline = _pipeline_per_gli_accordi(nuovi_clienti.quale())
	responsabile = ctx.squadra("manager")
	for (chiave, titolo, (tipo, passo), valore, giorni_fa, chiusura, perso), azienda in zip(
		dati.ACCORDI, dati.AZIENDE, strict=True
	):
		_chiave, nome_azienda, settore, dipendenti, (nome, cognome, ruolo, genere) = azienda
		ctx.avanza(nome_azienda)
		aperto = ctx.adesso - datetime.timedelta(days=giorni_fa, hours=ctx.rng.randint(1, 6))
		organizzazione = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": nome_libero("CRM Organization", nome_azienda),
				"industry": settore if frappe.db.exists("CRM Industry", settore) else None,
				"no_of_employees": dipendenti,
			}
		).insert(ignore_permissions=True)
		ctx.retrodata("CRM Organization", organizzazione.name, aperto, responsabile)
		ctx.ricorda("CRM Organization", organizzazione.name, f"company.{chiave}")

		with ctx.come(responsabile):
			persona = frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": nome,
					"last_name": cognome,
					"gender": genere,
					"email": indirizzo(nome, cognome),
					"mobile_no": simulazione.numero(ctx),
					"job_title": ruolo,
					"organization": organizzazione.name,
					"source": "Reference",
					"lead_owner": responsabile,
				}
			).insert(ignore_permissions=True)
		simulazione.retrodata_persona(ctx, persona, aperto, responsabile)
		ctx.ricorda("CRM Lead", persona.name, f"company_contact.{chiave}")

		stadio = _stadio(pipeline, tipo, passo)
		if not stadio:
			continue
		with ctx.come(responsabile):
			trattativa = frappe.get_doc(
				{
					"doctype": "CRM Deal",
					"status": stadio,
					"lead": persona.name,
					"organization": organizzazione.name,
					"deal_owner": responsabile,
					"source": "Reference",
					"expected_deal_value": valore,
					"expected_closure_date": add_days(ctx.oggi, chiusura)
					if tipo not in ("Won", "Lost")
					else None,
					"deal_value": valore if tipo == "Won" else None,
					"probability": frappe.db.get_value("CRM Deal Status", stadio, "probability"),
					"next_step": titolo,
					"lost_reason": perso
					if tipo == "Lost" and frappe.db.exists("CRM Lost Reason", perso)
					else None,
					"lost_notes": "Budget già impegnato per quest'anno, da ricontattare a gennaio."
					if tipo == "Lost"
					else None,
					"contacts": [{"contact": persona.contact, "is_primary": 1}] if persona.contact else [],
				}
			)
			trattativa.flags.from_inquiry = True
			if tipo == "Lost" and not trattativa.lost_reason:
				trattativa.lost_reason = "Other"
			trattativa.insert(ignore_permissions=True)
		frappe.db.set_value("CRM Lead", persona.name, "converted", 1, update_modified=False)
		chiusa = add_days(ctx.oggi, chiusura) if tipo in ("Won", "Lost") else None
		ctx.retrodata("CRM Deal", trattativa.name, aperto + datetime.timedelta(minutes=20), responsabile)
		if chiusa:
			frappe.db.set_value(
				"CRM Deal",
				trattativa.name,
				{"closed_date": chiusa, "modified": chiusa},
				update_modified=False,
			)
		ctx.ricorda("CRM Deal", trattativa.name, f"agreement.{chiave}")

	# the people of the company the centre has an agreement with come through it
	vinto = ctx.trova("company.studio_bianchi")
	if vinto:
		for persona in simulazione.clienti_recenti(ctx, 3):
			frappe.db.set_value("CRM Lead", persona, "organization", vinto, update_modified=False)


def _pipeline_per_gli_accordi(nuovi_clienti: str | None) -> str | None:
	"""The pipeline a sale to a company goes in: the default one, unless it is the new
	clients' or the quotes' own."""
	quotes = (
		frappe.db.get_single_value("CRM Quote Settings", "quotes_pipeline")
		if frappe.db.exists("DocType", "CRM Quote Settings")
		else None
	)
	occupate = {nuovi_clienti, quotes}
	candidate = frappe.get_all(
		"CRM Pipeline",
		filters={"disabled": 0},
		fields=["name", "is_default"],
		order_by="is_default desc, position asc, creation asc",
	)
	for riga in candidate:
		if riga.name not in occupate:
			return riga.name
	return None


def _stadio(pipeline: str | None, tipo: str, passo: int) -> str | None:
	"""The ``passo``-th stage of ``tipo`` in ``pipeline``, or the last one there is."""
	if not pipeline:
		return None
	stadi = frappe.get_all(
		"CRM Deal Status",
		filters={"pipeline": pipeline, "type": tipo},
		pluck="name",
		order_by="position asc",
	)
	if not stadi and tipo == "Ongoing":
		stadi = frappe.get_all(
			"CRM Deal Status",
			filters={"pipeline": pipeline, "type": "Open"},
			pluck="name",
			order_by="position asc",
		)
	if not stadi:
		return None
	return stadi[min(passo, len(stadi) - 1)]


# -- the day-to-day ------------------------------------------------------------------------------


def crea_lavoro(ctx: Contesto) -> None:
	persone = simulazione.persone_per_lavoro(ctx)
	if not persone:
		return
	ctx.avanza(_("Things to do"))
	_cose_da_fare(ctx, persone)
	ctx.avanza(_("Notes"))
	_note(ctx, persone)
	ctx.avanza(_("Calls"))
	_chiamate(ctx, persone)
	_commenti(ctx, persone)


def _cose_da_fare(ctx: Contesto, persone: dict[str, list[str]]) -> None:
	scrive = ctx.squadra("desk") or ctx.utente
	for indice, (titolo, descrizione, chi, priorita, stato, scadenza, su_persona) in enumerate(
		dati.COSE_DA_FARE
	):
		incaricato = ctx.squadra(chi) or ctx.utente
		riferimento = {}
		if su_persona:
			lead = _una(ctx, persone, chi, indice)
			if lead:
				riferimento = {"reference_doctype": "CRM Lead", "reference_docname": lead}
		autore = ctx.squadra("manager") if incaricato == scrive else scrive
		with ctx.come(autore):
			doc = frappe.get_doc(
				{
					"doctype": "CRM Task",
					"title": titolo,
					"description": f"<p>{descrizione}</p>",
					"assigned_to": incaricato,
					"priority": priorita,
					"status": stato,
					"due_date": ctx.alle(
						ctx.giorno(scadenza), ctx.rng.choice(("10:00", "12:00", "16:30", "18:00"))
					),
					**riferimento,
				}
			).insert(ignore_permissions=True)
		quando = ctx.adesso - datetime.timedelta(days=max(0, -scadenza) + ctx.rng.randint(1, 5), hours=2)
		ctx.retrodata("CRM Task", doc.name, quando, autore)
		if stato in ("Done", "Canceled"):
			fatto = min(ctx.adesso, quando + datetime.timedelta(days=ctx.rng.randint(1, 3)))
			frappe.db.set_value("CRM Task", doc.name, "modified", fatto, update_modified=False)


def _note(ctx: Contesto, persone: dict[str, list[str]]) -> None:
	for indice, (titolo, testo, chi, su_persona) in enumerate(dati.NOTE):
		autore = ctx.squadra(chi) or ctx.utente
		if su_persona:
			riferimento = ("CRM Lead", _una(ctx, persone, chi, indice))
		else:
			riferimento = (
				"CRM Deal",
				ctx.trova(("agreement.tecnoprogetti", "agreement.olimpia", "agreement.farmacia")[indice % 3]),
			)
		if not riferimento[1]:
			continue
		with ctx.come(autore):
			doc = frappe.get_doc(
				{
					"doctype": "FCRM Note",
					"title": titolo,
					"content": testo,
					"reference_doctype": riferimento[0],
					"reference_docname": riferimento[1],
				}
			).insert(ignore_permissions=True)
		quando = ctx.adesso - datetime.timedelta(days=ctx.rng.randint(1, 30), hours=ctx.rng.randint(0, 8))
		ctx.retrodata("FCRM Note", doc.name, quando, autore)


def _chiamate(ctx: Contesto, persone: dict[str, list[str]]) -> None:
	from crm.demo.simulazione import cellulare_di

	numero_del_centro = "+39 06 555 0100"
	tutte = persone.get("tutte") or []
	for indice, (tipo, esito, minuti, richiamata, messaggio, chi) in enumerate(dati.CHIAMATE * 2):
		if not tutte:
			break
		lead = tutte[(indice * 7) % len(tutte)]
		numero = cellulare_di(lead)
		if not numero:
			continue
		utente = ctx.squadra(chi) or ctx.utente
		inizio = ctx.adesso - datetime.timedelta(
			days=(indice * 23) % 26, hours=ctx.rng.randint(0, 6), minutes=ctx.rng.randint(0, 50)
		)
		inizio = min(inizio, ctx.adesso - datetime.timedelta(minutes=30))
		fine = inizio + datetime.timedelta(minutes=minuti, seconds=ctx.rng.randint(5, 50))
		in_arrivo = tipo == "Incoming"
		doc = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": f"demo-{frappe.generate_hash(length=16)}",
				"type": tipo,
				"status": esito,
				"telephony_medium": "Manual",
				"from": numero if in_arrivo else numero_del_centro,
				"to": numero_del_centro if in_arrivo else numero,
				"start_time": inizio,
				"end_time": fine,
				"duration": int((fine - inizio).total_seconds()) if esito == "Completed" else 0,
				"receiver": utente if in_arrivo else None,
				"caller": None if in_arrivo else utente,
				"reference_doctype": "CRM Lead",
				"reference_docname": lead,
				"callback_status": richiamata,
				"callback_due": inizio + datetime.timedelta(hours=2) if richiamata else None,
				"callback_completed_on": inizio + datetime.timedelta(hours=3)
				if richiamata == "Done"
				else None,
				"left_message": 1 if messaggio else 0,
			}
		)
		doc.insert(ignore_permissions=True)
		ctx.retrodata("CRM Call Log", doc.name, inizio, utente)


def _commenti(ctx: Contesto, persone: dict[str, list[str]]) -> None:
	"""Two colleagues mention whoever loads the demo: they find it in their
	notifications."""
	io = ctx.utente
	if not io or io == "Guest":
		return
	nome = frappe.utils.get_fullname(io)
	menzione = f'<span class="mention" data-type="mention" data-id="{io}" data-label="{nome}">@{nome}</span>'
	parole = (
		("manager", f"<p>{menzione} puoi richiamarla tu? Chiede una proposta per tutta la famiglia.</p>"),
		(
			"desk",
			f"<p>{menzione} ha chiesto di parlare con il responsabile per la fattura del mese scorso.</p>",
		),
	)
	for indice, (chi, testo) in enumerate(parole):
		lead = _una(ctx, persone, chi, indice + 3)
		autore = ctx.squadra(chi)
		if not (lead and autore):
			continue
		with ctx.come(autore):
			commento = frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Comment",
					"reference_doctype": "CRM Lead",
					"reference_name": lead,
					"content": testo,
					"comment_email": autore,
					"comment_by": frappe.utils.get_fullname(autore),
				}
			).insert(ignore_permissions=True)
		ctx.retrodata(
			"Comment", commento.name, ctx.adesso - datetime.timedelta(hours=3 + indice * 20), autore
		)


def _una(ctx: Contesto, persone: dict[str, list[str]], chi: str, indice: int) -> str | None:
	"""A person ``chi`` would write about: one of their clients, else anybody."""
	elenco = persone.get(chi) or persone.get("tutte") or []
	return elenco[(indice * 5) % len(elenco)] if elenco else None
