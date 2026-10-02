# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Waiting lists on the site (design.md, "Cosa si aggiunge al CRM": "le liste
d'attesa"). The rules are `attese_regole`; here, the agenda and the messages.

- **Joining**: the desk puts a person on the list from their page or the list's
  own; the person from /prenota when no time suits or a class is full, and from
  their area (`attese_pubblico`, `crm.area.api`). One entry per person and service
  in the line: joining again changes it.
- **When something frees up** - a cancellation, a move, a seat in a class, a new
  shift - the engine that books (`availability.get_slots`, the classes' seats
  too) says which places are free, and they are offered to who waits, in their
  order, by WhatsApp, SMS or email with a link: to a few at once, and the first who
  confirms takes it. Every ten minutes the offers nobody answered go to the next
  ones; once an hour the whole list is looked at again.
- **Confirming books**, under the same lock as /prenota, once the engine says the
  place is still free: an appointment of the service, or a seat in the class. The
  desk offers a place of its choosing, or books it by hand.
- **Who sees it** follows the person and the agenda (`seguono.waiting_conditions`),
  with `agenda.attese`. What frees a place never waits for the list: the look
  runs after the save, in a job, and a message that cannot leave is written on the
  offer for the desk.
"""

from __future__ import annotations

import datetime
import hashlib
import secrets

import frappe
from frappe import _
from frappe.utils import (
	add_days,
	cint,
	escape_html,
	format_datetime,
	get_datetime,
	get_fullname,
	get_url,
	getdate,
	now_datetime,
)

from crm.permissions import livelli
from crm.posta.aspetto import pulsante
from crm.scheduling import attese_regole as R
from crm.scheduling.availability import get_slots, party_busy
from crm.scheduling.timeutils import UTC, day_bounds, from_system_naive, scheduling_tz, to_system_naive
from crm.telephony import sms as sms_del_centro

VOCE = "CRM Waiting List Entry"
OFFERTA = "CRM Waiting List Offer"
IMPOSTAZIONI = "CRM Waiting List Settings"
APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"
#: The whole list is looked at again once an hour at least.
CHIAVE_GIRO = "crm:attese:giro"
#: At most this many places, when the desk asks what there is.
POSTI_DA_MOSTRARE = 8


# ------------------------------------------------------------------ the centre's choices


def _si(valore, predefinito: bool) -> bool:
	"""A tick of a Single that may never have been saved: its default then."""
	return predefinito if valore is None else bool(cint(valore))


def impostazioni() -> frappe._dict:
	doc = frappe.get_cached_doc(IMPOSTAZIONI)
	return frappe._dict(
		automatiche=_si(doc.get("enabled"), True),
		per_volta=R.entro(doc.get("offers_at_once"), R.PER_VOLTA),
		ore=R.entro(doc.get("hours_to_answer"), R.ORE_PER_RISPONDERE),
		preavviso=max(cint(doc.get("min_notice_hours") if doc.get("min_notice_hours") is not None else 2), 0),
		giorni=R.entro(doc.get("days_ahead"), R.GIORNI_AVANTI),
		giorni_online=R.entro(doc.get("default_until_days"), R.GIORNI_IN_LISTA),
		online=_si(doc.get("online_join"), True),
		area=_si(doc.get("area_join"), True),
		whatsapp=_modello_whatsapp(doc.get("whatsapp_template")),
		# the centre's one sender (doc 52), the same as every other SMS of its
		sms=sms_del_centro.mittente(),
	)


def _modello_whatsapp(nome: str | None) -> str | None:
	if not nome or not frappe.db.exists("DocType", "WhatsApp Templates"):
		return None
	return nome if frappe.db.exists("WhatsApp Templates", nome) else None


def canali_offerti(conf=None) -> list[str]:
	conf = conf or impostazioni()
	return R.canali_offerti(bool(conf.whatsapp), bool(conf.sms))


# ------------------------------------------------------------------ time


def _utc(valore) -> datetime.datetime:
	return from_system_naive(get_datetime(valore))


def _locale(valore) -> datetime.datetime:
	"""A moment in the centre's own time, as its hours are written."""
	momento = valore if isinstance(valore, datetime.datetime) and valore.tzinfo else _utc(valore)
	return momento.astimezone(scheduling_tz())


def _oggi() -> datetime.date:
	return datetime.datetime.now(scheduling_tz()).date()


def quando(valore) -> str:
	"""A day and a time as a person reads them: "martedì 6 ottobre, 18:00"."""
	return format_datetime(_locale(valore).replace(tzinfo=None), "EEEE d MMMM, HH:mm")


def _entro_le(valore) -> str:
	"""An answer's deadline: the time, and the day when it is not today."""
	momento = _locale(valore)
	if momento.date() == _oggi():
		return momento.strftime("%H:%M")
	return format_datetime(momento.replace(tzinfo=None), "EEEE d MMMM, HH:mm")


# ------------------------------------------------------------------ secrets


def _segreto() -> str:
	"""A link: 192 random bits, shown once and kept as a hash."""
	return secrets.token_urlsafe(24)


def impronta(segreto: str) -> str:
	return hashlib.sha256(segreto.encode("utf-8")).hexdigest()


def link_della_pagina(segreto: str) -> str:
	return get_url(f"/lista-attesa/{segreto}")


# ------------------------------------------------------------------ the places


def _staff_di(testo: str | None) -> tuple[str, ...]:
	return tuple(u for u in (testo or "").split(",") if u)


def posto_di(riga) -> R.Posto:
	"""The place an offer is about."""
	inizio = _utc(riga.starts_on)
	return R.Posto(
		inizio,
		_utc(riga.ends_on) if riga.ends_on else inizio,
		_staff_di(riga.staff),
		riga.class_session or None,
	)


def _posto(slot) -> R.Posto:
	return R.Posto(
		slot.start,
		slot.end,
		tuple(slot.staff),
		slot.join_appointment,
		max(cint(slot.seats_left), 1),
	)


