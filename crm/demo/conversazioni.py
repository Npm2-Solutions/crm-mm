# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's conversations: the emails people wrote to the centre and its answers,
and the SMS and WhatsApp messages where the centre has those on (a channel that is
off shows nothing, so nothing is written for it).

Each message is written as it arrived or left, at its own moment; the product's
hooks keep the person's conversation (`crm.api.conversations`), and whoever follows
the person hears of the new ones. Most are dealt with, a few wait for the centre -
some of them for you - and one was parked for a couple of days. Nobody receives
anything: the addresses and numbers are the demo's (`crm.demo.guardie`).
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import escape_html, get_datetime, get_fullname

from crm.demo import dati
from crm.demo.contesto import Contesto
from crm.demo.simulazione import persone_della_demo, persone_per_lavoro

PERSONA = "CRM Lead"
#: The message doctypes and how a notification names each.
MESSAGGI = ("Communication", "CRM SMS Message", "WhatsApp Message")


def crea(ctx: Contesto) -> None:
	from crm.api import sms, whatsapp

	ctx.avanza(_("Conversations"))
	per_lavoro = persone_per_lavoro(ctx)
	if not per_lavoro:
		return
	scelte = _chi_scrive(ctx)
	usati: set[str] = set()
	conversazioni = []
	for volta in range(2):
		for modello in dati.EMAIL:
			if len(conversazioni) >= ctx.quanti(len(dati.EMAIL) * 2):
				break
			# the second round only for the threads that end dealt with: the waiting
			# ones are few, as in a centre that answers
			if volta and modello[2] != "done":
				continue
			lead, _niente = _persona_per(ctx, modello[1], scelte, per_lavoro, usati, con="email")
			if lead:
				conversazioni.append(("email", modello, lead, None))
	for canale, acceso, modelli in (
		("sms", sms.is_sms_enabled(), dati.SMS),
		("whatsapp", whatsapp.is_whatsapp_enabled(), dati.WHATSAPP),
	):
		if not acceso:
			continue
		for modello in modelli[: ctx.quanti(len(modelli))]:
			passi, esito = modello
			# a reminder is about an appointment the person has
			verifica = _appuntamento_per(ctx, esito) if any("{quando}" in t for _c, _o, t in passi) else None
			lead, appuntamento = _persona_per(
				ctx, "desk", scelte, per_lavoro, usati, con="mobile_no", verifica=verifica
			)
			if lead:
				conversazioni.append((canale, modello, lead, appuntamento))
	with ctx.nella_lingua_del_centro():
		for canale, modello, lead, appuntamento in conversazioni:
			_conversazione(ctx, canale, modello, lead, appuntamento)


def _chi_scrive(ctx: Contesto) -> list[str]:
	"""The people who would write: the ones seen lately first."""
	persone = persone_della_demo(ctx)
	if not persone:
		return []
	return frappe.get_all(
		PERSONA,
		filters={"name": ["in", persone]},
		pluck="name",
		order_by="modified desc",
	)


def _persona_per(ctx, chi: str, scelte, per_lavoro, usati: set, con: str, verifica=None):
	"""Somebody for a thread: one of the practitioner's people when it names one, with
	an address or a mobile, never twice - and what ``verifica`` asks of them (the
	appointment a reminder is about). Returns the person and that."""
	gruppo = (
		scelte if chi in ("desk", "pratico") else [p for p in scelte if p in set(per_lavoro.get(chi, ()))]
	)
	candidati = [p for p in gruppo if p not in usati][:120]
	if not candidati:
		return None, None
	valori = dict(
		frappe.get_all(PERSONA, filters={"name": ["in", candidati]}, fields=["name", con], as_list=True)
	)
	for lead in candidati:
		if not valori.get(lead):
			continue
		trovato = verifica(lead) if verifica else None
		if verifica and not trovato:
			continue
		usati.add(lead)
		return lead, trovato
	return None, None


def _appuntamento_per(ctx: Contesto, esito: str):
	"""The appointment a reminder is about: tomorrow's, for a thread still waiting for
	the centre; else one of the last weeks."""
	if esito == "open":
		dal, al = ctx.adesso + datetime.timedelta(hours=3), ctx.adesso + datetime.timedelta(days=2)
	else:
		dal, al = ctx.adesso - datetime.timedelta(days=20), ctx.adesso - datetime.timedelta(days=1)

	def trova(lead: str):
		riga = frappe.db.sql(
			"""select a.starts_on from `tabCRM Appointment` a
			join `tabCRM Appointment Participant` p on p.parent = a.name and p.parenttype = 'CRM Appointment'
			where p.party = %(lead)s and a.status != 'Cancelled' and p.status != 'Cancelled'
				and a.starts_on between %(dal)s and %(al)s
			order by a.starts_on limit 1""",
			{"lead": lead, "dal": dal, "al": al},
		)
		return get_datetime(riga[0][0]) if riga else None

	return trova


