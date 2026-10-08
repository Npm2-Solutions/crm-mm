# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the client area shows: only the session's people, derived on the server.

Every call takes a ``person`` and first checks it is one of the session's
(`accesso.persone_di`): a person the session was not given is a refusal, never an
empty answer that could be probed. The rest reads the CRM as the centre does and
gives the person only what is theirs to see:

- **appointments**, upcoming and past, each with the booking page's own link to
  move or cancel it by the centre's rules, the cycles of sessions and the
  subscriptions going on (`crm.scheduling.abbonamenti`); «I'm here» around the
  time of one (`check_in`), which fills the desk's waiting room;
- **the waiting lists**: what the person waits for, the place offered to answer,
  joining one and leaving it (`crm.scheduling.attese`);
- **the forms** to fill before the next one, opened without another code;
- **invoices**, with their PDF;
- **the places other modules add** (`sezioni`): the clinic's documents, plans and
  care plans answer from the clinic.

The centre's preview (`anteprima`) goes through the same calls: the ones that only
read say so (`anche_in_anteprima`), every other one answers that it is a preview.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_datetime, now_datetime

from crm.area import accesso, anteprima, sezioni
from crm.area import prenota_regole as P
from crm.scheduling import abbonamenti, attese, cicli, visite_online
from crm.scheduling import arrivi_regole as A
from crm.scheduling import attese_regole as R
from crm.scheduling import visite_online_regole as V


def _utente(anche_in_anteprima: bool = False) -> str:
	"""Who is in the area; the centre's preview too, for a call that only reads."""
	utente = frappe.session.user
	if anteprima.in_anteprima():
		if not anche_in_anteprima:
			anteprima.rifiuta()
		return utente
	if utente == "Guest" or not accesso.entra_nell_area(utente):
		frappe.throw(_("Enter the area first"), frappe.PermissionError)
	return utente


def _mia(person: str, anche_in_anteprima: bool = False) -> dict:
	"""The person, if the session was given their area: in the centre's preview,
	the person previewed, for a call that only reads."""
	vista = anteprima.in_anteprima()
	if vista:
		if not anche_in_anteprima:
			anteprima.rifiuta()
		if person != vista.lead:
			frappe.throw(_("This is not your area"), frappe.PermissionError)
		return frappe._dict(lead=vista.lead, lead_name=vista.lead_name, relation=accesso.SE_STESSO)
	utente = _utente()
	for riga in accesso.persone_di(utente):
		if riga.lead == person:
			return riga
	frappe.throw(_("This is not your area"), frappe.PermissionError)


@frappe.whitelist()
def get_me() -> dict:
	"""Who is in, whose areas they see, and the centre's name."""
	from crm.area import avvisi, chat, messaggi
	from crm.moduli.richieste import nome_del_centro

	utente = _utente(anche_in_anteprima=True)
	vista = anteprima.in_anteprima()
	if vista:
		# the centre looks: the person's area, and nobody was seen in it
		persone = [frappe._dict(lead=vista.lead, lead_name=vista.lead_name, relation=accesso.SE_STESSO)]
	else:
		persone = accesso.persone_di(utente)
		frappe.db.set_value(
			accesso.ACCESSO,
			{"user": utente, "enabled": 1},
			"last_seen_on",
			now_datetime(),
			update_modified=False,
		)
	return {
		"user": utente,
		"full_name": frappe.utils.get_fullname(utente),
		"people": [
			{
				"name": p.lead,
				"lead_name": p.lead_name,
				"relation": p.relation,
				"unread": messaggi.da_leggere(p.lead),
				# the places other modules add, for this person: the clinic's plans
				# show to who follows one now
				"sections": sezioni.per_persona(p.lead),
			}
			for p in persone
		],
		"centre": nome_del_centro(),
		# the chat about hours and bookings, where the centre turned it on
		"chat": chat.attiva(),
		# news also by WhatsApp or SMS, where the centre offers them
		"notices": bool(avvisi.offerti()),
		# the centre's preview: whose area, read only
		"preview": {"lead": vista.lead, "lead_name": vista.lead_name} if vista else None,
	}