class Sguardo:
	"""One look at the list: the engine's free places, asked once per service,
	professional and places for the days looked at, and each person's own
	appointments."""

	def __init__(self, conf, primo: datetime.date, ultimo: datetime.date):
		self.conf = conf
		self.primo, self.ultimo = primo, ultimo
		self.adesso = datetime.datetime.now(UTC)
		self.da = self.adesso + datetime.timedelta(hours=conf.preavviso)
		self._liberi: dict[tuple, list] = {}

	def liberi(self, servizio: str, staff: str | None, posti: int) -> list:
		chiave = (servizio, staff or "", posti)
		if chiave not in self._liberi:
			try:
				self._liberi[chiave] = get_slots(
					servizio, self.primo, self.ultimo, staff=[staff] if staff else None, participants=posti
				)
			except Exception:
				# a service put wrong (no length, no staff) leaves its list waiting, not the others
				frappe.log_error(title=f"Waiting list: free places of {servizio}")
				self._liberi[chiave] = []
		return self._liberi[chiave]

	def posti(self, voce, giorni: set | None = None) -> list[R.Posto]:
		"""The places that fit an entry, earliest first: its days and hours, its
		professional or class, far enough ahead, and when the person is free."""
		giorni_voce = R.finestra(
			_oggi(),
			self.conf.giorni,
			getdate(voce.from_date) if voce.from_date else None,
			getdate(voce.until) if voce.until else None,
		)
		if not giorni_voce:
			return []
		fasce = R.fasce(voce.get("days") or [])
		adatti = []
		for slot in self.liberi(voce.service, voce.staff, cint(voce.seats) or 1):
			if voce.class_session and slot.join_appointment != voce.class_session:
				continue
			if slot.start < self.da:
				continue
			inizio, fine = _locale(slot.start), _locale(slot.end)
			if not giorni_voce[0] <= inizio.date() <= giorni_voce[1]:
				continue
			if giorni is not None and inizio.date() not in giorni:
				continue
			if not R.adatto(fasce, inizio, fine):
				continue
			adatti.append(slot)
		if not adatti:
			return []
		# not at a time the person is booked already, nor a seat in their own class
		persona = ("CRM Lead", voce.lead)
		occupato = party_busy([persona], adatti[0].start, adatti[-1].end + datetime.timedelta(hours=1))[
			persona
		]
		return [
			_posto(slot) for slot in adatti if not any(s < slot.end and slot.start < e for s, e in occupato)
		]


def _in_sospeso() -> list[R.Posto]:
	"""The places offered and waiting for an answer."""
	return [
		posto_di(riga)
		for riga in frappe.get_all(
			OFFERTA,
			filters={"parenttype": VOCE, "status": R.INVIATA},
			fields=["starts_on", "ends_on", "staff", "class_session"],
		)
	]


def _gia_offerti(voce) -> set[str]:
	"""The places this entry had and let go: never offered again."""
	return {
		posto_di(riga).chiave
		for riga in voce.get("offers") or []
		if riga.status in (R.RIFIUTATA, R.SENZA_RISPOSTA)
	}


def id_pubblico(nome: str) -> str:
	"""A class's id for a public page: its name would say how many appointments the
	centre books."""
	return hashlib.sha256(f"{frappe.local.site}:{nome}".encode()).hexdigest()[:12]


def sessioni_piene(servizio: str, dal: datetime.datetime, al: datetime.datetime) -> list[dict]:
	"""The classes of a service between two moments with no seat left: where one
	waits for a seat. The engine leaves them out of the free places."""
	from crm.utils import count_field

	doc = frappe.get_cached_doc("CRM Service", servizio)
	if cint(doc.max_participants) <= 1:
		return []
	righe = frappe.get_all(
		APPUNTAMENTO,
		filters={
			"service": servizio,
			"status": ("in", R.ATTIVI),
			"starts_on": ("between", [to_system_naive(dal), to_system_naive(al)]),
		},
		fields=["name", "starts_on", "ends_on"],
		order_by="starts_on asc",
	)
	if not righe:
		return []
	nomi = [r.name for r in righe]
	presenti = {
		r.parent: cint(r.total)
		for r in frappe.get_all(
			PARTECIPANTE,
			filters={"parenttype": APPUNTAMENTO, "parent": ("in", nomi), "status": ("!=", "Cancelled")},
			fields=["parent", count_field()],
			group_by="parent",
		)
	}
	sale: dict[str, list[str]] = {}
	for r in frappe.get_all(
		"CRM Appointment Resource",
		filters={"parenttype": APPUNTAMENTO, "parent": ("in", nomi)},
		fields=["parent", "resource"],
	):
		sale.setdefault(r.parent, []).append(r.resource)
	piene = []
	for r in righe:
		# the service's seats, narrowed by a room's own (`SlotFinder.seats_for`)
		posti = max(cint(doc.max_participants), 1)
		for sala in sale.get(r.name, []):
			sedie = cint(frappe.get_cached_value("CRM Resource", sala, "seats"))
			if sedie:
				posti = min(posti, sedie)
		if presenti.get(r.name, 0) >= posti:
			piene.append({"name": r.name, "start": _utc(r.starts_on), "end": _utc(r.ends_on), "seats": posti})
	return piene


def sessione_da_id(servizio: str, pubblico: str | None) -> str | None:
	"""The class a public id stands for, among the service's still to happen."""
	if not pubblico:
		return None
	for nome in frappe.get_all(
		APPUNTAMENTO,
		filters={"service": servizio, "status": ("in", R.ATTIVI), "starts_on": (">", now_datetime())},
		pluck="name",
		limit=500,
	):
		if id_pubblico(nome) == pubblico:
			return nome
	frappe.throw(_("This class is not on any more"))


# ------------------------------------------------------------------ looking at the list


def _fermo() -> bool:
	"""Nothing to do: installing, migrating, importing, or nobody waiting."""
	if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch or frappe.flags.in_import:
		return True
	return not frappe.db.exists(VOCE, {"status": ("in", R.APERTE)})


def chiudi_scadute() -> list[str]:
	"""The offers nobody answered in time, and the entries past their last day. The
	entries whose offer lapsed are back in the line: returns them."""
	adesso = now_datetime()
	tornate = []
	for riga in frappe.get_all(
		OFFERTA,
		filters={"parenttype": VOCE, "status": R.INVIATA, "expires_on": ("<", adesso)},
		fields=["name", "parent"],
	):
		frappe.db.set_value(OFFERTA, riga.name, "status", R.SENZA_RISPOSTA, update_modified=False)
		if di_nuovo_in_fila(riga.parent):
			tornate.append(riga.parent)
	# a filter on an empty date reads it as the first day there is: an entry with
	# no last day would expire the moment it joins
	for nome in frappe.get_all(
		VOCE,
		filters=[["status", "in", R.APERTE], ["until", "is", "set"], ["until", "<", _oggi()]],
		pluck="name",
	):
		_chiudi(frappe.get_doc(VOCE, nome), R.SCADUTA)
	return tornate


