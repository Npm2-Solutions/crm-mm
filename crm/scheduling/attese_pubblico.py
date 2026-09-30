# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The waiting list for the person, without logging in (`crm.scheduling.attese`).

- **Joining from /prenota**: when no time suits, or a class is full, the page
  asks the days, the parts of the day and until when, then the same details and
  ticks as a booking. The person is found or made as a booking finds them
  (`find_or_create_person`), and so is the one they wait for when it is somebody
  else; the ticks go in the consent register with the entry.
- **The page of the link**, `/lista-attesa/<link>`: an offer's link, or the one
  that came with joining. It shows what the person waits for and the place
  offered, if one waits for them; yes books it, no gives it to the next ones,
  and one can leave the list. Links are kept as SHA-256 only; an unknown one
  gets the same answer whatever is wrong with it. Every call is rate limited.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, cint, get_fullname, getdate, now_datetime

from crm.scheduling import attese as A
from crm.scheduling import attese_regole as R
from crm.scheduling.timeutils import scheduling_tz

# ------------------------------------------------------------------ joining from /prenota


def _giorno(valore) -> datetime.date | None:
	try:
		return getdate(valore) if valore else None
	except Exception:
		frappe.throw(_("This date cannot be read"))


# nosemgrep: guest-whitelisted-method — joining the waiting list is what /prenota offers when no time suits, 10/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def join_waiting_list(
	service: str,
	full_name: str,
	email: str,
	phone: str | None = None,
	staff: str | None = None,
	session: str | None = None,
	participants: int = 1,
	days: list | str | None = None,
	parts: list | str | None = None,
	until: str | None = None,
	channel: str | None = None,
	consent: int | str | None = None,
	consent_text: str | None = None,
	marketing_consent: int | str | None = None,
	for_name: str | None = None,
	for_relation: str | None = None,
	crm_vid: str | None = None,
	crm_sid: str | None = None,
) -> dict:
	"""On the waiting list from the booking page: for a service, maybe with one
	professional, on some days and parts of the day, until a day; or for a seat in
	a class that is full (``session``, its public id). Returns what the page shows."""
	from crm.api import service_booking as SB
	from crm.api.booking import _ensure_source, find_or_create_person
	from crm.api.tracking import record_conversion
	from crm.persone.collegate import persona_per_conto

	config = SB._config()
	conf = A.impostazioni()
	if not conf.online:
		frappe.throw(_("The waiting list is not open online"), frappe.PermissionError)
	doc = SB._resolve_service(service)

	full_name = " ".join((full_name or "").split())[:140]
	for_name = " ".join((for_name or "").split())[:140]
	email = SB._clean_email(email)
	phone = SB._clean_phone(phone)
	if not full_name or not email:
		frappe.throw(_("Name and email are required"))
	require_phone = SB._effective(doc).get("require_phone")
	if (require_phone is None or cint(require_phone)) and not phone:
		frappe.throw(_("A phone number is required"))
	if cint(config.get("require_privacy_consent")) and not cint(consent):
		frappe.throw(_("Please accept the privacy policy to go on the waiting list"))

	lezione = A.sessione_da_id(doc.name, session)
	staff_user = (
		SB._staff_from_public_id(doc, staff) if staff and SB._flag(doc, "allow_staff_choice") else None
	)
	giorni = frappe.parse_json(days) if isinstance(days, str) else (days or [])
	parti = frappe.parse_json(parts) if isinstance(parts, str) else (parts or [])
	oggi = A._oggi()
	fino = _giorno(until) or getdate(add_days(oggi, conf.giorni_online))
	if fino < oggi or fino > getdate(add_days(oggi, 365)):
		frappe.throw(_("Choose a last day from today to a year from now"))

	booker = find_or_create_person(
		full_name,
		email,
		phone,
		crm_vid=crm_vid,
		crm_sid=crm_sid,
		source=SB.ONLINE_SOURCE,
		medium="booking",
		source_dimension="service_booking",
		conversione=None,
	)
	lead = (
		persona_per_conto(booker, for_name, for_relation or "", fonte=_ensure_source(SB.ONLINE_SOURCE))
		if for_name
		else booker
	)
	voce = A.entra(
		lead,
		doc.name,
		staff=staff_user,
		lezione=lezione,
		posti=SB._seats(doc, participants),
		righe=[] if lezione else R.righe_da(giorni, parti),
		fino=fino,
		canale=channel,
		contatto=booker if lead != booker else None,
		fonte=R.ONLINE,
		ignora_permessi=True,
	)
	SB._registra_consensi(lead, voce, config, consent, consent_text, marketing_consent, booker)
	record_conversion(
		frappe.get_doc("CRM Lead", booker), "custom", _("Waiting list: {0}").format(doc.service_name), voce
	)
	segreto = A.segreto_della_voce(voce)
	_email_d_ingresso(voce, segreto)
	A.dopo_l_ingresso(voce.name)
	return {**vista(frappe.get_doc(A.VOCE, voce.name)), "link": A.link_della_pagina(segreto)}


