# Modifications copyright (c) 2026, NPM2 Solutions Srl
"""
Event notification handling for CRM.

This module handles event notifications for the CRM system, supporting both:
1. Custom event notifications set on individual events
2. Global default notifications from CRM Settings for events without custom notifications

The notification system processes events that are either:
- Starting from now or in the future (normal case)
- Currently in progress (between starts_on and ends_on) to handle delayed notifications

Global notifications are configured in CRM Settings under the Calendar tab and are applied
to events that don't have custom notifications set. This ensures all events can receive
reminders even if users don't configure them individually.

In DottorCloud (docs/crm/43, 56):

- The round looks at every event whose reminder can be due, whoever's it is: it runs
  as the scheduler's Administrator, and it looked only at the events of the user it
  ran as, so a professional never had the reminders of their own events nor of their
  appointments' calendar copies. It reads only the events whose reminder can fall in
  its window, and no event at all while nothing has a reminder of its unit.
- A reminder goes to whom its event is for: its owner and its participants who are
  enabled System Users (`_destinatari`), each in their own room on the screen; by
  email Administrator is left out.
- A reminder leaves at its time, at the first round after it, never before
  (`e_il_momento`). A round runs every four minutes ("minutes", "hours") and every
  hour ("hours", "days", "weeks"), and a reminder is due at every round of its window
  after its time: so an email leaves once, written in the register
  (`CRM Event Reminder`) before it leaves, and one written there does not leave
  again. The screen's needs no register: the browser shows an event's reminder once.
- It says the event's title and when, never the description, which on an
  appointment's calendar copy is its notes. By email such a copy is only «an
  appointment»: its title is the service and the people.
"""

import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.query_builder.functions import Count, IfNull, Max
from frappe.utils import add_to_date, cint, get_time, now_datetime

from crm.marchio import con_nome
from crm.posta.aspetto import pulsante

#: The register of the reminders that left by email, each written before it leaves.
REGISTRO = "CRM Event Reminder"
#: The way of a reminder the register keeps: the screen's needs none.
EMAIL = "Email"
#: An appointment's calendar copy (`sync_event`): its title is the service and the
#: people, its description the appointment's notes.
APPUNTAMENTO = "CRM Appointment"


def trigger_offset_event_notifications():
	"""Trigger event notifications for offset-based intervals (minutes)."""
	_process_event_notifications_by_interval("minutes")
	_process_event_notifications_by_interval("hours")


def trigger_hourly_event_notifications():
	"""Trigger event notifications for hourly intervals, and for days and weeks: a
	reminder leaves at the first round after its time (`e_il_momento`), and the days
	were looked at only at midnight, the weeks only on Sunday at midnight - a «1 day
	before» of a visit at ten never left, an all-day event's «at 9» left at midnight."""
	for interval in ("hours", "days", "weeks"):
		_process_event_notifications_by_interval(interval)


def _process_event_notifications_by_interval(interval):
	"""
	Process event notifications for a specific interval: every event's, each to whom
	its event is for.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
	"""

	if frappe.flags.in_import or frappe.flags.in_patch:
		return

	current_time = now_datetime()
	del_centro = _promemoria_del_centro(interval)
	anticipo = _anticipo_piu_lungo(interval, del_centro)
	if anticipo is None:
		# nobody set a reminder of this unit: no event to read
		return

	for notification in _promemoria_degli_eventi(interval, current_time, anticipo, del_centro):
		try:
			event_start = notification.get("starts_on")
			before_value = cint(notification.get("before_value"))

			trigger_datetime = _calculate_trigger_datetime(
				event_start,
				before_value,
				interval,
				notification.get("all_day_event"),
				notification.get("time_of_day"),
			)

			if not e_il_momento(
				current_time, trigger_datetime, event_start, notification.get("ends_on"), interval
			):
				continue

			if notification.get("notification_type") == "Email":
				_send_email_notification(notification, event_start, before_value, interval)
			elif notification.get("notification_type") == "Notification":
				_send_system_notification(notification)

		except Exception as e:
			frappe.log_error(
				f"Error processing {interval} notification for event {notification.get('event_name', 'Unknown')}: {e!s}"
			)
			continue


def _promemoria_del_centro(interval) -> list:
	"""The centre's reminders of this unit (Settings > Agenda > Agenda & reminders),
	for the events with none of their own: each marked for all-day events or for the
	others."""
	tabelle = {"event_notifications": 0, "all_day_event_notifications": 1}
	righe = frappe.get_all(
		"Event Notifications",
		filters={
			"parenttype": "FCRM Settings",
			"parent": "FCRM Settings",
			"parentfield": ["in", list(tabelle)],
			"interval": interval,
		},
		fields=["name", "parentfield", "type", "before", "time"],
		order_by="idx asc",
	)
	for riga in righe:
		riga.tutto_il_giorno = tabelle[riga.parentfield]
	return righe