def di_nuovo_in_fila(nome: str) -> bool:
	"""An entry whose offer went is waiting again, unless its last day is gone."""
	doc = frappe.get_doc(VOCE, nome)
	if doc.status != R.PROPOSTA or any(r.status == R.INVIATA for r in doc.offers):
		return False
	if R.scaduta(getdate(doc.until) if doc.until else None, _oggi()):
		_chiudi(doc, R.SCADUTA)
		return False
	doc.db_set("status", R.IN_ATTESA, update_modified=False)
	return True


def _chiudi(doc, stato: str, appuntamento: str | None = None) -> None:
	"""Out of the line: booked, expired or taken off. An offer still waiting goes
	with it."""
	for riga in doc.offers:
		if riga.status == R.INVIATA:
			riga.status = R.SENZA_RISPOSTA if stato == R.SCADUTA else R.RIFIUTATA
			riga.answered_on = riga.answered_on or now_datetime()
	doc.status = stato
	doc.closed_on = now_datetime()
	if appuntamento:
		doc.booked_appointment = appuntamento
	doc.flags.ignore_permissions = True
	doc.save()


def cerca(giorni: list[str] | None = None, voci: list[str] | None = None) -> list[tuple[str, str]]:
	"""Looks at the list and offers what fits, in the line's order. ``giorni``
	narrows the look to the days something freed on; ``voci`` to some entries (one
	that just joined). Returns (entry, place) of what was offered."""
	conf = impostazioni()
	if not conf.automatiche or _fermo():
		return []
	chiudi_scadute()
	filtri = {"status": R.IN_ATTESA}
	if voci:
		filtri["name"] = ("in", list(voci))
	nomi = frappe.get_all(VOCE, filters=filtri, pluck="name", order_by="urgent desc, creation asc")
	if not nomi:
		return []
	oggi = _oggi()
	ultimo = oggi + datetime.timedelta(days=conf.giorni)
	solo = None
	if giorni:
		solo = {getdate(g) for g in giorni if oggi <= getdate(g) <= ultimo}
		if not solo:
			return []
		sguardo = Sguardo(conf, min(solo), max(solo))
	else:
		sguardo = Sguardo(conf, oggi, ultimo)
	attese = []
	for nome in nomi:
		doc = frappe.get_doc(VOCE, nome)
		attese.append(R.Attesa(nome, sguardo.posti(doc, solo), _gia_offerti(doc)))
	fatte = []
	for nome, posto in R.scegli(attese, _in_sospeso(), conf.per_volta):
		frappe.db.savepoint("crm_attesa_offerta")
		try:
			offri(frappe.get_doc(VOCE, nome), posto, conf=conf)
		except Exception:
			frappe.db.rollback(save_point="crm_attesa_offerta")
			frappe.clear_last_message()
			frappe.log_error(
				title="Waiting list: offer not made", reference_doctype=VOCE, reference_name=nome
			)
			continue
		fatte.append((nome, posto.chiave))
	return fatte


def ogni_dieci_minuti() -> None:
	"""The offers nobody answered go to the next ones; the whole list once an hour."""
	if _fermo():
		return
	tornate = chiudi_scadute()
	if tornate or not frappe.cache.get_value(CHIAVE_GIRO):
		frappe.cache.set_value(CHIAVE_GIRO, 1, expires_in_sec=3600)
		cerca()


def _cerca_in_un_job(**kwargs) -> None:
	frappe.enqueue(
		"crm.scheduling.attese.cerca",
		queue="short",
		enqueue_after_commit=True,
		now=frappe.in_test,
		**kwargs,
	)


# ------------------------------------------------------------------ what frees a place


def _istantanea(doc) -> dict | None:
	if not doc or not doc.get("starts_on"):
		return None
	return {
		"status": doc.get("status"),
		"inizio": _utc(doc.starts_on),
		"fine": _utc(doc.ends_on or doc.starts_on),
		"staff": [r.user for r in doc.get("staff") or [] if r.user],
		"risorse": [r.resource for r in doc.get("resources") or [] if r.resource],
		"persone": len([r for r in doc.get("participants") or [] if r.status != "Cancelled"]),
	}


def _giorno_di(doc) -> str:
	return _locale(doc.starts_on).date().isoformat()


def appuntamento_aggiornato(doc, method=None) -> None:
	"""`on_update` of an appointment: cancelled, moved, a seat freed - who waits
	for that day is looked at, after the save."""
	if _fermo():
		return
	prima = doc.get_doc_before_save()
	if R.libera(_istantanea(prima), _istantanea(doc), datetime.datetime.now(UTC)):
		_cerca_in_un_job(giorni=[_giorno_di(prima)])


def appuntamento_in_eliminazione(doc, method=None) -> None:
	"""`on_trash` of an appointment: the lists let go of it, or their links would
	keep it from going. Who waited for a seat in that class waits no more."""
	for nome in frappe.get_all(
		VOCE, filters={"class_session": doc.name, "status": ("in", R.APERTE)}, pluck="name"
	):
		_chiudi(frappe.get_doc(VOCE, nome), R.SCADUTA)
	for campo in ("class_session", "booked_appointment"):
		for nome in frappe.get_all(VOCE, filters={campo: doc.name}, pluck="name"):
			frappe.db.set_value(VOCE, nome, campo, None, update_modified=False)
	for campo in ("class_session", "appointment"):
		for nome in frappe.get_all(OFFERTA, filters={"parenttype": VOCE, campo: doc.name}, pluck="name"):
			frappe.db.set_value(OFFERTA, nome, campo, None, update_modified=False)


def appuntamento_eliminato(doc, method=None) -> None:
	"""`after_delete` of an appointment still to happen: its time is free, now that
	it is gone."""
	if _fermo():
		return
	if R.libera(_istantanea(doc), None, datetime.datetime.now(UTC)):
		_cerca_in_un_job(giorni=[_giorno_di(doc)])


def orari_cambiati(doc, method=None) -> None:
	"""A new shift, a service or a room changed: the whole list is looked at, once
	however many are saved together."""
	if _fermo():
		return
	frappe.enqueue(
		"crm.scheduling.attese.cerca",
		queue="short",
		enqueue_after_commit=True,
		now=frappe.in_test,
		job_id=f"crm-attese-{frappe.local.site}",
		deduplicate=not frappe.in_test,
	)