# ------------------------------------------------------------------ appointments


def _link_di_gestione(riga) -> str | None:
	"""The booking page's own link for this seat: made the first time it is needed."""
	from crm.api.service_booking import manage_url

	token = riga.access_token
	if not token:
		token = secrets.token_urlsafe(24)
		frappe.db.set_value("CRM Appointment Participant", riga.name, "access_token", token)
		# asked with a GET too: the link has to last
		frappe.local.flags.commit = True
	return manage_url(token)


@frappe.whitelist()
def get_appointments(person: str) -> dict:
	"""The person's appointments: the next ones, and the last ones."""
	_mia(person, anche_in_anteprima=True)
	vista = anteprima.in_anteprima()
	righe = frappe.get_all(
		"CRM Appointment Participant",
		filters={"parenttype": "CRM Appointment", "party_type": "CRM Lead", "party": person},
		fields=["name", "parent", "status", "access_token"],
	)
	adesso = now_datetime()
	prossimi, passati = [], []
	# what was booked before, by its service: «Book again» books it once more
	storia = []
	arrivo = arrivo_dal_telefono()
	# "session 4 of 10": which session of a cycle each one is
	sedute = cicli.numero_della_seduta([riga.parent for riga in righe])
	for riga in righe:
		appuntamento = frappe.db.get_value(
			"CRM Appointment",
			riga.parent,
			["name", "title", "service", "starts_on", "ends_on", "status", "location", "video_link"],
			as_dict=True,
		)
		if not appuntamento:
			continue
		if vista and not anteprima.vede("CRM Appointment", appuntamento.name):
			# in the centre's preview, an appointment whoever previews does not read
			# keeps its place, with nothing of it
			(prossimi if get_datetime(appuntamento.starts_on) >= adesso else passati).append(
				{**anteprima.coperta(appuntamento), "starts_on": appuntamento.starts_on}
			)
			continue
		annullato = "Cancelled" in (appuntamento.status, riga.status)
		inizio, fine = (
			get_datetime(appuntamento.starts_on),
			(get_datetime(appuntamento.ends_on) if appuntamento.ends_on else None),
		)
		# going on now, the place still open: it is still the next one
		in_corso = (
			not annullato and inizio < adesso < (fine or inizio) and riga.status in ("Booked", "Arrived")
		)
		online = visite_online.del_servizio(appuntamento.service)
		voce = {
			"name": appuntamento.name,
			"service": frappe.db.get_value("CRM Service", appuntamento.service, "service_name")
			if appuntamento.service
			else appuntamento.title,
			"starts_on": appuntamento.starts_on,
			"ends_on": appuntamento.ends_on,
			# held by video: no place to come to, the room's door instead
			"location": None if online else appuntamento.location,
			"online": online,
			"status": "Cancelled" if annullato else appuntamento.status,
			"session": {
				k: v for k, v in (sedute.get(appuntamento.name) or {}).items() if k in ("number", "total")
			}
			or None,
			"staff": [
				frappe.utils.get_fullname(u)
				for u in frappe.get_all(
					"CRM Appointment Staff",
					filters={"parent": appuntamento.name, "parenttype": "CRM Appointment"},
					pluck="user",
				)
			],
		}
		if (inizio >= adesso and not annullato) or in_corso:
			# moved or cancelled on the booking page, by the service's own rules; not
			# from the centre's preview, which changes nothing
			if appuntamento.service and not vista and inizio >= adesso:
				voce["manage_url"] = _link_di_gestione(riga)
			voce["arrived"] = riga.status == "Arrived"
			# «I'm here», until the appointment ends: when it opens, by the server's clock;
			# an online visit is entered instead, from a quarter of an hour before. The
			# room's link is given only by `enter_online_visit`, never in the list
			if online:
				if not vista and appuntamento.video_link:
					voce["online_visit"] = V.tra_quanto(inizio, fine, adesso)
			elif not vista and arrivo and riga.status == A.IN_ATTESA:
				voce["check_in"] = A.tra_quanto(inizio, fine, adesso)
			prossimi.append(voce)
		else:
			passati.append(voce)
			storia.append({**voce, "service": appuntamento.service, "service_name": voce["service"]})
	prossimi.sort(key=lambda v: v["starts_on"])
	passati.sort(key=lambda v: v["starts_on"], reverse=True)
	storia.sort(key=lambda v: v["starts_on"], reverse=True)
	return {
		"upcoming": prossimi,
		"past": passati[:20],
		"cycles": cicli.della_persona(person),
		"subscriptions": abbonamenti.della_persona(person),
		"waiting": attese.della_persona(person),
		"can_wait": attese.impostazioni().area,
		# not from the centre's preview, which books nothing
		"book": None if vista else _per_prenotare(person, storia),
	}


