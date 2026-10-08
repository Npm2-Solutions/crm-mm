# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders of the appointments (docs/crm/59): the day before, by
WhatsApp with three buttons, else SMS, else email; and what the person answers.

Every quarter of an hour (`ogni_quarto_d_ora`) the places whose reminder is due
get it - each person of a class their own - once for the time they are booked at:
an appointment moved is reminded again of its new time. Where the centre wants it,
a second one leaves the same day (`second_hours_before`), not to whoever already
said they are coming or cannot come. The register (`CRM
Appointment Reminder`) keeps each one, written before it leaves so that it never
leaves twice: by which way, to where, how it went, what was answered. A WhatsApp
that did not arrive goes by SMS or email at the next round.

An answer - a button tapped on WhatsApp (`alla_risposta_whatsapp`), an SMS that
says yes or no and nothing else (`alla_risposta_sms`), «I'll be there» on the
booking page (`conferma_dalla_pagina`) - is kept on its reminder (`rispondi`). A
«cannot come» cancels the person's place where the centre wants it, and the time
goes to whoever waits; a «move it» gets the booking page's link where the service
moves online; whoever runs the agenda is told of both.

It writes to the number and the address the booking keeps, as the waiting list's
offers do; never about the demo's appointments, nor about the ones a booking
platform keeps (the platform reminds them itself).
"""

from __future__ import annotations

import datetime
import re
import secrets
from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import cint, escape_html, format_datetime, get_datetime, get_fullname, get_url, now_datetime

from crm.notifiche import regole as N
from crm.permissions import livelli
from crm.scheduling import promemoria_regole as R
from crm.scheduling import visite_online
from crm.scheduling.timeutils import from_system_naive, scheduling_tz, to_system_naive
from crm.telephony import sms as sms_del_centro

IMPOSTAZIONI = "CRM Reminder Settings"
PROMEMORIA = "CRM Appointment Reminder"
APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"
#: The appointments that are still to come.
ATTIVI = ("Scheduled", "Confirmed")
#: At most this many reminders in a round: the next round takes the rest.
PER_GIRO = 200
#: How long after it left an SMS reminder is answered by «SI» or «NO».
RISPOSTA_SMS = datetime.timedelta(days=4)


# ------------------------------------------------------------------ the centre's choices


def _si(valore, predefinito: bool) -> bool:
	"""A tick of a Single that may never have been saved: its default then."""
	return predefinito if valore is None else bool(cint(valore))


def impostazioni() -> frappe._dict:
	doc = frappe.get_cached_doc(IMPOSTAZIONI)
	return frappe._dict(
		attivi=_si(doc.get("enabled"), False),
		ore=R.ore_prima(doc.get("hours_before")),
		secondo=R.ore_del_secondo(doc.get("second_hours_before"), R.ore_prima(doc.get("hours_before"))),
		whatsapp=_modello_whatsapp(doc.get("whatsapp_template")),
		# the centre's one sender (doc 52), the same as every other SMS of its
		sms=sms_del_centro.mittente() if _si(doc.get("use_sms"), False) else None,
		email=_si(doc.get("use_email"), True),
		disdice=_si(doc.get("cancel_on_reply"), True),
	)


def _modello_whatsapp(nome: str | None) -> str | None:
	if not nome or not frappe.db.exists("DocType", "WhatsApp Templates"):
		return None
	return nome if frappe.db.exists("WhatsApp Templates", {"name": nome, "status": "APPROVED"}) else None


def _quante_variabili(modello: str) -> int:
	corpo = frappe.db.get_value("WhatsApp Templates", modello, "template") or ""
	return len(set(re.findall(r"{{\s*(\d+)\s*}}", corpo)))


# ------------------------------------------------------------------ time and words


def _locale(valore) -> datetime.datetime:
	"""A moment of the agenda in the centre's clock, without its zone: as the rules
	read it."""
	return from_system_naive(valore).astimezone(scheduling_tz()).replace(tzinfo=None)


def _di_sistema(locale: datetime.datetime) -> datetime.datetime:
	return to_system_naive(locale.replace(tzinfo=scheduling_tz()))


def _adesso() -> datetime.datetime:
	return datetime.datetime.now(scheduling_tz()).replace(tzinfo=None)


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


def quando(valore) -> str:
	"""A day and a time as a person reads them: «mercoledì 7 ottobre alle 09:30»."""
	momento = _locale(valore)
	return _("{0} at {1}").format(format_datetime(momento, "EEEE d MMMM"), format_datetime(momento, "HH:mm"))


def _nome_del_centro() -> str:
	from crm.moduli.richieste import nome_del_centro

	return nome_del_centro() or _("the centre")


# ------------------------------------------------------------------ who and where


def persona_di(riga) -> str | None:
	"""The person a place's messages go to: who booked it for somebody else, else
	the person themselves, else the deal's."""
	if riga.get("booked_by"):
		return riga.booked_by
	if riga.get("party_type") == "CRM Lead":
		return riga.party
	if riga.get("party_type") == "CRM Deal" and riga.get("party"):
		return frappe.db.get_value("CRM Deal", riga.party, "lead")
	return None