def cancella_con_la_persona(doc, method=None) -> None:
	"""`on_trash` of a person: what they waited for goes with them."""
	for nome in frappe.get_all(VOCE, filters={"lead": doc.name}, pluck="name"):
		frappe.delete_doc(VOCE, nome, ignore_permissions=True, force=True)
	for nome in frappe.get_all(VOCE, filters={"contact": doc.name}, pluck="name"):
		frappe.db.set_value(VOCE, nome, "contact", None, update_modified=False)


# ------------------------------------------------------------------ offering


def offri(voce, posto: R.Posto, da: str | None = None, conf=None) -> dict:
	"""A place to somebody waiting: the offer, its link, and the message. What
	cannot leave is written on the offer: the desk sees it and calls."""
	conf = conf or impostazioni()
	scade = R.scadenza(datetime.datetime.now(UTC), posto.inizio, conf.ore)
	if not scade:
		frappe.throw(_("This place starts too soon to wait for an answer: book it by hand"))
	if any(r.status == R.INVIATA for r in voce.offers):
		frappe.throw(_("An offer is waiting for this person's answer already"))
	segreto = _segreto()
	riga = voce.append(
		"offers",
		{
			"starts_on": to_system_naive(posto.inizio),
			"ends_on": to_system_naive(posto.fine),
			"staff": ",".join(posto.staff),
			"class_session": posto.sessione,
			"status": R.INVIATA,
			"sent_on": now_datetime(),
			"expires_on": to_system_naive(scade),
			"token_hash": impronta(segreto),
			"offered_by": da,
		},
	)
	voce.status = R.PROPOSTA
	voce.flags.ignore_permissions = True
	voce.save()
	canale, perche = manda_proposta(voce, riga, segreto, conf)
	riga.db_set({"channel": canale or "", "delivery": perche}, update_modified=False)
	return {"offer": riga.name, "channel": canale, "not_sent": perche}


def _destinatario(voce) -> tuple[str, str | None, str | None]:
	"""Who hears of an offer, and where: the email and the mobile given when
	joining, as a booking keeps them on its row - a family shares a phone, and the
	record found by it may hold none of theirs - else the person's own, or those
	of who booked for them."""
	from crm.api.whatsapp import numbers_of
	from crm.utils import stored_value, to_e164

	chi = voce.contact or voce.lead
	email = (voce.get("email") or "").strip() or stored_value("CRM Lead", chi, "email") or None
	numero = to_e164(voce.get("phone")) if voce.get("phone") else None
	if not numero:
		numeri = numbers_of("CRM Lead", chi)
		numero = numeri[0] if numeri else None
	return chi, email, numero


def _nome_servizio(servizio: str) -> str:
	return frappe.db.get_value("CRM Service", servizio, "service_name") or servizio


def _nomi(staff) -> str:
	return ", ".join(get_fullname(u) for u in staff if u)


def manda_proposta(voce, riga, segreto: str, conf=None) -> tuple[str | None, str | None]:
	"""The message of an offer by the channel the person chose, else by email.
	Returns the channel it left by, or why it did not."""
	from crm.moduli.richieste import nome_del_centro

	conf = conf or impostazioni()
	chi, email, numero = _destinatario(voce)
	offerti = canali_offerti(conf)
	# a STOP to the centre's SMS is heard here too (doc 52): the offer goes another way
	fermato = sms_del_centro.ha_fermato("CRM Lead", chi)
	if fermato:
		offerti = [canale for canale in offerti if canale != R.SMS]
	canali = R.come_mandare(voce.channel, offerti, bool(email), bool(numero))
	if not canali:
		if fermato and numero:
			return None, _("They wrote STOP to the centre's SMS and have no email on file: call them")
		return None, _("No email or mobile on file: call them")
	testo = {
		"centro": nome_del_centro() or _("the centre"),
		"nome": (frappe.db.get_value("CRM Lead", chi, "first_name") or "").strip()
		or frappe.db.get_value("CRM Lead", chi, "lead_name")
		or "",
		"servizio": _nome_servizio(voce.service),
		"quando": quando(riga.starts_on),
		"con": _nomi(_staff_di(riga.staff)),
		"entro": _entro_le(riga.expires_on),
		"link": link_della_pagina(segreto),
		"per": voce.lead_name if voce.contact else "",
	}
	errori = []
	for canale in canali:
		try:
			if canale == R.WHATSAPP:
				_per_whatsapp(chi, numero, conf.whatsapp, testo)
			elif canale == R.SMS:
				_per_sms(chi, numero, conf.sms, testo)
			else:
				_per_email(voce, email, testo)
			return canale, None
		except Exception as errore:
			frappe.clear_last_message()
			frappe.log_error(
				title=f"Waiting list: offer not sent by {canale}",
				reference_doctype=VOCE,
				reference_name=voce.name,
			)
			errori.append(f"{canale}: {errore}")
	return None, "; ".join(errori)[:500]


def _testo_breve(testo: dict) -> str:
	return _("{0}: a place has freed up for {1}, {2}. It is yours if you confirm by {3}: {4}").format(
		testo["centro"], testo["servizio"], testo["quando"], testo["entro"], testo["link"]
	)


def _per_sms(chi: str, numero: str, mittente: str, testo: dict) -> None:
	from crm.api.sms import create_sms, deliver_via_twilio

	doc = create_sms(
		type="Outgoing",
		from_number=mittente,
		to=numero,
		message=_testo_breve(testo),
		reference_doctype="CRM Lead",
		reference_name=chi,
	)
	deliver_via_twilio(doc)
	if doc.status == "Failed":
		raise frappe.ValidationError(doc.error_message or _("The SMS did not leave"))


def _per_whatsapp(chi: str, numero: str, modello: str, testo: dict) -> None:
	from crm.api.whatsapp import manda_modello

	manda_modello(
		"CRM Lead",
		chi,
		numero,
		modello,
		R.variabili(
			_quante_variabili(modello), testo["nome"], testo["servizio"], testo["quando"], testo["link"]
		),
	)


def _quante_variabili(modello: str) -> int:
	import re

	corpo = frappe.db.get_value("WhatsApp Templates", modello, "template") or ""
	return len(set(re.findall(r"{{\s*(\d+)\s*}}", corpo)))