def _scelte_a_parole(voce) -> str:
	"""The days and parts of an entry in words, for an email."""
	scelte = R.scelte_da(voce.days)
	if scelte is None:
		return ", ".join(f"{_(r.workday)} {str(r.start_time)[:5]}–{str(r.end_time)[:5]}" for r in voce.days)
	giorni = ", ".join(_(g) for g in scelte["days"]) if 0 < len(scelte["days"]) < 7 else _("Any day")
	nomi = {"morning": _("morning"), "afternoon": _("afternoon"), "evening": _("evening")}
	parti = ", ".join(nomi[p] for p in scelte["parts"]) if scelte["parts"] else _("any time")
	return f"{giorni} · {parti}"


def _email_d_ingresso(voce, segreto: str) -> None:
	"""The email that says one is on the list, with the link to see it or leave:
	never stops the joining."""
	from frappe.utils import escape_html as esc

	from crm.moduli.richieste import nome_del_centro
	from crm.utils import stored_value

	email = stored_value("CRM Lead", voce.contact or voce.lead, "email")
	if not email:
		return
	try:
		servizio = A._nome_servizio(voce.service)
		centro = nome_del_centro() or _("the centre")
		righe = [
			f"<p><b>{esc(_('You are on the waiting list for {0} at {1}').format(servizio, centro))}</b></p>"
		]
		if voce.contact:
			righe.append(f"<p>{esc(_('For {0}').format(voce.lead_name))}</p>")
		if voce.class_session:
			righe.append(
				f"<p>{esc(_('The class of {0}, when a seat frees up').format(A.quando(frappe.db.get_value(A.APPUNTAMENTO, voce.class_session, 'starts_on'))))}</p>"
			)
		else:
			righe.append(f"<p>{esc(_scelte_a_parole(voce))}</p>")
		if voce.until:
			righe.append(f"<p>{esc(_('Until {0}').format(frappe.utils.formatdate(voce.until)))}</p>")
		righe.append(
			f"<p>{esc(_('When a place frees up we write to you: it goes to whoever confirms first.'))}</p>"
		)
		righe.append(
			f'<p><a href="{esc(A.link_della_pagina(segreto))}">{esc(_("See or leave the waiting list"))}</a></p>'
		)
		frappe.sendmail(
			recipients=[email],
			subject=_("You are on the waiting list — {0}").format(servizio),
			message="".join(righe),
			reference_doctype=A.VOCE,
			reference_name=voce.name,
		)
	except Exception:
		frappe.log_error(
			title="Waiting list: joining email not sent", reference_doctype=A.VOCE, reference_name=voce.name
		)


# ------------------------------------------------------------------ the page of the link


def _per_token(token: str | None):
	"""The entry of a link, and the offer if it was an offer's. An unknown link gets
	the same answer whatever is wrong with it, so a guess learns nothing."""
	voce = riga = None
	if isinstance(token, str) and 16 <= len(token) <= 120:
		impronta = A.impronta(token)
		trovata = frappe.db.get_value(
			A.OFFERTA, {"token_hash": impronta, "parenttype": A.VOCE}, ["name", "parent"], as_dict=True
		)
		if trovata:
			voce = frappe.get_doc(A.VOCE, trovata.parent)
			riga = next((r for r in voce.offers if r.name == trovata.name), None)
		else:
			nome = frappe.db.get_value(A.VOCE, {"token_hash": impronta}, "name")
			voce = frappe.get_doc(A.VOCE, nome) if nome else None
	if not voce:
		frappe.throw(_("This link is not valid"), frappe.PermissionError)
	return voce, riga


def _in_corso(voce, riga):
	"""The offer the page is about: the one waiting for an answer, else the link's own."""
	return next((r for r in voce.offers if r.status == R.INVIATA), None) or riga


def _nomi_staff(testo) -> list[str]:
	return [get_fullname(u) for u in A._staff_di(testo)]