def destinatario(riga) -> tuple[str | None, str | None, str | None]:
	"""Who hears of a place's reminder, and where: the email and the mobile the
	booking keeps - a family shares a phone - else the person's own."""
	from crm.api.whatsapp import numbers_of
	from crm.utils import stored_value, to_e164

	persona = persona_di(riga)
	email = (riga.get("email") or "").strip() or (
		stored_value("CRM Lead", persona, "email") if persona else None
	)
	numero = to_e164(riga.phone) if riga.get("phone") else None
	if not numero and persona:
		numeri = numbers_of("CRM Lead", persona)
		numero = numeri[0] if numeri else None
	return persona, email or None, numero


def _link(riga) -> str:
	"""The booking page's own link for this place: made the first time it is needed."""
	from crm.api.service_booking import manage_url

	if not riga.access_token:
		riga.access_token = secrets.token_urlsafe(24)
		frappe.db.set_value(PARTECIPANTE, riga.name, "access_token", riga.access_token)
	return manage_url(riga.access_token)


def _testo(appuntamento, riga, persona: str | None) -> dict:
	nome = (frappe.db.get_value("CRM Lead", persona, "first_name") or "").strip() if persona else ""
	nome = nome or (riga.participant_name or "").strip().split(" ")[0]
	servizio = frappe.db.get_value("CRM Service", appuntamento.service, "service_name") or (
		appuntamento.title or _("your appointment")
	)
	# a child booked by a parent: whose appointment it is
	per_altri = riga.booked_by and not (riga.party_type == "CRM Lead" and riga.party == riga.booked_by)
	# held by video: every way says so, in what it is (a WhatsApp template's words
	# are fixed); the email and the SMS say how to enter it - from the area, never
	# the room's link
	online = visite_online.del_servizio(appuntamento.service)
	if online:
		servizio = _("{0}, online visit").format(servizio)
	return {
		"nome": nome,
		"cosa": _("{0} for {1}").format(servizio, riga.participant_name)
		if per_altri and riga.participant_name
		else servizio,
		"quando": quando(appuntamento.starts_on),
		"centro": _nome_del_centro(),
		"con": ", ".join(get_fullname(s.user) for s in appuntamento.staff if s.user),
		# whose area: the person who comes (a child's, entered by the parent)
		"online": visite_online.frase(
			visite_online.area_per(riga.party if riga.party_type == "CRM Lead" else persona)
		)
		if online
		else "",
	}


# ------------------------------------------------------------------ the rounds


def ogni_quarto_d_ora() -> None:
	"""Every quarter of an hour: the reminders that are due, then the WhatsApp ones
	that did not arrive."""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	conf = impostazioni()
	if not conf.attivi:
		return
	with _nella_lingua_del_centro():
		for appuntamento, riga, quale in dovuti(conf):
			try:
				manda(appuntamento, riga, conf, quale)
				_conferma()
			except Exception:
				_annulla()
				frappe.log_error(
					title=f"Reminder of {appuntamento.name} not sent",
					reference_doctype=APPUNTAMENTO,
					reference_name=appuntamento.name,
				)
		for nome in da_ricontrollare():
			try:
				ricontrolla(nome, conf)
				_conferma()
			except Exception:
				_annulla()
				frappe.log_error(
					title=f"Reminder {nome} not checked", reference_doctype=PROMEMORIA, reference_name=nome
				)