# ------------------------------------------------------------------ booking again


def _per_prenotare(person: str, storia: list[dict]) -> dict | None:
	"""The booking page's link, on the service of the last appointment when it is
	still booked online; ``None`` where the centre takes no booking online."""
	from crm.scheduling.availability import settings

	if not cint(settings().get("online_booking_enabled")):
		return None
	prenotabili = {
		s.name: s.website_slug
		for s in frappe.get_all(
			"CRM Service", filters={"enabled": 1, "bookable_online": 1}, fields=["name", "website_slug"]
		)
	}
	return P.link_per_prenotare(storia, prenotabili, person)


def per_la_pagina_di_prenotazione(person: str | None) -> dict:
	"""What /prenota writes in for whoever comes from their area (``?persona=``):
	the session says who they are, the link only whose area. Anybody else, the
	centre's preview included, gets the empty form."""
	utente = frappe.session.user
	if not person or utente == "Guest" or anteprima.in_anteprima() or not accesso.entra_nell_area(utente):
		return {}
	riga = next((r for r in accesso.persone_di(utente) if r.lead == person), None)
	if not riga:
		return {}
	from crm.utils import stored_value

	def dati(lead: str | None) -> dict:
		if not lead:
			return {}
		return {
			"lead_name": frappe.db.get_value("CRM Lead", lead, "lead_name"),
			"email": stored_value("CRM Lead", lead, "email"),
			"phone": stored_value("CRM Lead", lead, "mobile_no") or stored_value("CRM Lead", lead, "phone"),
		}

	# who is in: the person with the session's address, else the session's own name
	io = dati(frappe.db.get_value("CRM Lead", {"email": utente}, "name"))
	io = {**io, "lead_name": io.get("lead_name") or frappe.utils.get_fullname(utente), "email": utente}
	return P.chi_prenota(riga.relation, dati(person), io)


# ------------------------------------------------------------------ «I'm here»


def arrivo_dal_telefono() -> bool:
	"""Whether the area offers «I'm here» (`CRM Area Settings.self_check_in`): on
	unless the centre switched it off."""
	valore = frappe.db.get_singles_dict("CRM Area Settings").get("self_check_in")
	return valore is None or bool(cint(valore))


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def check_in(person: str, appointment: str) -> dict:
	"""«I'm here»: the person says from their phone they are at the centre, from
	half an hour before their appointment until it ends. Marked arrived as the desk
	marks them - the waiting room counts from now -, and the desk and whoever the
	appointment is with are told."""
	from crm.notifiche import regole as N
	from crm.notifiche.avvisi import avvisa
	from crm.scheduling import esiti

	_mia(person)
	if not arrivo_dal_telefono():
		frappe.throw(_("The centre does not take arrivals from the phone: tell the desk."))
	if not frappe.db.exists("CRM Appointment", appointment):
		frappe.throw(_("This is not your appointment"), frappe.PermissionError)
	doc = frappe.get_doc("CRM Appointment", appointment)
	riga = next(
		(
			r
			for r in doc.participants
			if r.party_type == "CRM Lead" and r.party == person and r.status != "Cancelled"
		),
		None,
	) or next((r for r in doc.participants if r.party_type == "CRM Lead" and r.party == person), None)
	if not riga:
		frappe.throw(_("This is not your appointment"), frappe.PermissionError)
	perche = A.perche_no(
		get_datetime(doc.starts_on),
		get_datetime(doc.ends_on) if doc.ends_on else None,
		now_datetime(),
		doc.status,
		riga.status,
	)
	if perche == A.GIA_DETTO and riga.status == "Arrived":
		return {"arrived": True}
	if perche:
		frappe.throw(
			{
				A.PRESTO: _("It is a little early: you can say you are here from half an hour before."),
				A.FINITO: _("This appointment is over."),
				A.ANNULLATO: _("This appointment was cancelled."),
				A.GIA_DETTO: _("The centre already knows how this appointment went."),
			}[perche]
		)
	esiti.scrivi(doc, riga.name, "Arrived")
	nome = frappe.db.get_value("CRM Lead", person, "lead_name") or riga.participant_name or ""
	utenti = dict.fromkeys([*esiti.chi_avvisare(), *(s.user for s in doc.staff if s.user)])
	for utente in utenti:
		avvisa(
			utente,
			"Agenda",
			N.ARRIVATO_DALL_AREA,
			[nome],
			riguarda=("CRM Lead", person),
			oggetto=("CRM Appointment", doc.name),
		)
	return {"arrived": True}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=60, seconds=60 * 60)