def _anticipo_piu_lungo(interval, del_centro) -> int | None:
	"""How many units before its event the earliest reminder of this unit leaves, the
	events' own and the centre's: None where nobody set one."""
	N = frappe.qb.DocType("Event Notifications")
	((propri, quanti),) = (
		frappe.qb.from_(N)
		.select(Max(IfNull(N.before, 0)), Count(N.name))
		.where((N.parenttype == "Event") & (N.parentfield == "notifications") & (N.interval == interval))
	).run()
	anticipi = [cint(riga.before) for riga in del_centro]
	if quanti:
		anticipi.append(cint(propri))
	return max(anticipi) if anticipi else None


def _promemoria_degli_eventi(interval, adesso, anticipo, del_centro) -> list:
	"""Each reminder of this unit of the events it can be due for now, whoever's they
	are: the event's own, else the centre's - for all-day events, or for the others.

	Only the events that start before a reminder of this unit can fall in the window
	(`fin_dove_cercare`), and the ones under way."""
	E = frappe.qb.DocType("Event")
	eventi = (
		frappe.qb.from_(E)
		.select(
			E.name.as_("event_name"),
			E.subject,
			E.starts_on,
			E.ends_on,
			E.owner,
			E.all_day.as_("all_day_event"),
			E.reference_doctype,
			E.reference_docname,
		)
		.where(E.status != "Cancelled")
		.where(
			((E.starts_on >= adesso) & (E.starts_on <= fin_dove_cercare(adesso, interval, anticipo)))
			| ((E.starts_on <= adesso) & (E.ends_on > adesso))
		)
		.orderby(E.starts_on)
		.orderby(E.name)
	).run(as_dict=True)
	if not eventi:
		return []

	nomi = [evento.event_name for evento in eventi]
	propri = defaultdict(list)
	for riga in frappe.get_all(
		"Event Notifications",
		filters={
			"parenttype": "Event",
			"parentfield": "notifications",
			"parent": ["in", nomi],
			"interval": interval,
		},
		fields=["name", "parent", "type", "before", "time"],
		order_by="idx asc",
	):
		propri[riga.parent].append(riga)
	partecipanti = defaultdict(list)
	for riga in frappe.get_all(
		"Event Participants",
		filters={"parenttype": "Event", "parentfield": "event_participants", "parent": ["in", nomi]},
		fields=["parent", "email"],
		order_by="idx asc",
	):
		if riga.email and riga.email.strip():
			partecipanti[riga.parent].append(riga.email.strip())

	promemoria = []
	for evento in eventi:
		evento.event_participants = partecipanti.get(evento.event_name, [])
		righe = propri.get(evento.event_name) or [
			riga for riga in del_centro if riga.tutto_il_giorno == cint(evento.all_day_event)
		]
		for riga in righe:
			promemoria.append(
				frappe._dict(
					evento,
					# which reminder it is: the event's own row, or the centre's
					reminder=riga.name,
					notification_type=riga.type,
					before_value=cint(riga.before),
					time_of_day=riga.time,
				)
			)
	return promemoria


def fin_dove_cercare(adesso: datetime, interval: str, anticipo: int) -> datetime:
	"""The latest start of an event whose reminder of this unit, ``anticipo`` units
	before it at most, can be due in the round at ``adesso``: a reminder is never due
	before its time (`e_il_momento`). An all-day event is reminded at an hour of a day
	before it (`time`): up to a day later than its start says."""
	fino_a = adesso + _durata(interval, anticipo)
	if interval in ("days", "weeks"):
		fino_a += timedelta(days=1)
	return fino_a


def e_il_momento(adesso: datetime, trigger: datetime, inizio: datetime, fine, interval: str) -> bool:
	"""Whether a reminder due at ``trigger`` leaves in the round at ``adesso``: from
	that time to the end of its window after it, or - its time passed while the event
	is under way, a round that did not run then - until the event ends. An event with
	no end is never under way.

	Never before its time: the window went as far before it as after it, and the one
	email the register lets leave left at its start - «1 hour before» two hours
	before, saying «It starts in an hour.»"""
	if fine and inizio <= adesso < fine and adesso > trigger:
		return True
	return trigger <= adesso <= trigger + timedelta(**_get_trigger_window_duration(interval))


def _durata(interval: str, quanti: int) -> timedelta:
	"""``quanti`` of a unit as a span of time; an unknown unit is hours, as the trigger
	reads it."""
	unita = interval if interval in ("minutes", "hours", "days", "weeks") else "hours"
	return timedelta(**{unita: cint(quanti)})