def _conferma() -> None:
	"""Each reminder on its own: one that fails takes nothing else with it."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — each reminder of the round on its own


def _annulla() -> None:
	if not frappe.flags.in_test:
		frappe.db.rollback()


def dovuti(conf=None) -> list[tuple]:
	"""The places whose reminder leaves now: (appointment, participant's row, which
	reminder - `R.PRIMO` or `R.SECONDO`)."""
	from crm.demo import guardie

	conf = conf or impostazioni()
	adesso = _adesso()
	dal, al = R.da_cercare(adesso, conf.ore, bool(conf.secondo))
	nomi = frappe.get_all(
		APPUNTAMENTO,
		filters={
			"status": ["in", ATTIVI],
			"starts_on": ["between", (_di_sistema(dal), _di_sistema(al))],
		},
		pluck="name",
		order_by="starts_on asc",
	)
	if not nomi:
		return []
	# each place's reminders already written for its time, and whether it was answered
	fatti, risposti = {}, set()
	for r in frappe.get_all(
		PROMEMORIA,
		filters={"appointment": ["in", nomi]},
		fields=["appointment", "party_type", "party", "starts_on", "second", "answer"],
	):
		chiave = (r.appointment, r.party_type, r.party, get_datetime(r.starts_on))
		fatti.setdefault(chiave, set()).add(R.SECONDO if r.second else R.PRIMO)
		if R.chiude(r.answer):
			risposti.add(chiave)
	dovuti_ = []
	for nome in nomi:
		# nothing about the demo leaves (crm/demo/guardie.py)
		if guardie.mai_fuori(APPUNTAMENTO, nome):
			continue
		doc = frappe.get_doc(APPUNTAMENTO, nome)
		# a booking platform reminds its own; an online booking still waits for the centre's yes
		if doc.source == "External" or (doc.source == "Online" and doc.status == "Scheduled"):
			continue
		inizio = get_datetime(doc.starts_on)
		for riga in doc.participants:
			if riga.status != "Booked" or not riga.party:
				continue
			chiave = (doc.name, riga.party_type, riga.party, inizio)
			quale = R.quale(
				_locale(doc.starts_on),
				adesso,
				conf.ore,
				conf.secondo,
				_locale(doc.creation),
				fatti.get(chiave, ()),
				chiave in risposti,
			)
			if not quale:
				continue
			dovuti_.append((doc, riga, quale))
			if len(dovuti_) >= PER_GIRO:
				return dovuti_
	return dovuti_


def manda(appuntamento, riga, conf=None, quale: int = R.PRIMO) -> str:
	"""The reminder of one place, by the first way that works; kept in the register
	however it went, and written there before it leaves - the same day's second
	one marked so. Returns its name."""
	conf = conf or impostazioni()
	persona, email, numero = destinatario(riga)
	fermato = bool(persona) and sms_del_centro.ha_fermato("CRM Lead", persona)
	vie = R.canali(
		bool(conf.whatsapp) and bool(persona),
		bool(conf.sms) and bool(persona),
		conf.email,
		bool(numero),
		bool(email),
		fermato,
	)
	registro = frappe.get_doc(
		{
			"doctype": PROMEMORIA,
			"appointment": appuntamento.name,
			"party_type": riga.party_type,
			"party": riga.party,
			"lead": persona,
			"starts_on": appuntamento.starts_on,
			"second": 1 if quale == R.SECONDO else 0,
			"status": R.NON_INVIATO,
			"sent_on": now_datetime(),
		}
	)
	if not vie:
		registro.reason = _perche_no(numero, email, fermato)
		registro.insert(ignore_permissions=True)
		return registro.name
	registro.insert(ignore_permissions=True)
	# written down before it leaves: whatever happens next, it never leaves twice
	_conferma()
	testo = _testo(appuntamento, riga, persona)
	testo["link"] = _link(riga)
	_per_le_vie(registro, vie, appuntamento, persona, email, numero, testo, conf)
	return registro.name


def _perche_no(numero, email, fermato) -> str:
	if fermato and numero and not email:
		return _("They wrote STOP to the centre's SMS and have no email on file: call them")
	if not (numero or email):
		return _("No email or mobile on file: call them")
	return _("None of the centre's ways reaches them: call them")


def _in_parole(errore: Exception) -> str:
	"""Why a way did not work, in DottorCloud's words: the framework's sentence for a
	site with no outgoing mailbox names its Desk («Strumenti > Account Email»)."""
	if isinstance(errore, frappe.OutgoingEmailError):
		return _("no mailbox sends the centre's emails yet: Settings > Email > Accounts")
	return str(errore)


def _per_le_vie(registro, vie, appuntamento, persona, email, numero, testo, conf, nota=None) -> bool:
	"""The reminder by the first of ``vie`` that works, written on its register."""
	errori = []
	for via in vie:
		try:
			messaggio = _manda_per(via, appuntamento, persona, email, numero, testo, conf)
		except Exception as errore:
			frappe.clear_last_message()
			frappe.log_error(
				title=f"Reminder not sent by {via}",
				reference_doctype=PROMEMORIA,
				reference_name=registro.name,
			)
			errori.append(f"{via}: {_in_parole(errore)}")
			continue
		registro.update(
			{
				"channel": via,
				"status": R.INVIATO,
				"sent_on": now_datetime(),
				"sent_to": email if via == R.EMAIL else numero,
				"message_doctype": messaggio[0],
				"message_name": messaggio[1],
				"reason": nota,
			}
		)
		registro.save(ignore_permissions=True)
		return True
	registro.reason = "; ".join(parte for parte in [nota, *errori] if parte)[:500]
	registro.save(ignore_permissions=True)
	return False


def _manda_per(via, appuntamento, persona, email, numero, testo, conf) -> tuple[str | None, str | None]:
	if via == R.WHATSAPP:
		from crm.api.whatsapp import manda_modello

		valori = R.variabili(
			_quante_variabili(conf.whatsapp), testo["nome"], testo["cosa"], testo["quando"], testo["centro"]
		)
		return "WhatsApp Message", manda_modello("CRM Lead", persona, numero, conf.whatsapp, valori)
	if via == R.SMS:
		from crm.api.sms import create_sms, deliver_via_twilio

		doc = create_sms(
			type="Outgoing",
			from_number=conf.sms,
			to=numero,
			message=testo_sms(testo, conf.sms),
			reference_doctype="CRM Lead",
			reference_name=persona,
		)
		deliver_via_twilio(doc)
		if doc.status == "Failed":
			raise frappe.ValidationError(doc.error_message or _("The SMS did not leave"))
		return "CRM SMS Message", doc.name
	_per_email(appuntamento, email, testo)
	return None, None


def testo_sms(testo: dict, mittente: str | None) -> str:
	"""The SMS of a reminder: answered «SI» or «NO» where the person can answer
	the sender, the booking page's link in any case."""
	if sms_del_centro.si_risponde(mittente):
		corpo = _(
			"{0}: a reminder of your appointment: {1}, {2}. Reply YES to confirm, NO if you cannot come. To move it: {3}"
		).format(testo["centro"], testo["cosa"], testo["quando"], testo["link"])
	else:
		corpo = _("{0}: a reminder of your appointment: {1}, {2}. To confirm, move or cancel it: {3}").format(
			testo["centro"], testo["cosa"], testo["quando"], testo["link"]
		)
	return f"{corpo} {testo['online']}" if testo.get("online") else corpo