def enter_online_visit(person: str, appointment: str) -> dict:
	"""«Enter the visit»: the room's link of the person's online visit, from a
	quarter of an hour before it starts until it ends. Only to the person whose
	place it is, never in the centre's preview, which enters nothing."""
	_mia(person)
	if not frappe.db.exists("CRM Appointment", appointment):
		frappe.throw(_("This is not your appointment"), frappe.PermissionError)
	doc = frappe.get_doc("CRM Appointment", appointment)
	righe = [r for r in doc.participants if r.party_type == "CRM Lead" and r.party == person]
	if not righe:
		frappe.throw(_("This is not your appointment"), frappe.PermissionError)
	riga = next((r for r in righe if r.status != "Cancelled"), righe[0])
	if not visite_online.del_servizio(doc.service):
		frappe.throw(_("This appointment is not an online visit."))
	perche = V.perche_no(
		get_datetime(doc.starts_on),
		get_datetime(doc.ends_on) if doc.ends_on else None,
		now_datetime(),
		doc.status,
		riga.status,
		doc.video_link,
	)
	if perche:
		frappe.throw(
			{
				V.PRESTO: _("It is a little early: you can enter from {0} minutes before.").format(
					visite_online.MINUTI
				),
				V.FINITO: _("This appointment is over."),
				V.ANNULLATO: _("This appointment was cancelled."),
				V.SENZA_STANZA: _("The centre has not given the link of this visit yet: ask the centre."),
			}[perche]
		)
	return {"url": doc.video_link}


# ------------------------------------------------------------------ waiting lists


def _in_lista() -> frappe._dict:
	conf = attese.impostazioni()
	if not conf.area:
		frappe.throw(_("The centre does not take the waiting list from the area"), frappe.PermissionError)
	return conf


def _prenotabili() -> list:
	"""The services one may wait for from the area: the booking page's own."""
	return frappe.get_all(
		"CRM Service",
		filters={"enabled": 1, "bookable_online": 1},
		fields=["name", "service_name", "max_participants", "staff_selection", "allow_staff_choice"],
		order_by="website_order asc, service_name asc",
	)


@frappe.whitelist()
def get_waiting_options(person: str) -> dict:
	"""What one may wait for from the area: the services, who does them when one
	may choose, the channels the offers go by, and the last day proposed."""
	_mia(person, anche_in_anteprima=True)
	conf = _in_lista()
	servizi = []
	for servizio in _prenotabili():
		staff = []
		if (
			frappe.utils.cint(servizio.allow_staff_choice)
			and (servizio.staff_selection or "Any one") == "Any one"
		):
			staff = [
				{"user": u, "name": frappe.utils.get_fullname(u)}
				for u in frappe.get_all(
					"CRM Service Staff",
					filters={"parenttype": "CRM Service", "parent": servizio.name},
					pluck="user",
					order_by="idx asc",
				)
			]
		servizi.append(
			{
				"name": servizio.name,
				"service_name": servizio.service_name,
				"staff": staff if len(staff) > 1 else [],
			}
		)
	return {
		"services": servizi,
		"channels": attese.canali_offerti(conf),
		"until": str(attese.fino_predefinito(conf)),
	}