def _calculate_trigger_datetime(event_start, before_value, interval, all_day_event, time_of_day):
	"""
	Calculate when the notification should be triggered based on event start time and interval.

	Args:
		event_start (datetime): Event start datetime
		before_value (int): How many units before the event
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
		all_day_event (bool): Whether this is an all-day event
		time_of_day (time): Specific time to send notification for all-day events

	Returns:
		datetime: When the notification should be triggered
	"""

	if all_day_event and time_of_day and interval in ["days", "weeks"]:
		if interval == "days":
			trigger_date = event_start.date() - timedelta(days=before_value)
		elif interval == "weeks":
			trigger_date = event_start.date() - timedelta(weeks=before_value)

		# the database gives a time as the span since midnight, which combine refuses
		trigger_datetime = datetime.combine(trigger_date, get_time(time_of_day))
	else:
		interval_kwargs = _get_interval_kwargs(interval, before_value)
		trigger_datetime = add_to_date(event_start, **interval_kwargs)

	return trigger_datetime


def _get_interval_kwargs(interval, before_value):
	"""
	Get the appropriate keyword arguments for add_to_date based on interval type.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')
		before_value (int): How many units before the event

	Returns:
		dict: Keyword arguments for add_to_date with negative values
	"""
	interval_mapping = {
		"minutes": {"minutes": -before_value},
		"hours": {"hours": -before_value},
		"days": {"days": -before_value},
		"weeks": {"weeks": -before_value},
	}

	return interval_mapping.get(interval, {"hours": -before_value})


def _get_trigger_window_duration(interval):
	"""
	Get the trigger window duration based on interval type.

	Args:
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		dict: How long after its time a reminder may still leave: a round of its unit
		falls in it (every four minutes for minutes and hours, every hour for days
		and weeks), and one held up a while still leaves
	"""
	window_mapping = {
		"minutes": {"minutes": 5},
		"hours": {"hours": 1},
		"days": {"hours": 8},
		"weeks": {"days": 4},
	}

	return window_mapping.get(interval, {"hours": 1})


# ------------------------------------------------------------------ the register


def nome_del_promemoria(evento, promemoria, destinatario, canale, inizio) -> str:
	"""A reminder's name in the register: its key's fingerprint - the event, which of
	its reminders (its own row, or the centre's), to whom, by which way, for which
	time. The same key gives the same name, and the database takes it once; the time
	is in it, so an event moved is reminded again of its new one."""
	quando = inizio.strftime("%Y-%m-%d %H:%M:%S") if hasattr(inizio, "strftime") else str(inizio or "")
	chiave = "\n".join(
		str(parte or "")
		for parte in (evento, promemoria, destinatario, canale, quando.replace("T", " ")[:19])
	)
	return hashlib.sha256(chiave.encode()).hexdigest()[:32]


def _segna(notification, utente: str, canale: str = EMAIL) -> bool:
	"""Write down that this reminder leaves for ``utente`` by ``canale``, before it
	does: False where it is written already - it left in an earlier round of its
	window, or another round is sending it (this one and the hourly one both take
	the hours)."""
	nome = nome_del_promemoria(
		notification.event_name, notification.reminder, utente, canale, notification.starts_on
	)
	if frappe.db.exists(REGISTRO, nome):
		return False
	try:
		frappe.get_doc(
			{
				"doctype": REGISTRO,
				"event": notification.event_name,
				"reminder": notification.reminder,
				"recipient": utente,
				"channel": canale,
				"starts_on": notification.starts_on,
			}
		).insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# the framework's «already exists» is for a screen: nobody reads it here
		frappe.clear_last_message()
		return False
	return True