def _per_email(appuntamento, email: str, testo: dict) -> None:
	from crm.posta.aspetto import pulsante

	esc = escape_html
	righe = [
		f"<p>{esc(_('Hi {0},').format(testo['nome']))}</p>" if testo["nome"] else "",
		f"<p>{esc(_('a reminder of your appointment at {0}:').format(testo['centro']))}</p>",
		f"<p><b>{esc(testo['cosa'])}</b><br>{esc(testo['quando'])}"
		+ (f"<br>{esc(_('With {0}').format(testo['con']))}" if testo["con"] else "")
		+ "</p>",
		f"<p>{esc(testo['online'])}</p>" if testo.get("online") else "",
		pulsante(testo["link"], _("Confirm, move or cancel")),
		f'<p class="text-muted text-small">{esc(_("If you cannot come, let us know: the time goes to whoever is waiting for one."))}</p>',
	]
	frappe.sendmail(
		recipients=[email],
		subject=_("Reminder: {0}, {1}").format(testo["cosa"], testo["quando"]),
		header=_("Your appointment"),
		with_container=True,
		message="".join(righe),
		reference_doctype=APPUNTAMENTO,
		reference_name=appuntamento.name,
	)


# ------------------------------------------------------------------ a WhatsApp that did not arrive


def da_ricontrollare() -> list[str]:
	"""The WhatsApp reminders of the last hours nobody answered yet: one Meta could
	not deliver goes another way."""
	adesso = now_datetime()
	return frappe.get_all(
		PROMEMORIA,
		filters={
			"channel": R.WHATSAPP,
			"status": R.INVIATO,
			"answer": ["is", "not set"],
			"sent_on": [">", adesso - R.GUARDA_INDIETRO],
			"starts_on": [">", adesso + R.ULTIMA_ORA],
		},
		pluck="name",
	)


def ricontrolla(nome: str, conf=None) -> None:
	"""A WhatsApp reminder Meta said it could not deliver: by SMS or email, when
	the centre has them and the person can receive them; else it says so."""
	conf = conf or impostazioni()
	registro = frappe.get_doc(PROMEMORIA, nome)
	if registro.message_doctype != "WhatsApp Message" or not registro.message_name:
		return
	stato = (frappe.db.get_value("WhatsApp Message", registro.message_name, "status") or "").lower()
	if stato != "failed":
		return
	nota = _("WhatsApp did not deliver it")
	appuntamento = frappe.get_doc(APPUNTAMENTO, registro.appointment)
	riga = _riga_di(appuntamento, registro)
	if not riga or not R.vale(
		appuntamento.status, _locale(appuntamento.starts_on), _locale(registro.starts_on), _adesso()
	):
		registro.update({"status": R.NON_CONSEGNATO, "reason": nota})
		registro.save(ignore_permissions=True)
		return
	persona, email, numero = destinatario(riga)
	fermato = bool(persona) and sms_del_centro.ha_fermato("CRM Lead", persona)
	vie = R.canali(False, bool(conf.sms) and bool(persona), conf.email, bool(numero), bool(email), fermato)
	if vie:
		testo = _testo(appuntamento, riga, persona)
		testo["link"] = _link(riga)
		if _per_le_vie(registro, vie, appuntamento, persona, email, numero, testo, conf, nota=nota):
			return
	registro.update({"status": R.NON_CONSEGNATO, "reason": nota})
	registro.save(ignore_permissions=True)