def _contatto(riga) -> str | None:
	"""Who hears of the offers: the person themselves, or the parent who is in."""
	if riga.relation == accesso.SE_STESSO:
		return None
	from crm.area.avvisi import _persona_di

	return _persona_di(frappe.session.user)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def join_waiting_list(
	person: str,
	service: str,
	staff: str | None = None,
	days: list | str | None = None,
	parts: list | str | None = None,
	until: str | None = None,
	channel: str | None = None,
) -> dict:
	"""On the waiting list from the area, for a service of the booking page. Joining
	again changes what the person waits for."""
	riga = _mia(person)
	conf = _in_lista()
	if service not in {s.name for s in _prenotabili()}:
		frappe.throw(_("This service is not booked online"))
	giorni = frappe.parse_json(days) if isinstance(days, str) else (days or [])
	parti = frappe.parse_json(parts) if isinstance(parts, str) else (parts or [])
	oggi = attese._oggi()
	fino = frappe.utils.getdate(until) if until else attese.fino_predefinito(conf)
	if fino < oggi or fino > frappe.utils.getdate(frappe.utils.add_days(oggi, 365)):
		frappe.throw(_("Choose a last day from today to a year from now"))
	voce = attese.entra(
		person,
		service,
		staff=staff or None,
		righe=R.righe_da(giorni, parti),
		fino=fino,
		canale=channel,
		contatto=_contatto(riga),
		fonte=R.DALL_AREA,
		ignora_permessi=True,
	)
	attese.dopo_l_ingresso(voce.name)
	return {"waiting": attese.della_persona(person)}


def _voce_di(person: str, entry: str):
	doc = frappe.get_doc(attese.VOCE, entry)
	if doc.lead != person:
		frappe.throw(_("This is not your area"), frappe.PermissionError)
	return doc


@frappe.whitelist(methods=["POST"])
def leave_waiting_list(person: str, entry: str) -> dict:
	_mia(person)
	attese.togli(_voce_di(person, entry))
	return {"waiting": attese.della_persona(person)}


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def answer_waiting_offer(person: str, entry: str, answer: str) -> dict:
	"""Yes or no to the place offered: yes books it, if it is still free."""
	_mia(person)
	doc = _voce_di(person, entry)
	riga = next((r for r in doc.offers if r.status == R.INVIATA), None)
	if not riga:
		esito = {"result": "none"}
	elif answer == "yes":
		esito = attese.conferma(doc, riga, R.DALL_AREA)
	else:
		attese.rifiuta(doc, riga)
		esito = {"result": "declined"}
	return {"result": esito["result"], "waiting": attese.della_persona(person)}


# ------------------------------------------------------------------ preparing the appointment

#: In the trace of a link: made, or taken up, from the area.
DALL_AREA = "Client area"
#: How long the forms opened from the area stay open.
ORE_MODULI = 4
#: A form filled at home that is signed at the desk (`dovuti._in_corso`).
A_STUDIO = "to_sign_at_desk"


#: Why who is in does not sign: the page says it in its own words.
PERCHE = {
	"parent": "Your forms are answered by a parent or guardian, from their area",
	"not_linked": "To sign for them, ask the centre to add you to their related people",
	"follows": "The person signs their own forms",
}


def _chi_firma(person: str, riga) -> tuple[dict | None, str | None]:
	"""Who signs the person's forms from the area, as a link by email would go
	(`richieste.destinatario`): the person, if nobody answers for them; else the
	parent or guardian who is in. Who only follows them sees, and does not sign
	(design.md, "Familiari"). Else, why not (`PERCHE`)."""
	from crm.moduli import richieste

	rappresentanti = richieste._rappresentanti(person)
	if riga.relation == accesso.SE_STESSO:
		if rappresentanti or richieste._minorenne(person):
			return None, "parent"
		return {"lead": person, "given_by": None}, None
	if riga.relation == accesso.TUTORE:
		for chi in rappresentanti:
			if accesso._normalizza(frappe.db.get_value("CRM Lead", chi, "email")) == frappe.session.user:
				return {"lead": chi, "given_by": chi}, None
		return None, "not_linked"
	return None, "follows"