def _per_email(voce, email: str, testo: dict) -> None:
	from crm.moduli.richieste import _subito

	esc = escape_html
	righe = [
		f"<p>{esc(_('Hi {0},').format(testo['nome']))}</p>" if testo["nome"] else "",
		f"<p>{esc(_('a place you were waiting for has freed up at {0}:').format(testo['centro']))}</p>",
		f"<p><b>{esc(testo['servizio'])}</b><br>{esc(testo['quando'])}"
		+ (f"<br>{esc(_('With {0}').format(testo['con']))}" if testo["con"] else "")
		+ (f"<br>{esc(_('For {0}').format(testo['per']))}" if testo["per"] else "")
		+ "</p>",
		f"<p>{esc(_('It is yours if you confirm by {0}; then it goes to the next person waiting.').format(testo['entro']))}</p>",
		pulsante(testo["link"], _("Confirm or decline")),
		f'<p class="text-muted text-small">{esc(_("From the same page you can leave the waiting list."))}</p>',
	]
	posta = frappe.sendmail(
		recipients=[email],
		subject=_("A place has freed up: {0}, {1}").format(testo["servizio"], testo["quando"]),
		header=_("A place has freed up"),
		with_container=True,
		message="".join(righe),
		reference_doctype=VOCE,
		reference_name=voce.name,
	)
	if posta:
		# the place waits a couple of hours: out now, not at the queue's next turn
		frappe.db.after_commit.add(lambda: _subito(posta))


# ------------------------------------------------------------------ confirming


def ancora_libero(voce, riga):
	"""The engine's slot for an offer, if the place is still free: the same class,
	or the same time with the same professional - with another one who does the
	service, if the person asked for nobody in particular."""
	inizio = _utc(riga.starts_on)
	giorno = _locale(inizio).date()
	posti = cint(voce.seats) or 1
	staff = list(_staff_di(riga.staff))

	def trova(con):
		for slot in get_slots(voce.service, giorno, giorno, staff=con or None, participants=posti):
			if riga.class_session:
				if slot.join_appointment == riga.class_session:
					return slot
			elif slot.start == inizio:
				return slot
		return None

	slot = trova(staff)
	if not slot and not riga.class_session and not voce.staff and staff:
		slot = trova(None)
	return slot


def _righe_partecipanti(voce, segreto: str, online: bool) -> list[dict]:
	_chi, email, numero = _destinatario(voce)
	righe = [
		{
			"party_type": "CRM Lead",
			"party": voce.lead,
			"participant_name": voce.lead_name or voce.lead,
			"booked_by": voce.contact or None,
			"email": email,
			"phone": numero,
			"status": "Booked",
			"access_token": segreto,
			"booked_online": 1 if online else 0,
		}
	]
	for numero in range(2, (cint(voce.seats) or 1) + 1):
		righe.append(
			{
				"party_type": "CRM Lead",
				"participant_name": _("{0} — guest {1}").format(voce.lead_name, numero - 1),
				"status": "Booked",
				"access_token": segreto,
				"booked_online": 1 if online else 0,
			}
		)
	return righe


def prenota(voce, slot, fonte: str, ignora_permessi: bool = True):
	"""The appointment of a place: a seat in the class, or a new one of the
	service, confirmed. Booked by the person themselves it is an online booking;
	by the desk, the desk's own - with its permissions."""
	online = fonte != R.DAL_BANCO
	segreto = frappe.generate_hash(length=32)
	righe = _righe_partecipanti(voce, segreto, online)
	if slot.join_appointment:
		appuntamento = frappe.get_doc(APPUNTAMENTO, slot.join_appointment)
		for riga in righe:
			appuntamento.append("participants", riga)
		appuntamento.save(ignore_permissions=ignora_permessi)
	else:
		appuntamento = frappe.get_doc(
			{
				"doctype": APPUNTAMENTO,
				"service": voce.service,
				"status": "Confirmed",
				"starts_on": to_system_naive(slot.start),
				"ends_on": to_system_naive(slot.end),
				"staff": [{"user": u, "required": 1} for u in slot.staff],
				"resources": slot.resources,
				"participants": righe,
				"source": "Online" if online else "Internal",
				"location": frappe.db.get_value("CRM Service", voce.service, "location") or None,
			}
		)
		appuntamento.insert(ignore_permissions=ignora_permessi)
	return appuntamento, segreto


def conferma(voce, riga, fonte: str = R.ONLINE) -> dict:
	"""The person says yes. Booked if the place is still free; else the offer is
	taken, the entry goes back in the line and the answer says so - nothing is
	thrown, so what happened stays written."""
	if riga.status != R.INVIATA:
		return {"result": "answered", "status": riga.status}
	if get_datetime(riga.expires_on) < now_datetime():
		riga.db_set({"status": R.SENZA_RISPOSTA, "answered_on": now_datetime()}, update_modified=False)
		di_nuovo_in_fila(voce.name)
		return {"result": "expired"}
	# the same lock as /prenota: the check below must not race another booking
	frappe.db.get_value("CRM Service", voce.service, "name", for_update=True)
	slot = ancora_libero(voce, riga)
	if not slot:
		_presa(voce, riga)
		return {"result": "taken"}
	appuntamento, segreto = prenota(voce, slot, fonte)
	riga.status = R.ACCETTATA
	riga.answered_on = now_datetime()
	riga.appointment = appuntamento.name
	_chiudi(voce, R.PRENOTATA, appuntamento.name)
	_presa_dagli_altri(voce.name, _posto(slot) if not slot.join_appointment else posto_di(riga), appuntamento)
	_conferma_al_cliente(voce, appuntamento, segreto)
	from crm.api.service_booking import notify_staff

	notify_staff(appuntamento, _("Booked from the waiting list"))
	return {"result": "booked", "appointment": appuntamento.name}


def _presa(voce, riga) -> None:
	"""The place went to somebody else: the offer says so, the entry waits again."""
	riga.db_set({"status": R.PRESA, "answered_on": now_datetime()}, update_modified=False)
	if di_nuovo_in_fila(voce.name):
		_cerca_in_un_job(voci=[voce.name])


def _presa_dagli_altri(nome: str, posto: R.Posto, appuntamento) -> None:
	"""A place booked: the offers of it to the others are taken - a class's only
	once its seats are gone - and those entries wait again."""
	if (
		posto.sessione
		or cint(frappe.db.get_value("CRM Service", appuntamento.service, "max_participants")) > 1
	):
		sessione = appuntamento.name
		occupati = len([r for r in appuntamento.participants if r.status != "Cancelled"])
		posti = cint(frappe.db.get_value("CRM Service", appuntamento.service, "max_participants")) or 1
		if occupati < posti:
			return
		posto = R.Posto(posto.inizio, posto.fine, posto.staff, sessione)
	tornate = []
	for riga in frappe.get_all(
		OFFERTA,
		filters={"parenttype": VOCE, "status": R.INVIATA, "parent": ("!=", nome)},
		fields=["name", "parent", "starts_on", "ends_on", "staff", "class_session"],
	):
		altro = posto_di(riga)
		if R.si_toccano(altro, posto) or (
			posto.sessione and altro.inizio == posto.inizio and set(altro.staff) & set(posto.staff)
		):
			frappe.db.set_value(
				OFFERTA, riga.name, {"status": R.PRESA, "answered_on": now_datetime()}, update_modified=False
			)
			if di_nuovo_in_fila(riga.parent):
				tornate.append(riga.parent)
	if tornate:
		_cerca_in_un_job(voci=tornate)