def _firma(ctx: Contesto, chi: str, lead: str) -> str:
	"""Who writes for the centre: the desk, the practitioner named, or the one the
	person saw the most."""
	if chi == "desk":
		return ctx.squadra("desk") or ctx.utente
	if chi != "pratico":
		return ctx.squadra(chi) or ctx.squadra("desk") or ctx.utente
	riga = frappe.db.sql(
		"""select s.user, count(*) n from `tabCRM Appointment Staff` s
		join `tabCRM Appointment Participant` p on p.parent = s.parent and p.parenttype = 'CRM Appointment'
		where p.party = %(lead)s group by s.user order by n desc limit 1""",
		{"lead": lead},
	)
	return riga[0][0] if riga else ctx.squadra("desk") or ctx.utente


def _momenti(ctx: Contesto, passi, esito: str, inizio=None) -> list[datetime.datetime]:
	"""When each message went: from ``inizio`` (a reminder the evening before its
	appointment), else a thread waiting for the centre ends in the last day, the
	others within the last three weeks; never at night, never in the future."""
	ore = [max(int(ore), 0) for _chi, ore, _testo in passi]
	durata = datetime.timedelta(hours=sum(ore))
	if inizio:
		fine = min(inizio + durata, ctx.adesso - datetime.timedelta(minutes=ctx.rng.randint(20, 90)))
	elif esito == "open":
		fine = ctx.adesso - datetime.timedelta(hours=ctx.rng.randint(1, 20), minutes=ctx.rng.randint(0, 50))
	elif esito == "later":
		fine = ctx.adesso - datetime.timedelta(days=ctx.rng.randint(1, 2), hours=ctx.rng.randint(0, 5))
	else:
		fine = ctx.adesso - datetime.timedelta(days=ctx.rng.randint(2, 20), hours=ctx.rng.randint(0, 8))
	momento = fine - durata
	if not inizio:
		momento = momento.replace(hour=min(max(momento.hour, 8), 19))
	momenti = []
	for indice, ora in enumerate(ore):
		if indice:
			momento += datetime.timedelta(hours=ora, minutes=ctx.rng.randint(4, 40))
		momenti.append(min(momento, ctx.adesso - datetime.timedelta(minutes=5 * (len(ore) - indice))))
	return momenti


def _conversazione(ctx: Contesto, canale: str, modello, lead: str, appuntamento=None) -> None:
	from crm.api import conversations

	if canale == "email":
		oggetto, chi, esito, passi = modello
	else:
		(passi, esito), oggetto, chi = modello, None, "desk"
	firma = _firma(ctx, chi, lead)
	persona = frappe.db.get_value(
		PERSONA, lead, ["first_name", "lead_name", "email", "mobile_no"], as_dict=True
	)
	parole = {
		"nome": persona.first_name or persona.lead_name,
		"firma": _chi_firma(firma),
		"quando": _come_si_dice(appuntamento) if appuntamento else "",
	}
	# a reminder goes the evening before its appointment
	sera_prima = (
		datetime.datetime.combine(appuntamento.date() - datetime.timedelta(days=1), datetime.time(18, 30))
		if appuntamento
		else None
	)
	momenti = _momenti(ctx, passi, esito, sera_prima)
	prima = frappe.db.get_value(PERSONA, lead, ["modified", "first_response_time"], as_dict=True)
	scritti = []
	for indice, ((chi_scrive, _ore, testo), quando) in enumerate(zip(passi, momenti, strict=True)):
		lui = chi_scrive == "lui"
		testo = testo.format(**parole)
		if canale == "email":
			nome = _email(ctx, lead, persona, firma, oggetto, indice, lui, testo, quando)
		elif canale == "sms":
			nome = _sms(ctx, lead, persona, firma, lui, testo, quando)
		else:
			nome = _whatsapp(ctx, lead, persona, firma, lui, testo, quando)
		if nome:
			scritti.append((MESSAGGI[("email", "sms", "whatsapp").index(canale)], nome, quando, lui))
	if not scritti:
		return
	# what the conversation says of itself, now that its messages are where they were
	conversations.remember(PERSONA, lead)
	_stato(ctx, lead, esito, scritti, firma)
	_ritocca_la_persona(lead, prima, scritti)


def _ritocca_la_persona(lead: str, prima, scritti: list) -> None:
	"""The framework touched the person as the messages were written, "now": their
	last change is the last message, their first answer the centre's first."""
	ultimo = max(quando for _d, _n, quando, _lui in scritti)
	valori = {"modified": max(get_datetime(prima.modified), ultimo)}
	if not prima.first_response_time and frappe.db.get_value(PERSONA, lead, "first_response_time"):
		risposte = [quando for _d, _n, quando, lui in scritti if not lui]
		creata = get_datetime(frappe.db.get_value(PERSONA, lead, "creation"))
		if risposte and risposte[0] > creata:
			valori.update(
				{
					"first_responded_on": risposte[0],
					"first_response_time": round((risposte[0] - creata).total_seconds(), 2),
				}
			)
	frappe.db.set_value(PERSONA, lead, valori, update_modified=False)


def _chi_firma(utente: str) -> str:
	"""How somebody of the centre signs: their first name."""
	return (get_fullname(utente) or "").split(" ")[0] or utente