def _riga_di(appuntamento, registro):
	return next(
		(
			r
			for r in appuntamento.participants
			if r.party_type == registro.party_type and r.party == registro.party and r.status == "Booked"
		),
		None,
	)


# ------------------------------------------------------------------ the answers


def alla_risposta_whatsapp(doc, method=None) -> None:
	"""A reminder's button tapped on WhatsApp (WhatsApp Message after_insert): the
	answer kept and done, a word back. A message that is not one passes by."""
	if (
		doc.get("type") != "Incoming"
		or doc.get("content_type") != "button"
		or not doc.get("reply_to_message_id")
	):
		return
	inviato = frappe.db.get_value(
		"WhatsApp Message", {"message_id": doc.reply_to_message_id, "type": "Outgoing"}, "name"
	)
	nome = inviato and frappe.db.get_value(
		PROMEMORIA, {"message_doctype": "WhatsApp Message", "message_name": inviato}, "name"
	)
	if not nome:
		return
	registro = frappe.get_doc(PROMEMORIA, nome)
	# the number that taps is the one written to: a message made up elsewhere does nothing
	if not R.stesso_numero(doc.get("from"), registro.sent_to):
		return
	cosa = R.risposta(doc.message, pulsante=True)
	if not cosa:
		return
	frappe.db.savepoint("promemoria")
	try:
		with _nella_lingua_del_centro():
			testo = rispondi(registro, cosa, R.WHATSAPP)
			if testo:
				_su_whatsapp(registro, doc, testo)
	except Exception:
		frappe.db.rollback(save_point="promemoria")
		frappe.log_error(
			title="Reminder: a WhatsApp answer not taken", reference_doctype=PROMEMORIA, reference_name=nome
		)


def _su_whatsapp(registro, risposta, testo: str) -> None:
	"""A word back in the conversation the person just wrote in, quoting them."""
	from crm.api.whatsapp import insert_and_send

	messaggio = frappe.new_doc("WhatsApp Message")
	messaggio.update(
		{
			"reference_doctype": "CRM Lead",
			"reference_name": registro.lead,
			"message": testo,
			"to": risposta.get("from"),
			"content_type": "text",
			"is_reply": True,
			"reply_to_message_id": risposta.message_id,
		}
	)
	insert_and_send(messaggio)


def alla_risposta_sms(messaggio) -> str:
	"""An SMS that answers a reminder - «SI», «NO», «sposta», nothing else - from
	the number it went to, while its appointment is ahead. The words to send back;
	'' for a message, which stays a message."""
	cosa = R.risposta(messaggio.message)
	if not cosa:
		return ""
	adesso = now_datetime()
	candidati = frappe.get_all(
		PROMEMORIA,
		filters={
			"channel": R.SMS,
			"status": R.INVIATO,
			"starts_on": [">", adesso],
			"sent_on": [">", adesso - RISPOSTA_SMS],
		},
		fields=["name", "sent_to"],
		order_by="sent_on desc",
		limit=50,
	)
	nome = next((c.name for c in candidati if R.stesso_numero(c.sent_to, messaggio.get("from"))), None)
	if not nome:
		return ""
	with _nella_lingua_del_centro():
		return rispondi(frappe.get_doc(PROMEMORIA, nome), cosa, R.SMS) or ""