def rifiuta(voce, riga) -> None:
	"""No thanks: the place goes on to the next ones, the person keeps their place
	in the line."""
	if riga.status != R.INVIATA:
		return
	riga.db_set({"status": R.RIFIUTATA, "answered_on": now_datetime()}, update_modified=False)
	di_nuovo_in_fila(voce.name)
	_cerca_in_un_job(giorni=[_locale(riga.starts_on).date().isoformat()])


def togli(voce) -> None:
	"""Off the list: the person no longer waits. An offer still waiting goes back."""
	if voce.status not in R.APERTE:
		return
	aveva = [r for r in voce.offers if r.status == R.INVIATA]
	_chiudi(voce, R.TOLTA)
	if aveva:
		_cerca_in_un_job(giorni=[_locale(r.starts_on).date().isoformat() for r in aveva])


def _conferma_al_cliente(voce, appuntamento, segreto: str) -> None:
	"""The email of the booking, to whoever hears of it: never stops the booking."""
	from crm.api.service_booking import _calendar_links, ics_file, manage_url
	from crm.moduli.richieste import nome_del_centro
	from crm.scheduling.availability import settings

	_chi, email, _numero = _destinatario(voce)
	if not email:
		return
	try:
		servizio = _nome_servizio(voce.service)
		inizio, fine = _utc(appuntamento.starts_on), _utc(appuntamento.ends_on)
		esc = escape_html
		righe = [f"<p><b>{esc(servizio)}</b><br>{esc(quando(inizio))}</p>"]
		if voce.contact:
			righe.append(f"<p>{esc(_('The appointment is for {0}.').format(voce.lead_name))}</p>")
		staff = [r.user for r in appuntamento.staff]
		if staff:
			righe.append(f"<p>{esc(_('With {0}').format(_nomi(staff)))}</p>")
		if appuntamento.location:
			righe.append(f"<p>{esc(appuntamento.location)}</p>")
		# the booking page moves or cancels it, where the centre books online
		online = cint(settings().get("online_booking_enabled")) and cint(
			frappe.db.get_value("CRM Service", voce.service, "bookable_online")
		)
		if online:
			righe.append(pulsante(manage_url(segreto), _("Manage your booking")))
		link = _calendar_links(servizio, inizio, fine, appuntamento.location)
		righe.append(
			f'<p><a href="{esc(link["google"])}">{esc(_("Add to Google Calendar"))}</a> · '
			f'<a href="{esc(link["outlook"])}">{esc(_("Add to Outlook"))}</a></p>'
		)
		centro = nome_del_centro()
		if centro:
			righe.append(f"<p>{esc(centro)}</p>")
		frappe.sendmail(
			recipients=[email],
			subject=_("Your appointment is booked — {0}, {1}").format(servizio, quando(inizio)),
			header=_("Your appointment is booked"),
			with_container=True,
			message="".join(righe),
			attachments=[ics_file(segreto, servizio, inizio, fine, appuntamento.location)],
			reference_doctype=APPUNTAMENTO,
			reference_name=appuntamento.name,
		)
	except Exception:
		frappe.log_error(
			title="Waiting list: booking email not sent", reference_doctype=VOCE, reference_name=voce.name
		)


# ------------------------------------------------------------------ joining


def entra(
	lead: str,
	servizio: str,
	*,
	staff: str | None = None,
	lezione: str | None = None,
	posti: int = 1,
	righe: list | None = None,
	dal=None,
	fino=None,
	canale: str | None = None,
	contatto: str | None = None,
	fonte: str = R.DAL_BANCO,
	urgente: bool = False,
	note: str | None = None,
	email: str | None = None,
	telefono: str | None = None,
	ignora_permessi: bool = False,
):
	"""On the list, or the entry already there changed: one per person and service
	(and class). ``email`` and ``telefono`` are the ones given when joining, where
	the offers go. Returns the entry."""
	nome = frappe.db.get_value(
		VOCE,
		{
			"lead": lead,
			"service": servizio,
			"class_session": lezione or ("is", "not set"),
			"status": ("in", R.APERTE),
		},
		"name",
	)
	doc = frappe.get_doc(VOCE, nome) if nome else frappe.new_doc(VOCE)
	if lezione:
		# a seat in a class is waited for until the class
		fino = _locale(frappe.db.get_value(APPUNTAMENTO, lezione, "starts_on")).date()
		righe, dal = [], None
	if doc.is_new():
		doc.lead = lead
		doc.service = servizio
		doc.class_session = lezione or None
		doc.source = fonte
		doc.status = R.IN_ATTESA
	doc.staff = staff or None
	doc.seats = cint(posti) or 1
	doc.set("days", righe or [])
	doc.from_date = dal or None
	doc.until = fino or None
	doc.channel = canale if canale in canali_offerti() else R.EMAIL
	doc.contact = contatto or None
	if email or telefono:
		doc.email = email or None
		doc.phone = telefono or None
	if fonte == R.DAL_BANCO:
		doc.urgent = 1 if urgente else 0
		doc.notes = (note or "").strip() or None
	doc.flags.ignore_permissions = ignora_permessi
	doc.save() if not doc.is_new() else doc.insert()
	return doc


def segreto_della_voce(doc) -> str:
	"""A new link to the entry's page, for the person to see it or leave: the old
	one stops working."""
	segreto = _segreto()
	doc.db_set("token_hash", impronta(segreto), update_modified=False)
	return segreto


def dopo_l_ingresso(nome: str) -> None:
	"""A new entry is looked at at once: a place may be free for it already."""
	_cerca_in_un_job(voci=[nome])


# ------------------------------------------------------------------ reading