def _come_si_dice(quando) -> str:
	"""An appointment's day and time as a person reads them, in the centre's clock."""
	from crm.scheduling.attese import quando as come_si_dice

	return come_si_dice(quando)


def _html(testo: str) -> str:
	return "".join(f"<p>{escape_html(parte).replace(chr(10), '<br>')}</p>" for parte in testo.split("\n\n"))


def _email(ctx, lead, persona, firma, oggetto, indice, lui, testo, quando) -> str | None:
	if not persona.email:
		return None
	indirizzo_firma = frappe.db.get_value("User", firma, "email") or firma
	doc = frappe.get_doc(
		{
			"doctype": "Communication",
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received" if lui else "Sent",
			"subject": oggetto if not indice else f"Re: {oggetto}",
			"content": _html(testo),
			"sender": persona.email if lui else indirizzo_firma,
			"sender_full_name": persona.lead_name if lui else get_fullname(firma),
			"recipients": indirizzo_firma if lui else persona.email,
			"reference_doctype": PERSONA,
			"reference_name": lead,
			"communication_date": quando,
			"status": "Linked",
			"user": None if lui else firma,
		}
	)
	with ctx.come(None if lui else firma):
		doc.insert(ignore_permissions=True)
	ctx.retrodata("Communication", doc.name, quando, "Administrator" if lui else firma)
	return doc.name


def _sms(ctx, lead, persona, firma, lui, testo, quando) -> str | None:
	from crm.telephony import sms as sms_del_centro

	if not persona.mobile_no:
		return None
	centro = sms_del_centro.mittente() or "DottorCloud"
	doc = frappe.get_doc(
		{
			"doctype": "CRM SMS Message",
			"type": "Incoming" if lui else "Outgoing",
			"from": persona.mobile_no if lui else centro,
			"to": centro if lui else persona.mobile_no,
			"message": testo,
			"status": "Received" if lui else "Delivered",
			"telephony_medium": "Twilio",
			"reference_doctype": PERSONA,
			"reference_name": lead,
		}
	)
	with ctx.come(None if lui else firma):
		doc.insert(ignore_permissions=True)
	ctx.retrodata("CRM SMS Message", doc.name, quando, "Administrator" if lui else firma)
	return doc.name


def _whatsapp(ctx, lead, persona, firma, lui, testo, quando) -> str | None:
	from crm.utils import digits_of, to_e164

	if not persona.mobile_no:
		return None
	numero = to_e164(persona.mobile_no)
	valori = {
		"doctype": "WhatsApp Message",
		"type": "Incoming" if lui else "Outgoing",
		"message": testo,
		"content_type": "text",
		"reference_doctype": PERSONA,
		"reference_name": lead,
	}
	if lui:
		# WhatsApp hands the number over without its plus
		valori.update({"from": digits_of(numero), "profile_name": persona.lead_name})
	else:
		valori.update({"to": numero, "status": "read"})
	doc = frappe.get_doc(valori)
	with ctx.come(None if lui else firma):
		doc.insert(ignore_permissions=True)
	if not lui:
		# kept as read on the person's phone: the demo's message never left
		frappe.db.set_value("WhatsApp Message", doc.name, "status", "read", update_modified=False)
	ctx.retrodata("WhatsApp Message", doc.name, quando, "Administrator" if lui else firma)
	return doc.name


def _stato(ctx: Contesto, lead: str, esito: str, scritti: list, firma: str) -> None:
	"""Where the conversation stands: dealt with and read, waiting for the centre - for
	you, when it is the desk's - or parked a couple of days. The notices of the
	messages read the same, at the moments they came."""
	from crm.api.conversations import HANDLED, OPEN

	ultimo = max(quando for _d, _n, quando, _lui in scritti)
	ultimo_suo = scritti[-1][3]
	valori = {"conversation_status": OPEN, "conversation_snoozed_until": None}
	if esito == "done":
		valori.update(
			{
				"conversation_status": HANDLED,
				"conversation_unread": 0,
				"conversation_seen_until": ultimo,
				"conversation_seen_by": firma,
			}
		)
	elif esito == "later":
		valori.update(
			{
				"conversation_snoozed_until": ctx.alle(ctx.giorno(2), "09:00"),
				"conversation_unread": 0,
				"conversation_seen_until": ultimo,
				"conversation_seen_by": firma,
				"conversation_assigned_to": firma,
			}
		)
	else:
		valori.update(
			{
				"conversation_unread": 1 if ultimo_suo else 0,
				# the desk's open ones wait for whoever loads the demo
				"conversation_assigned_to": ctx.utente if firma == ctx.squadra("desk") else firma,
			}
		)
	frappe.db.set_value(PERSONA, lead, valori, update_modified=False)
	letto = esito != "open"
	for doctype, nome, quando, _lui in scritti:
		for notifica in frappe.get_all(
			"CRM Notification",
			filters={"notification_type_doctype": doctype, "notification_type_doc": nome},
			pluck="name",
		):
			frappe.db.set_value(
				"CRM Notification",
				notifica,
				{"creation": quando, "modified": quando, **({"read": 1} if letto else {})},
				update_modified=False,
			)