def vista(voce, riga=None) -> dict:
	"""What the page shows: what the person waits for, the place offered and how it
	stands, the booking once made. Nobody else's name but the professional's."""
	from crm.api.service_booking import _calendar_links, manage_url
	from crm.moduli.richieste import nome_del_centro
	from crm.scheduling.availability import settings

	servizio = frappe.get_cached_doc("CRM Service", voce.service)
	offerta = _in_corso(voce, riga)
	dati = {
		"centre": nome_del_centro(),
		"service": servizio.service_name,
		"for": voce.lead_name if voce.contact else "",
		"status": voce.status,
		"staff": get_fullname(voce.staff) if voce.staff else "",
		"class_start": A._utc(
			frappe.db.get_value(A.APPUNTAMENTO, voce.class_session, "starts_on")
		).isoformat()
		if voce.class_session
		else None,
		"choice": R.scelte_da(voce.days),
		"days": [
			{"workday": r.workday, "start": str(r.start_time)[:5], "end": str(r.end_time)[:5]}
			for r in voce.days
		],
		"until": str(voce.until) if voce.until else None,
		"channel": voce.channel,
		"can_leave": voce.status in R.APERTE,
		"timezone": str(scheduling_tz()),
		"offer": None,
		"booked": None,
	}
	if offerta and voce.status != R.PRENOTATA:
		dati["offer"] = {
			"status": offerta.status,
			"start": A._utc(offerta.starts_on).isoformat(),
			"end": A._utc(offerta.ends_on or offerta.starts_on).isoformat(),
			"staff": _nomi_staff(offerta.staff),
			"location": servizio.get("location") or "",
			"expires_on": A._utc(offerta.expires_on).isoformat() if offerta.expires_on else None,
			"can_answer": offerta.status == R.INVIATA
			and bool(offerta.expires_on)
			and frappe.utils.get_datetime(offerta.expires_on) > now_datetime(),
		}
	if voce.status == R.PRENOTATA and voce.booked_appointment:
		appuntamento = frappe.get_doc(A.APPUNTAMENTO, voce.booked_appointment)
		inizio, fine = A._utc(appuntamento.starts_on), A._utc(appuntamento.ends_on)
		prenotato = {
			"start": inizio.isoformat(),
			"end": fine.isoformat(),
			"staff": [get_fullname(r.user) for r in appuntamento.staff],
			"location": appuntamento.location or "",
			"cancelled": appuntamento.status == "Cancelled",
			"calendar_links": _calendar_links(servizio.service_name, inizio, fine, appuntamento.location),
		}
		mio = next((r for r in appuntamento.participants if r.party == voce.lead and r.access_token), None)
		if mio and cint(settings().get("online_booking_enabled")) and cint(servizio.bookable_online):
			prenotato["manage_url"] = manage_url(mio.access_token)
		dati["booked"] = prenotato
	return dati


def _controlla(voce, riga) -> None:
	"""An offer that is shown is still a place: if the engine says it has gone, the
	offer is taken now, not when the person presses yes."""
	offerta = _in_corso(voce, riga)
	if not offerta or offerta.status != R.INVIATA:
		return
	if frappe.utils.get_datetime(offerta.expires_on) < now_datetime():
		offerta.db_set({"status": R.SENZA_RISPOSTA, "answered_on": now_datetime()}, update_modified=False)
		A.di_nuovo_in_fila(voce.name)
		return
	if not A.ancora_libero(voce, offerta):
		A._presa(voce, offerta)


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 300/h an address
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=300, seconds=60 * 60)
def open_offer(token: str) -> dict:
	"""The first look at a link: a POST, since a place that has gone is marked so."""
	voce, riga = _per_token(token)
	_controlla(voce, riga)
	return vista(frappe.get_doc(A.VOCE, voce.name), riga)


def _riga_di(voce, riga):
	offerta = _in_corso(frappe.get_doc(A.VOCE, voce.name), riga)
	return next((r for r in voce.offers if offerta and r.name == offerta.name), None)


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def confirm_offer(token: str) -> dict:
	"""Yes: booked, if the place is still free."""
	voce, riga = _per_token(token)
	offerta = _riga_di(voce, riga)
	esito = A.conferma(voce, offerta, R.ONLINE) if offerta else {"result": "none"}
	return {**vista(frappe.get_doc(A.VOCE, voce.name), riga), "result": esito["result"]}


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def decline_offer(token: str) -> dict:
	"""No thanks: the place goes on, the person keeps their place in the line."""
	voce, riga = _per_token(token)
	offerta = _riga_di(voce, riga)
	if offerta:
		A.rifiuta(voce, offerta)
	return {**vista(frappe.get_doc(A.VOCE, voce.name), riga), "result": "declined"}


# nosemgrep: guest-whitelisted-method — the opaque link is the credential, 20/h
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def leave_list(token: str) -> dict:
	"""Off the waiting list: the person no longer waits."""
	voce, riga = _per_token(token)
	A.togli(voce)
	return {**vista(frappe.get_doc(A.VOCE, voce.name), riga), "result": "left"}