def rispondi(registro, cosa: str, via: str) -> str | None:
	"""What the person answered a reminder: kept on it and done - a «cannot come»
	cancels their place where the centre wants it -, the agenda's people told. The
	words to send back to the person, if any."""
	appuntamento = frappe.get_doc(APPUNTAMENTO, registro.appointment)
	mie = [
		r
		for r in appuntamento.participants
		if r.party_type == registro.party_type and r.party == registro.party
	]
	partecipa = any(r.status == "Booked" for r in mie)
	if not R.vale(
		appuntamento.status,
		_locale(appuntamento.starts_on),
		_locale(registro.starts_on),
		_adesso(),
		partecipa,
	):
		# the same button again after it was done, or an answer to an old time
		if registro.answer == cosa:
			return None
		return _("This appointment has changed in the meantime: for anything, write to us or call us.")
	if registro.answer == cosa:
		return None
	registro.update({"answer": cosa, "answered_on": now_datetime(), "answered_by": via})
	testo = _testo(appuntamento, mie[0], registro.lead)
	if cosa == R.CONFERMA:
		registro.save(ignore_permissions=True)
		if via != R.WHATSAPP:
			return None
		if testo["nome"]:
			return _("Thank you, {0}: see you {1}.").format(testo["nome"], testo["quando"])
		return _("Thank you: see you {0}.").format(testo["quando"])
	if cosa == R.NON_VIENE:
		disdetto = impostazioni().disdice and _disdici(appuntamento, mie)
		registro.cancelled = 1 if disdetto else 0
		registro.save(ignore_permissions=True)
		_avvisa(appuntamento, registro, testo, N.PROMEMORIA_DISDETTO if disdetto else N.PROMEMORIA_NON_VIENE)
		if not disdetto:
			return _(
				"Thank you for letting us know: the centre will cancel it and help you find another time."
			)
		pagina = _pagina_di_prenotazione()
		if pagina:
			return _(
				"Thank you for letting us know: the appointment of {0} is cancelled. To book another one: {1}"
			).format(testo["quando"], pagina)
		return _("Thank you for letting us know: the appointment of {0} is cancelled.").format(
			testo["quando"]
		)
	registro.save(ignore_permissions=True)
	_avvisa(appuntamento, registro, testo, N.PROMEMORIA_SPOSTA)
	link = _link_per_spostare(appuntamento, mie)
	if link:
		return _("Choose another time here: {0}. The centre knows you would like to move it.").format(link)
	return _("Thank you: the centre will get in touch to find another time.")


def _disdici(appuntamento, mie: list) -> bool:
	"""The person's place cancelled: their seat in a class that goes on, else the
	whole appointment. Saved as the desk would, so the time goes to whoever waits."""
	from crm.verticali import parola

	altre = [r for r in appuntamento.participants if r.status != "Cancelled" and all(r is not m for m in mie)]
	if altre:
		for riga in mie:
			riga.status = "Cancelled"
	else:
		appuntamento.status = "Cancelled"
		appuntamento.cancellation_reason = parola("Cancelled by the client, answering the reminder")
		for riga in appuntamento.participants:
			riga.status = "Cancelled"
	# the person was answered in their own conversation: no email besides it
	prima = frappe.flags.in_service_booking_api
	frappe.flags.in_service_booking_api = True
	try:
		appuntamento.save(ignore_permissions=True)
	finally:
		frappe.flags.in_service_booking_api = prima
	return True


def _pagina_di_prenotazione() -> str | None:
	"""The booking page, where the centre has something to book on it."""
	if not frappe.db.exists("CRM Service", {"enabled": 1, "bookable_online": 1}):
		return None
	return get_url("/prenota")


def _link_per_spostare(appuntamento, mie: list) -> str | None:
	"""The booking page's link for the person's place, where it moves online now."""
	from crm.api import service_booking

	riga = next((r for r in mie if r.status == "Booked"), None)
	if not riga or not frappe.db.get_value(
		"CRM Service", {"name": appuntamento.service, "enabled": 1, "bookable_online": 1}
	):
		return None
	link = _link(riga)
	return (
		link if service_booking.public_view(appuntamento, riga.access_token).get("can_reschedule") else None
	)


def _avvisa(appuntamento, registro, testo: dict, frase: str) -> None:
	"""Whoever runs the agenda, and whoever the appointment is with."""
	from crm.notifiche.avvisi import avvisa
	from crm.scheduling.esiti import chi_avvisare

	nome = (
		frappe.db.get_value(registro.party_type, registro.party, "lead_name")
		if registro.party_type == "CRM Lead"
		else None
	) or next((r.participant_name for r in appuntamento.participants if r.party == registro.party), "")
	utenti = dict.fromkeys([*chi_avvisare(), *(s.user for s in appuntamento.staff if s.user)])
	for utente in utenti:
		avvisa(
			utente,
			"Agenda",
			frase,
			[nome, testo["quando"]],
			riguarda=("CRM Lead", registro.lead) if registro.lead else None,
			oggetto=(APPUNTAMENTO, appuntamento.name),
		)


# ------------------------------------------------------------------ the booking page


def stato_per_la_pagina(appuntamento, riga) -> dict:
	"""For the booking page: whether the person may say «I'll be there», and
	whether they did."""
	registro = _registro_di(appuntamento, riga)
	if not registro or registro.status != R.INVIATO:
		return {"can_confirm": False, "confirmed": False}
	confermato = registro.answer == R.CONFERMA
	return {"can_confirm": not confermato, "confirmed": confermato}


def _registro_di(appuntamento, riga):
	nome = frappe.db.get_value(
		PROMEMORIA,
		{
			"appointment": appuntamento.name,
			"party_type": riga.party_type,
			"party": riga.party,
			"starts_on": appuntamento.starts_on,
		},
		"name",
		order_by="creation desc",
	)
	return frappe.get_doc(PROMEMORIA, nome) if nome else None