@frappe.whitelist()
def get_forms(person: str) -> dict:
	"""What to prepare for the next appointment: the forms the centre asks, which
	are under way, and whether who is in signs them (design.md, "Prepara la visita")."""
	from crm.moduli import dovuti

	riga = _mia(person, anche_in_anteprima=True)
	prossimo = dovuti.prossimo_appuntamento(person)
	# the person's own forms, those with health data too: they are theirs to fill
	voci = dovuti.dovuti([person], {person: prossimo}, clinici=True)[person]
	firma, perche = _chi_firma(person, riga)
	# today's forms count for today's visit, but "before your appointment" only
	# while it is still ahead, as the appointments say
	davanti = prossimo and get_datetime(prossimo.starts_on) >= now_datetime()
	return {
		"appointment": {"name": prossimo.name, "starts_on": prossimo.starts_on} if davanti else None,
		"forms": [
			{
				"template": voce["template"],
				"title": voce["title"],
				"reason": voce["reason"],
				"pending": voce["pending"],
				# filled already, it waits for its signature at the desk
				"fill": bool(firma) and voce["pending"] != A_STUDIO,
			}
			for voce in voci
		],
		"can_fill": bool(firma),
		"why_not": perche,
	}


def _da_riprendere(person: str, firma: dict, scelti: set[str]):
	"""An open link for these forms, signed by the same person: taken up again with
	its answers so far rather than started twice - made by the area, or sent by
	email (whose link then gives way to the area's, as a new link would)."""
	from crm.moduli import richieste

	for nome in frappe.get_all(
		richieste.RICHIESTA,
		filters={
			"lead": person,
			"channel": "Link",
			"via": ("is", "not set"),
			"status": ("in", richieste.APERTE),
			"expires_on": (">", now_datetime()),
		},
		pluck="name",
		order_by="creation desc",
	):
		capo = frappe.get_doc(richieste.RICHIESTA, nome)
		if (capo.given_by or None) != firma["given_by"]:
			continue
		aperti = {r.template for r in richieste._gruppo(capo) if r.status in richieste.APERTE}
		if scelti <= aperti:
			return capo
	return None


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def fill_forms(person: str, templates: str | list) -> dict:
	"""The forms page for these forms, already open: who is in came with a code, so
	the page asks for none. Returns its link and its session."""
	from frappe.utils import add_to_date

	from crm.moduli import dovuti, richieste, traccia

	riga = _mia(person)
	firma, perche = _chi_firma(person, riga)
	if not firma:
		frappe.throw(_(PERCHE[perche]), frappe.PermissionError)
	chiesti = {voce["template"] for voce in get_forms(person)["forms"] if voce["fill"]}
	elenco = frappe.parse_json(templates) if isinstance(templates, str) else (templates or [])
	scelti = [nome for nome in elenco if nome in chiesti]
	if not scelti:
		frappe.throw(_("There is nothing to fill here"))
	capo = _da_riprendere(person, firma, set(scelti))
	if capo:
		token = richieste._segreto()
		capo.db_set("token_hash", richieste._impronta(token))
		traccia.traccia(richieste.RICHIESTA, capo.name, "taken up", DALL_AREA)
	else:
		prossimo = dovuti.prossimo_appuntamento(person)
		# where a code goes if the page asks for one again: the signer's address
		indirizzo = frappe.db.get_value("CRM Lead", firma["lead"], "email") or frappe.session.user
		gruppo, token = richieste._crea(
			person,
			scelti,
			"Link",
			scadenza=add_to_date(now_datetime(), hours=ORE_MODULI),
			appointment=prossimo.name if prossimo else None,
			given_by=firma["given_by"],
			recipient=firma["lead"],
			sent_to=richieste._nascosta(indirizzo),
			# asked for by who is in: nobody of the centre sent it, and the forms
			# are the person's own, those with health data too
			mittente=frappe.session.user,
			dal_centro=True,
		)
		capo = gruppo[0]
		traccia.traccia(
			richieste.RICHIESTA, capo.name, "sent", DALL_AREA, {"forms": [r.name for r in gruppo]}
		)
	sessione = richieste._apri_sessione(capo)
	return {"url": f"/modulo/{token}", "token": token, "session": sessione}