def descrivi(doc) -> dict:
	"""An entry for the screens: the person, what they wait for, their days, the
	offer waiting and the last ones."""
	offerte = sorted(doc.offers, key=lambda r: get_datetime(r.sent_on or r.creation), reverse=True)
	in_corso = next((r for r in offerte if r.status == R.INVIATA), None)
	return {
		"name": doc.name,
		"lead": doc.lead,
		"lead_name": doc.lead_name,
		"service": doc.service,
		"service_name": _nome_servizio(doc.service),
		"staff": doc.staff,
		"staff_name": get_fullname(doc.staff) if doc.staff else None,
		"class_session": doc.class_session,
		"class_starts_on": str(frappe.db.get_value(APPUNTAMENTO, doc.class_session, "starts_on"))
		if doc.class_session
		else None,
		"seats": cint(doc.seats) or 1,
		"status": doc.status,
		"urgent": cint(doc.urgent),
		"from_date": str(doc.from_date) if doc.from_date else None,
		"until": str(doc.until) if doc.until else None,
		"days": [
			{"workday": r.workday, "start_time": str(r.start_time), "end_time": str(r.end_time)}
			for r in doc.days
		],
		"choice": R.scelte_da(doc.days),
		"channel": doc.channel,
		"email": doc.get("email"),
		"phone": doc.get("phone"),
		"contact": doc.contact,
		"contact_name": frappe.db.get_value("CRM Lead", doc.contact, "lead_name") if doc.contact else None,
		"source": doc.source,
		"notes": doc.notes,
		"since": str(doc.creation),
		"booked_appointment": doc.booked_appointment,
		"booked_starts_on": str(frappe.db.get_value(APPUNTAMENTO, doc.booked_appointment, "starts_on"))
		if doc.booked_appointment
		else None,
		"offer": _offerta(in_corso) if in_corso else None,
		"offers": [_offerta(r) for r in offerte[:10]],
	}


def _offerta(riga) -> dict:
	return {
		"name": riga.name,
		"starts_on": str(riga.starts_on),
		"ends_on": str(riga.ends_on) if riga.ends_on else None,
		"staff": list(_staff_di(riga.staff)),
		"staff_name": _nomi(_staff_di(riga.staff)),
		"class_session": riga.class_session,
		"status": riga.status,
		"channel": riga.channel,
		"not_sent": riga.delivery,
		"sent_on": str(riga.sent_on) if riga.sent_on else None,
		"expires_on": str(riga.expires_on) if riga.expires_on else None,
		"answered_on": str(riga.answered_on) if riga.answered_on else None,
		"offered_by": get_fullname(riga.offered_by) if riga.offered_by else None,
		"appointment": riga.appointment,
	}


# ------------------------------------------------------------------ the desk


def _vede() -> None:
	livelli.verifica("agenda.attese")


def _la_voce(nome: str):
	_vede()
	doc = frappe.get_doc(VOCE, nome)
	doc.check_permission("read")
	return doc


def _scrive(doc) -> None:
	doc.check_permission("write")


def _potere() -> dict:
	return {
		"can_manage": livelli.puo("agenda.attese"),
		"can_book": livelli.puo("agenda.prenota"),
		"channels": canali_offerti(),
	}


@frappe.whitelist()
def get_entries(lead: str) -> dict:
	"""The person's entries: in the line first, then the last ones closed."""
	_vede()
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	voci = [
		descrivi(frappe.get_doc(VOCE, nome))
		for nome in frappe.get_list(
			VOCE, filters={"lead": lead}, pluck="name", order_by="creation desc", limit=20
		)
	]
	voci.sort(key=lambda v: (v["status"] not in R.APERTE, v["since"] if v["status"] in R.APERTE else ""))
	return {"entries": voci, **_potere()}


@frappe.whitelist()
def get_waiting_list(service: str | None = None, staff: str | None = None, closed: int = 0) -> dict:
	"""Who waits, in the line's order: the urgent first, then who joined first.
	``closed`` shows the last ones out of the line instead."""
	_vede()
	filtri = {"status": ("not in", R.APERTE) if cint(closed) else ("in", R.APERTE)}
	if service:
		filtri["service"] = service
	if staff:
		filtri["staff"] = staff
	ordine = "modified desc" if cint(closed) else "urgent desc, creation asc"
	nomi = frappe.get_list(
		VOCE, filters=filtri, pluck="name", order_by=ordine, limit=200 if not cint(closed) else 50
	)
	voci = [descrivi(frappe.get_doc(VOCE, nome)) for nome in nomi]
	return {"entries": voci, **_potere()}


@frappe.whitelist()
def get_entry(name: str) -> dict:
	return {**descrivi(_la_voce(name)), **_potere()}


def _date(valore):
	return getdate(valore) if valore else None


@frappe.whitelist(methods=["POST"])
def save_entry(lead: str, data: dict | str, name: str | None = None) -> dict:
	"""An entry, new or put right, from the desk."""
	_vede()
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = _la_voce(name)
		_scrive(doc)
		if doc.lead != lead:
			frappe.throw(_("This entry belongs to somebody else"))
		if doc.status not in R.APERTE:
			frappe.throw(_("This entry is out of the line: add a new one"))
	righe = dati.get("days")
	if righe is None:
		righe = R.righe_da(dati.get("weekdays") or [], dati.get("parts") or [])
	doc = entra(
		lead,
		dati.get("service"),
		staff=dati.get("staff") or None,
		lezione=dati.get("class_session") or None,
		posti=cint(dati.get("seats")) or 1,
		righe=righe,
		dal=_date(dati.get("from_date")),
		fino=_date(dati.get("until")),
		canale=dati.get("channel"),
		contatto=dati.get("contact") or None,
		fonte=R.DAL_BANCO,
		urgente=bool(cint(dati.get("urgent"))),
		note=dati.get("notes"),
	)
	if not name:
		dopo_l_ingresso(doc.name)
	return get_entry(doc.name)


@frappe.whitelist(methods=["POST"])
def remove_entry(name: str) -> dict:
	"""Off the list, from the desk: the person no longer waits."""
	doc = _la_voce(name)
	_scrive(doc)
	togli(doc)
	return get_entry(name)


def _dalla_scrivania(doc, start: str, staff: str | None, class_session: str | None):
	"""The slot of a place the desk picked among the free ones."""
	from crm.scheduling.timeutils import parse_utc

	inizio = parse_utc(start)
	giorno = _locale(inizio).date()
	for slot in get_slots(
		doc.service, giorno, giorno, staff=[staff] if staff else None, participants=cint(doc.seats) or 1
	):
		if class_session:
			if slot.join_appointment == class_session:
				return slot
		elif slot.start == inizio and not slot.join_appointment and (not staff or staff in slot.staff):
			return slot
		elif slot.start == inizio and slot.join_appointment and not staff:
			return slot
	frappe.throw(_("This place is no longer free"))