def conferma_dalla_pagina(appuntamento, riga) -> None:
	"""«I'll be there» from the booking page the reminder linked to."""
	registro = _registro_di(appuntamento, riga)
	if not registro:
		frappe.throw(_("There is nothing to confirm for this appointment."))
	rispondi(registro, R.CONFERMA, R.DALLA_PAGINA)


def disdetto_dalla_pagina(appuntamento, righe) -> None:
	"""Places cancelled on the booking page: their reminder's answer, «cannot come»,
	kept as done - the page has cancelled them and told the desk already."""
	for riga in righe:
		registro = _registro_di(appuntamento, riga)
		if not registro or registro.status != R.INVIATO or registro.answer == R.NON_VIENE:
			continue
		registro.update(
			{
				"answer": R.NON_VIENE,
				"answered_on": now_datetime(),
				"answered_by": R.DALLA_PAGINA,
				"cancelled": 1,
			}
		)
		registro.save(ignore_permissions=True)


# ------------------------------------------------------------------ the agenda


def nelle_righe(appuntamenti: list[dict]) -> None:
	"""The reminder of each person's place on the agenda's rows: sent or not,
	answered or not - the latest one for the time they are booked at."""
	if not appuntamenti:
		return
	per = {}
	for r in frappe.get_all(
		PROMEMORIA,
		filters={"appointment": ["in", [a["name"] for a in appuntamenti]]},
		fields=[
			"appointment",
			"party_type",
			"party",
			"starts_on",
			"channel",
			"status",
			"answer",
			"answered_on",
			"cancelled",
			"second",
		],
		order_by="creation asc",
	):
		chiave = (r.appointment, r.party_type, r.party, get_datetime(r.starts_on))
		prima = per.get(chiave)
		# the same day's second one, not answered (yet): the first one's answer stands
		if prima and prima.answer and not r.answer:
			r.update({k: prima[k] for k in ("answer", "answered_on", "cancelled")})
		per[chiave] = r
	# with a second one the centre sends, the first says it is the first
	due = bool(impostazioni().secondo)
	for appuntamento in appuntamenti:
		inizio = get_datetime(appuntamento["starts_on"])
		for partecipante in appuntamento.get("participants") or []:
			r = per.get(
				(appuntamento["name"], partecipante.get("party_type"), partecipante.get("party"), inizio)
			)
			if r:
				partecipante["reminder"] = {
					"channel": r.channel,
					"status": r.status,
					"answer": r.answer or "",
					"answered_on": str(r.answered_on) if r.answered_on else None,
					"cancelled": bool(r.cancelled),
					"which": quale(r.second, due),
				}


# ------------------------------------------------------------------ the settings


@frappe.whitelist()
def get_settings() -> dict:
	livelli.verifica("agenda.configura")
	from crm.api.whatsapp import sending_account_name
	from crm.integrations.whatsapp.templates import modelli_inviabili, templates_available

	doc = frappe.get_cached_doc(IMPOSTAZIONI)
	conf = impostazioni()
	modelli = []
	for modello in modelli_inviabili() if templates_available() else []:
		pulsanti = _pulsanti(modello["name"])
		# the answers reach the agenda only from a template with their buttons
		modelli.append({**modello, "buttons": pulsanti, "suitable": R.ha_i_pulsanti(pulsanti)})
	return {
		"enabled": int(conf.attivi),
		"hours_before": conf.ore,
		"second_hours_before": cint(doc.get("second_hours_before")) or "",
		"cancel_on_reply": int(conf.disdice),
		"whatsapp_template": doc.get("whatsapp_template") or "",
		"use_sms": int(_si(doc.get("use_sms"), False)),
		"use_email": int(conf.email),
		"templates": modelli,
		"our_template": _il_nostro(),
		"whatsapp": templates_available() and bool(sending_account_name()),
		"can_make_template": templates_available() and livelli.puo("modelli_messaggio.gestisci"),
		"sms_sender": sms_del_centro.mittente(),
		"sms_replies": sms_del_centro.si_risponde(sms_del_centro.mittente()),
		"recent": recenti(),
	}


def _pulsanti(modello: str) -> list[str]:
	return frappe.get_all(
		"WhatsApp Button",
		filters={"parent": modello, "parenttype": "WhatsApp Templates", "button_type": "Quick Reply"},
		pluck="button_label",
		order_by="idx asc",
	)