def _conferma() -> None:
	"""Kept now, whatever happens next: a reminder written down before it leaves, its
	email after."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — a reminder is written down before it leaves, as an appointment's is


# ------------------------------------------------------------------ the email


def _send_email_notification(notification, event_start, before_value, interval):
	"""The reminder by email to each of whom the event is for, once: the enabled
	System Users who own it or take part in it (`_utenti`) - Administrator left out,
	whose address is the setup's - each in their own language, each written in the
	register before it leaves.

	It says the event's title, when, how long to it and where to open it, never the
	description, as the screen's reminder does: on an appointment's calendar copy the
	description is its notes. Of such a copy it says only that it is an appointment:
	its title is the service and the people, which stay out of an email to a
	colleague, kept in a mailbox and shown on a phone's locked screen
	(PRIV-NOTIFICHE-SENZA-SALUTE, docs/verticali/clinica/principi-sanitari.md). An
	event about the demo is reminded on the screen, never by email, as a notification
	about it is read only in the panel."""
	from crm.demo import guardie
	from crm.notifiche.posta import nella_lingua_di

	if guardie.solo_nel_pannello(
		("Event", notification.event_name),
		(notification.get("reference_doctype"), notification.get("reference_docname")),
	):
		return

	for utente in _utenti(notification):
		if utente.name == "Administrator" or not utente.email:
			continue
		if not _segna(notification, utente.name):
			continue
		# written down before it leaves: whatever happens next, it never leaves twice
		_conferma()
		try:
			with nella_lingua_di(utente.name):
				_manda_l_email(notification, utente.email, event_start, before_value, interval)
			_conferma()
		except Exception:
			frappe.log_error(
				title=f"Reminder of event {notification.event_name} not sent",
				reference_doctype="Event",
				reference_name=notification.event_name,
			)


def _manda_l_email(notification, email, event_start, before_value, interval):
	esc = frappe.utils.escape_html
	tutto_il_giorno = cint(notification.get("all_day_event"))
	quando = frappe.utils.format_datetime(
		event_start, "EEEE d MMMM" if tutto_il_giorno else "EEEE d MMMM, HH:mm"
	)
	if notification.get("reference_doctype") == APPUNTAMENTO:
		# the copy's title is the service and the people: only that it is one
		titolo = _("Appointment")
		oggetto = _("Reminder: appointment on {0}").format(quando)
	else:
		# one line: a title may have been written on more
		titolo = " ".join(str(notification.get("subject") or "").split()) or _("Event")
		oggetto = _("Reminder: {0}").format(titolo)
	message = "".join(
		[
			f"<p><b>{esc(titolo)}</b><br>{esc(quando)}</p>",
			f"<p>{esc(_format_time_remaining(before_value, interval))}</p>",
			pulsante(
				frappe.utils.get_url(f"/crm/calendar?date={event_start.strftime('%Y-%m-%d')}"),
				con_nome(_("Open the agenda in {brand}")),
			),
		]
	)

	frappe.sendmail(
		recipients=[email],
		subject=oggetto,
		header=_("Event reminder"),
		with_container=True,
		message=message,
		reference_doctype="Event",
		reference_name=notification.event_name,
		now=True,
	)


def _format_time_remaining(before_value, interval):
	"""
	Format the time remaining message based on the interval and before value.

	Args:
		before_value (int): The number of units before the event
		interval (str): The interval type ('minutes', 'hours', 'days', 'weeks')

	Returns:
		str: Formatted time remaining message
	"""
	# one whole sentence per unit, and one for a single one: "1 hours" reads wrong anywhere
	frasi = {
		"minutes": (_("It starts in a minute."), _("It starts in {0} minutes.")),
		"hours": (_("It starts in an hour."), _("It starts in {0} hours.")),
		"days": (_("It starts tomorrow."), _("It starts in {0} days.")),
		"weeks": (_("It starts in a week."), _("It starts in {0} weeks.")),
	}
	una, molte = frasi.get(interval, frasi["hours"])
	return una if frappe.utils.cint(before_value) == 1 else molte.format(before_value)


# ------------------------------------------------------------------ on the screen


#: What a reminder tells the browser about its event: never the description,
#: which on an appointment's calendar copy is its notes (`sync_event`).
CAMPI_DEL_PROMEMORIA = (
	"event_name",
	"subject",
	"starts_on",
	"ends_on",
	"all_day_event",
	"owner",
	"event_participants",
)


def _send_system_notification(notification):
	"""The reminder on the screen of whom the event is for: its owner and its
	participants who are users of the centre, each in their own room.

	It went to the site's room, which every desk user's browser joins (the
	reception, marketing, the other professionals, the agency), with the
	description, and each browser kept it."""
	messaggio = {campo: notification.get(campo) for campo in CAMPI_DEL_PROMEMORIA}
	for utente in _destinatari(notification):
		frappe.publish_realtime("event_notification", messaggio, user=utente)


def _utenti(notification) -> list:
	"""The enabled System Users an event is for, with their email: its owner and its
	participants, which the event keeps by email - a user's name, or the email of a
	user whose name is not one (Administrator)."""
	chi = {
		str(valore).strip()
		for valore in (notification.get("owner"), *(notification.get("event_participants") or []))
		if valore and str(valore).strip()
	}
	if not chi:
		return []
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		or_filters={"name": ["in", sorted(chi)], "email": ["in", sorted(chi)]},
		fields=["name", "email"],
		order_by="name asc",
	)


def _destinatari(notification) -> list[str]:
	"""The names of the users an event is for (`_utenti`)."""
	return [utente.name for utente in _utenti(notification)]