@frappe.whitelist()
def get_full_classes(service: str) -> list[dict]:
	"""The classes of a service with no seat left, in the days the list looks at:
	one waits for a seat in one of them."""
	_vede()
	conf = impostazioni()
	adesso = datetime.datetime.now(UTC)
	return [
		{
			"name": lezione["name"],
			"starts_on": str(to_system_naive(lezione["start"])),
			"seats": lezione["seats"],
		}
		for lezione in sessioni_piene(service, adesso, adesso + datetime.timedelta(days=conf.giorni))
	]


@frappe.whitelist()
def find_places(name: str) -> dict:
	"""What is free for an entry now, earliest first, and how many are being
	offered each place already."""
	doc = _la_voce(name)
	conf = impostazioni()
	oggi = _oggi()
	sguardo = Sguardo(conf, oggi, oggi + datetime.timedelta(days=conf.giorni))
	# the desk may offer or book what is closer than the automatic offers
	sguardo.da = datetime.datetime.now(UTC)
	aperte = _in_sospeso()
	posti = []
	for posto in sguardo.posti(doc)[:POSTI_DA_MOSTRARE]:
		posti.append(
			{
				"start": posto.inizio.isoformat(),
				"end": posto.fine.isoformat(),
				"starts_on": str(to_system_naive(posto.inizio)),
				"staff": list(posto.staff),
				"staff_name": _nomi(posto.staff),
				"class_session": posto.sessione,
				"seats_left": posto.capienza,
				"offered": sum(1 for altro in aperte if R.si_toccano(altro, posto)),
				"can_offer": bool(R.scadenza(datetime.datetime.now(UTC), posto.inizio, conf.ore)),
			}
		)
	return {"places": posti, "days_ahead": conf.giorni}


@frappe.whitelist(methods=["POST"])
def offer_place(name: str, start: str, staff: str | None = None, class_session: str | None = None) -> dict:
	"""The desk offers a place of its choosing: the same message and link as the
	ones that leave by themselves."""
	doc = _la_voce(name)
	_scrive(doc)
	if doc.status != R.IN_ATTESA:
		frappe.throw(_("Only somebody waiting gets an offer: one is waiting for an answer already"))
	slot = _dalla_scrivania(doc, start, staff, class_session)
	esito = offri(doc, _posto(slot), da=frappe.session.user)
	return {**get_entry(name), "sent": esito}


@frappe.whitelist(methods=["POST"])
def book_place(name: str, start: str, staff: str | None = None, class_session: str | None = None) -> dict:
	"""The desk books a place for the person, as it would on the calendar - with its
	own permissions - and the entry is done."""
	doc = _la_voce(name)
	_scrive(doc)
	if doc.status not in R.APERTE:
		frappe.throw(_("This entry is out of the line"))
	livelli.verifica("agenda.prenota")
	frappe.db.get_value("CRM Service", doc.service, "name", for_update=True)
	slot = _dalla_scrivania(doc, start, staff, class_session)
	appuntamento, _segreto_partecipante = prenota(doc, slot, R.DAL_BANCO, ignora_permessi=False)
	for riga in doc.offers:
		if riga.status == R.INVIATA:
			riga.status = R.PRESA
			riga.answered_on = now_datetime()
	_chiudi(doc, R.PRENOTATA, appuntamento.name)
	_presa_dagli_altri(doc.name, _posto(slot), appuntamento)
	return {**get_entry(name), "appointment": appuntamento.name}


# ------------------------------------------------------------------ the settings


@frappe.whitelist()
def get_settings() -> dict:
	livelli.verifica("agenda.configura")
	conf = impostazioni()
	modelli = []
	if frappe.db.exists("DocType", "WhatsApp Templates"):
		modelli = frappe.get_all(
			"WhatsApp Templates",
			filters={"status": "APPROVED"},
			fields=["name", "template_name", "template"],
			order_by="template_name asc",
		)
	doc = frappe.get_cached_doc(IMPOSTAZIONI)
	return {
		"enabled": int(conf.automatiche),
		"offers_at_once": conf.per_volta,
		"hours_to_answer": conf.ore,
		"min_notice_hours": conf.preavviso,
		"days_ahead": conf.giorni,
		"default_until_days": conf.giorni_online,
		"online_join": int(conf.online),
		"area_join": int(conf.area),
		"whatsapp_template": doc.get("whatsapp_template"),
		"sms_sender": conf.sms,
		"templates": modelli,
		"twilio": bool(cint(frappe.db.get_single_value("CRM Twilio Settings", "enabled"))),
	}


@frappe.whitelist(methods=["POST"])
def save_settings(data: dict | str) -> dict:
	livelli.verifica("agenda.configura")
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc(IMPOSTAZIONI)
	for campo in (
		"enabled",
		"offers_at_once",
		"hours_to_answer",
		"min_notice_hours",
		"days_ahead",
		"default_until_days",
		"online_join",
		"area_join",
		"whatsapp_template",
	):
		if campo in dati:
			doc.set(campo, dati[campo])
	doc.save()
	return get_settings()


# ------------------------------------------------------------------ for the person


def della_persona(persona: str) -> list[dict]:
	"""For the person's own area: what they wait for, and the offer waiting for
	their answer - no notes, nobody else's names but the professional's."""
	fatto = []
	for nome in frappe.get_all(
		VOCE, filters={"lead": persona, "status": ("in", R.APERTE)}, pluck="name", order_by="creation asc"
	):
		dati = descrivi(frappe.get_doc(VOCE, nome))
		offerta = dati["offer"]
		fatto.append(
			{
				"name": dati["name"],
				"service": dati["service_name"],
				"staff": dati["staff_name"],
				"class_starts_on": dati["class_starts_on"],
				"choice": dati["choice"],
				"days": dati["days"],
				"until": dati["until"],
				"status": dati["status"],
				"offer": {
					"starts_on": offerta["starts_on"],
					"staff": offerta["staff_name"],
					"expires_on": offerta["expires_on"],
					"can_answer": bool(offerta["expires_on"])
					and get_datetime(offerta["expires_on"]) > now_datetime(),
				}
				if offerta
				else None,
			}
		)
	return fatto


def per_giorno(giorno: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
	return day_bounds(giorno, scheduling_tz())


def fino_predefinito(conf=None) -> datetime.date:
	conf = conf or impostazioni()
	return getdate(add_days(_oggi(), conf.giorni_online))