def _il_nostro() -> dict | None:
	"""DottorCloud's own reminder template on the number that sends, if it was made:
	its name and where Meta's review is. Another account's is not it (doc 12): the
	number that sends could not send it."""
	from crm import lingue
	from crm.api.whatsapp import sending_account_name
	from crm.integrations.whatsapp.modelli_regole import stesso_account
	from crm.integrations.whatsapp.templates import numeri, templates_available

	if not templates_available():
		return None
	nome = R.modello(lingue.del_centro())["template_name"]
	# on Meta it is «nome», or «nome_2» made on a second account (`_nome_libero`)
	forma = re.compile(rf"{re.escape(nome)}(_\d+)?")
	meta = frappe.get_meta("WhatsApp Templates")
	campi = ["name", "status", "template_name"] + [
		campo for campo in ("actual_name", "whatsapp_account") if meta.has_field(campo)
	]
	invia, numeri_ = sending_account_name(), numeri()
	riga = next(
		(
			riga
			for riga in frappe.get_all(
				"WhatsApp Templates",
				filters={"template_name": ["like", f"{nome}%"]},
				fields=campi,
				order_by="creation desc",
			)
			if forma.fullmatch(riga.get("actual_name") or riga.template_name)
			and stesso_account(riga.get("whatsapp_account"), invia, numeri_)
		),
		None,
	)
	return {"name": riga.name, "status": riga.status or ""} if riga else None


def _nome_libero(nome: str) -> str:
	"""A template's name is one on the site whatever its account (frappe_whatsapp's
	label, Meta's name made from it): ours made on a second account takes the next
	number."""
	libero, numero = nome, 1
	while frappe.db.exists("WhatsApp Templates", {"template_name": libero}):
		numero += 1
		libero = f"{nome}_{numero}"
	return libero


@frappe.whitelist(methods=["POST"])
def save_settings(data: dict | str) -> dict:
	livelli.verifica("agenda.configura")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(IMPOSTAZIONI)
	for campo in (
		"enabled",
		"hours_before",
		"second_hours_before",
		"cancel_on_reply",
		"whatsapp_template",
		"use_sms",
		"use_email",
	):
		if campo in dati:
			doc.set(campo, dati[campo])
	secondo = cint(doc.get("second_hours_before"))
	minimo, massimo = R.ORE_DEL_SECONDO
	# out of its hours it is said, as the page says it, never put right in silence
	if secondo and (
		not minimo <= secondo <= massimo or not R.ore_del_secondo(secondo, R.ore_prima(doc.hours_before))
	):
		frappe.throw(
			_("The second reminder leaves from 1 to 12 hours before, and fewer hours than the first.")
		)
	if secondo:
		doc.second_hours_before = R.ore_del_secondo(secondo, R.ore_prima(doc.hours_before))
	if doc.whatsapp_template:
		etichette = _pulsanti(doc.whatsapp_template)
		if not R.ha_i_pulsanti(etichette):
			frappe.throw(
				_(
					"This template has no buttons to confirm and to cancel: the answers would not reach the agenda."
				)
			)
	doc.save()
	return get_settings()


@frappe.whitelist(methods=["POST"])
def create_template() -> dict:
	"""DottorCloud's own reminder template, in the centre's language, made on the
	number that sends: Meta reviews it, and once approved it is chosen here."""
	livelli.verifica("agenda.configura")
	from crm import lingue
	from crm.integrations.whatsapp import modelli_regole
	from crm.integrations.whatsapp.templates import save_template

	if _il_nostro():
		frappe.throw(_("The reminder template is already there: Meta reviews it, then it can be chosen."))
	modello = R.modello(lingue.del_centro())
	modello["template_name"] = _nome_libero(modello["template_name"])
	risultato = save_template(
		{
			**{chiave: valore for chiave, valore in modello.items() if chiave != "buttons"},
			"buttons": [{"type": modelli_regole.RISPOSTA, "text": testo} for testo in modello["buttons"]],
		}
	)
	return {**get_settings(), "made": risultato}


def quale(secondo, due: bool) -> str:
	"""Which reminder a row of the register is, for the screens: "second", "first"
	where the centre sends two, else nothing to say."""
	if secondo:
		return "second"
	return "first" if due else ""


def recenti(quanti: int = 20) -> list[dict]:
	"""The last reminders, for the settings page: who, for when, by which way, how
	it went and what they answered."""
	righe = frappe.get_all(
		PROMEMORIA,
		fields=[
			"name",
			"appointment",
			"party_type",
			"party",
			"lead",
			"starts_on",
			"channel",
			"status",
			"reason",
			"sent_on",
			"answer",
			"cancelled",
			"second",
		],
		order_by="creation desc",
		limit=quanti,
	)
	due = bool(impostazioni().secondo)
	for riga in righe:
		riga["which"] = quale(riga.second, due)
		riga["person"] = (
			frappe.db.get_value("CRM Lead", riga.party, "lead_name")
			if riga.party_type == "CRM Lead"
			else None
		) or frappe.db.get_value(
			PARTECIPANTE, {"parent": riga.appointment, "party": riga.party}, "participant_name"
		)
		riga["when"] = quando(riga.starts_on)
	return righe