# ------------------------------------------------------------------ invoices


def _fatture(person: str) -> list:
	return frappe.get_all(
		"CRM Invoice",
		# a test invoice is the centre's rehearsal, never the person's
		filters={"party_type": "CRM Lead", "party": person, "docstatus": 1, "test_document": 0},
		fields=[
			"name",
			"document_number",
			"posting_date",
			"grand_total",
			"net_payable",
			"pdf_file",
			"document_type",
			"collected_on",
			"sdi_status",
		],
		order_by="posting_date desc",
		limit=50,
	)


def _da_pagare(fattura) -> float:
	"""What is left to pay of an invoice, by the desk's rule (`incassi`): issued, not
	a credit note, not collected, not sent back by the SdI. Nothing for the rest."""
	from crm.invoicing import incassi

	if (
		fattura.collected_on
		or (fattura.document_type or "TD01") in incassi.NOTE_DI_CREDITO
		or fattura.sdi_status == "scartata"
	):
		return 0.0
	return incassi.da_pagare(fattura)


@frappe.whitelist()
def get_invoices(person: str) -> dict:
	"""The person's invoices, each with what is left to pay of it; the total left,
	and how the centre is paid (`solleciti.come_pagare`)."""
	from crm.demo import guardie
	from crm.invoicing import solleciti
	from crm.pagamenti import collegamento, pagamenti

	_mia(person, anche_in_anteprima=True)
	righe = _fatture(person)
	# paid online on Stripe (`crm.pagamenti`): «Pay online», and «Paid online on…»
	online = (
		collegamento.collegato()
		and not anteprima.in_anteprima()
		and not guardie.mai_a_stripe(("CRM Lead", person))
	)
	pagate = pagamenti.pagate_online([f.name for f in righe])
	fatture = anteprima.filtra(
		"CRM Invoice",
		[
			{
				"name": f.name,
				"number": f.document_number or f.name,
				"date": f.posting_date,
				"total": f.grand_total,
				"to_pay": _da_pagare(f),
				"has_pdf": bool(f.pdf_file),
				"pay_online": bool(
					online and _da_pagare(f) > 0 and not guardie.mai_a_stripe(("CRM Invoice", f.name))
				),
				"paid_online_on": pagate.get(f.name),
			}
			for f in righe
		],
	)
	# in the centre's preview, only what whoever previews reads counts
	totale = round(sum(f.get("to_pay") or 0 for f in fatture if not f.get("hidden")), 2)
	return {
		"invoices": fatture,
		"to_pay": totale,
		"how_to_pay": solleciti.come_pagare() if totale else "",
	}


@frappe.whitelist(methods=["POST"])
def pay_invoice(person: str, invoice: str) -> dict:
	"""«Pay online»: the Stripe link that pays what is left of one of the person's
	invoices, back to the area once paid. Never in the centre's preview."""
	from crm.pagamenti import pagamenti

	_mia(person)
	if not any(f.name == invoice for f in _fatture(person)):
		frappe.throw(_("This is not your area"), frappe.PermissionError)
	return pagamenti.link_della_fattura(invoice, frappe.utils.get_url("/area/documents"))


@frappe.whitelist(methods=["GET"])
def download_invoice(person: str, invoice: str) -> None:
	_mia(person)
	fattura = next((f for f in _fatture(person) if f.name == invoice), None)
	if not fattura or not fattura.pdf_file:
		frappe.throw(_("There is no PDF of this invoice"), frappe.PermissionError)
	contenuto = frappe.get_doc("File", {"file_url": fattura.pdf_file}).get_content(encodings=[])
	frappe.local.response.filename = f"{fattura.document_number or fattura.name}.pdf".replace("/", "-")
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"
