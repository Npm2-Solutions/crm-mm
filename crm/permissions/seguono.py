# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What belongs to a person follows the person: the agenda, the messages, the tracking.

Every Sales User read every appointment with its notes, every WhatsApp message and
SMS, every visitor's journey (doc 30, "Come stanno le cose oggi"). Now:

- **the agenda** by its capability's scope (`agenda.vedi`): the whole centre for the
  front desk and the manager; a practitioner their own - the appointments they work
  or booked; sales their people's appointments, and the rest as busy time without who
  or what (`get_calendar` shows it);
- **WhatsApp and SMS** to whoever may converse, about the people they see; a message
  about nobody is everybody's who converses, as a call is;
- **the tracking** about the people one sees; the anonymous traffic to whoever
  handles tracking;
- **the old booking pages' bookings** about the people one sees, or taken by them;
- **the emails** about a person or a deal to whoever converses (PR 4), and **the
  address book** not at all to whoever sees people masked.

The bricks are `org_hierarchy`'s: one condition for the list and for the record.
Somebody outside the levels, on the Desk with roles only, keeps the rules of their roles.
"""

from __future__ import annotations

import frappe
from frappe.query_builder.functions import IfNull

from crm.permissions import livelli
from crm.permissions import org_hierarchy as oh

APPUNTAMENTO = "CRM Appointment"


def _sql(condizione) -> str:
	return oh._as_sql(condizione)


def _riga_visibile(doc, doctype: str, condizione) -> bool:
	"""The list's condition, asked of one row."""
	if condizione is None or not doc.get("name"):
		return True
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(condizione).limit(1).run()
	)


# ------------------------------------------------------------------ the agenda


def _dello_staff(A, user: str):
	"""The appointments ``user`` works, or booked."""
	Staff = frappe.qb.DocType("CRM Appointment Staff").as_("_appt_staff")
	return A.name.isin(
		frappe.qb.from_(Staff)
		.select(Staff.parent)
		.where((Staff.parenttype == APPUNTAMENTO) & (Staff.user == user))
	) | (A.owner == user)


def _delle_sue_persone(A, user: str):
	"""The appointments of the people ``user`` sees."""
	Part = frappe.qb.DocType("CRM Appointment Participant").as_("_appt_part")
	di_persone = (Part.parenttype == APPUNTAMENTO) & (Part.party_type == "CRM Lead")
	visibili = oh.visible_leads(user)
	if visibili is not None:
		di_persone = di_persone & Part.party.isin(visibili)
	return A.name.isin(frappe.qb.from_(Part).select(Part.parent).where(di_persone))


def appointment_conditions(user: str | None = None):
	"""The appointments ``user`` reads in full: ``None`` all of them."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	ambito = livelli.ambito("agenda.vedi", user)
	if ambito == livelli.CENTRO:
		return None
	A = frappe.qb.DocType(APPUNTAMENTO)
	if ambito is None:
		return A.name.isnull()
	if ambito == livelli.SUOI:
		return _dello_staff(A, user)
	return _dello_staff(A, user) | _delle_sue_persone(A, user)


def shows_busy_time(user: str | None = None) -> bool:
	"""Whether the calendar shows ``user`` the rest of the agenda as busy time: they
	see some of it in full, not all."""
	user = user or frappe.session.user
	return livelli.nel_crm(user) and livelli.ambito("agenda.vedi", user) not in (livelli.CENTRO, None)


def get_appointment_permission_query_conditions(user: str | None = None) -> str:
	return _sql(appointment_conditions(user))


def has_appointment_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if livelli.nel_crm(user):
		if ptype == "delete" and not livelli.puo("agenda.elimina", user):
			return False
		if ptype in ("create", "write"):
			ambito = livelli.ambito("agenda.prenota", user)
			if ambito is None:
				return False
			# a practitioner books in their own agenda, nobody else's
			if ambito == livelli.SUOI and user not in {row.user for row in doc.get("staff") or []}:
				return False
	if ptype == "create":
		return True
	return _riga_visibile(doc, APPUNTAMENTO, appointment_conditions(user))


# ------------------------------------------------------------------ cycles of sessions

CICLO = "CRM Session Cycle"


def cycle_conditions(user: str | None = None):
	"""The cycles of sessions ``user`` reads: those of the appointments they read,
	and the ones they follow or sold; ``None`` all of them."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	ambito = livelli.ambito("agenda.vedi", user)
	if ambito == livelli.CENTRO:
		return None
	C = frappe.qb.DocType(CICLO)
	if ambito is None:
		return C.name.isnull()
	A = frappe.qb.DocType(APPUNTAMENTO).as_("_cycle_appt")
	suoi = (
		(C.practitioner == user)
		| (C.owner == user)
		| C.name.isin(
			frappe.qb.from_(A)
			.select(A.session_cycle)
			.where(A.session_cycle.isnotnull())
			.where(_dello_staff(A, user))
		)
	)
	if ambito == livelli.SUOI:
		return suoi
	visibili = oh.visible_leads(user)
	return None if visibili is None else suoi | C.lead.isin(visibili)


def get_cycle_permission_query_conditions(user: str | None = None) -> str:
	return _sql(cycle_conditions(user))


def has_cycle_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if livelli.nel_crm(user) and ptype in ("create", "write", "delete"):
		if not livelli.puo("agenda.cicli", user):
			return False
	if ptype == "create":
		return True
	return _riga_visibile(doc, CICLO, cycle_conditions(user))


# ------------------------------------------------------------------ subscriptions

ABBONAMENTO = "CRM Subscription"


def _ambito_abbonamenti(user: str) -> str | None:
	"""Who sells subscriptions reads them as far as they sell them; who reads the
	agenda, as far as they read it - its free and busy time shows no subscription."""
	vedi = livelli.ambito("agenda.vedi", user)
	if vedi == livelli.LIBERO_OCCUPATO:
		vedi = None
	return livelli.piu_ampio(livelli.ambito("agenda.abbonamenti", user), vedi)


def subscription_conditions(user: str | None = None):
	"""The subscriptions ``user`` reads: the whole centre's; a practitioner the ones
	they follow or sold, and those of the appointments they do; somebody with a team,
	also their people's. ``None`` all of them."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	ambito = _ambito_abbonamenti(user)
	if ambito == livelli.CENTRO:
		return None
	S = frappe.qb.DocType(ABBONAMENTO)
	if ambito is None:
		return S.name.isnull()
	A = frappe.qb.DocType(APPUNTAMENTO).as_("_subscription_appt")
	suoi = (
		(S.practitioner == user)
		| (S.owner == user)
		| S.name.isin(
			frappe.qb.from_(A)
			.select(A.subscription)
			.where(A.subscription.isnotnull())
			.where(_dello_staff(A, user))
		)
	)
	if ambito == livelli.SUOI:
		return suoi
	visibili = oh.visible_leads(user)
	return None if visibili is None else suoi | S.lead.isin(visibili)


def get_subscription_permission_query_conditions(user: str | None = None) -> str:
	return _sql(subscription_conditions(user))


def has_subscription_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if livelli.nel_crm(user) and ptype in ("create", "write", "delete"):
		if not livelli.puo("agenda.abbonamenti", user):
			return False
	if ptype == "create":
		return True
	return _riga_visibile(doc, ABBONAMENTO, subscription_conditions(user))


# ------------------------------------------------------------------ waiting lists

ATTESA = "CRM Waiting List Entry"


def waiting_conditions(user: str | None = None):
	"""The waiting list ``user`` reads, with `agenda.attese`: the whole centre's;
	a practitioner who waits for them, or for a service they do with anybody, and
	the ones they added; somebody with a team, also their people's. ``None`` all."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	ambito = livelli.ambito("agenda.attese", user)
	if ambito == livelli.CENTRO:
		return None
	W = frappe.qb.DocType(ATTESA)
	if ambito is None:
		return W.name.isnull()
	Staff = frappe.qb.DocType("CRM Service Staff").as_("_wait_staff")
	suoi_servizi = (
		frappe.qb.from_(Staff)
		.select(Staff.parent)
		.where((Staff.parenttype == "CRM Service") & (Staff.user == user))
	)
	suoi = (
		(W.staff == user) | (W.owner == user) | ((IfNull(W.staff, "") == "") & W.service.isin(suoi_servizi))
	)
	if ambito == livelli.SUOI:
		return suoi
	visibili = oh.visible_leads(user)
	return None if visibili is None else suoi | W.lead.isin(visibili)


def get_waiting_permission_query_conditions(user: str | None = None) -> str:
	return _sql(waiting_conditions(user))


def has_waiting_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if livelli.nel_crm(user) and not livelli.puo("agenda.attese", user):
		return False
	if ptype == "create":
		return True
	return _riga_visibile(doc, ATTESA, waiting_conditions(user))


# ---------------------------------------------------------------- the messages


def _message_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	DT = frappe.qb.DocType(doctype)
	if not livelli.puo("conversazioni.vedi", user):
		return DT.name.isnull()
	if oh.sees_everyone(user):
		return None
	# about a person or a deal they see; about nobody, everybody's who converses
	return oh._about_visible(DT.reference_doctype, DT.reference_name, user) | ~oh._about_someone(
		DT.reference_doctype, DT.reference_name
	)


def get_whatsapp_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_message_conditions(user, "WhatsApp Message"))


def has_whatsapp_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	return _riga_visibile(doc, "WhatsApp Message", _message_conditions(user, "WhatsApp Message"))


def get_sms_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_message_conditions(user, "CRM SMS Message"))


def has_sms_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	return _riga_visibile(doc, "CRM SMS Message", _message_conditions(user, "CRM SMS Message"))


# ---------------------------------------------------------------- the tracking


def _della_persona(DT, user: str):
	"""The row is about a person or a deal ``user`` sees."""
	condizione = None
	for campo, doctype in (("lead", "CRM Lead"), ("deal", "CRM Deal")):
		vede = IfNull(DT[campo], "") != ""
		if oh._scope(user, doctype) is not None:
			vede = vede & DT[campo].isin(oh._visible(doctype, user))
		condizione = vede if condizione is None else condizione | vede
	return condizione


def _tracking_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	gestisce = livelli.puo("tracciamento.gestisci", user)
	if gestisce and oh.sees_everyone(user):
		return None
	DT = frappe.qb.DocType(doctype)
	condizione = _della_persona(DT, user)
	if gestisce:
		# the traffic that is nobody yet: whoever handles tracking reads it
		anonimo = (IfNull(DT.lead, "") == "") & (IfNull(DT.deal, "") == "")
		condizione = condizione | anonimo
	return condizione


def get_visitor_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_tracking_conditions(user, "CRM Visitor"))


def has_visitor_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	return _riga_visibile(doc, "CRM Visitor", _tracking_conditions(user, "CRM Visitor"))


def get_tracking_event_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_tracking_conditions(user, "CRM Tracking Event"))


def has_tracking_event_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	return _riga_visibile(doc, "CRM Tracking Event", _tracking_conditions(user, "CRM Tracking Event"))


# ------------------------------------------------------- the old booking pages


def _booking_conditions(user: str | None):
	user = user or frappe.session.user
	if not livelli.nel_crm(user) or oh._scope(user, "CRM Lead") is None:
		return None
	B = frappe.qb.DocType("CRM Booking")
	return (B.agent == user) | B.lead.isin(oh._visible("CRM Lead", user))


def get_booking_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_booking_conditions(user))


def has_booking_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	return _riga_visibile(doc, "CRM Booking", _booking_conditions(user))


# ---------------------------------------------------------------- the emails


def _email_conditions(user: str | None):
	"""Emails about a person or a deal are conversations: whoever does not converse
	(Marketing, Accounting, the medical director) does not read them. The rest of the
	rule is Frappe's: an email follows the record it is about."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user) or livelli.puo("conversazioni.vedi", user):
		return None
	C = frappe.qb.DocType("Communication")
	return IfNull(C.reference_doctype, "").notin(oh._ABOUT)


def get_communication_permission_query_conditions(user: str | None = None) -> str:
	return _sql(_email_conditions(user))


def has_communication_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not livelli.nel_crm(user) or livelli.puo("conversazioni.vedi", user):
		return True
	return doc.get("reference_doctype") not in oh._ABOUT


# ------------------------------------------------------------- the address book


def _nasconde_i_recapiti(user: str) -> bool:
	"""Who sees people with email and phone masked (Marketing). An address book entry
	is little else than those: they do not read it at all."""
	return livelli.nel_crm(user) and livelli.ambito("persone.vedi", user) == livelli.MASCHERATO


def contact_conditions(user: str | None = None):
	"""The address book entries ``user`` reads: ``None`` all of them.

	An entry is little else than a name, an email and a phone, and every person has
	one (`CRM Lead.contact`): it follows the person, as the rest of what is theirs
	does - a practitioner read the whole centre's in the address book. One on a deal
	the user sees comes with the deal; one nobody owns (a company's, an old record)
	is the centre's.
	"""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return None
	C = frappe.qb.DocType("Contact")
	if _nasconde_i_recapiti(user):
		return C.name.isnull()
	persone = oh.visible_leads(user)
	if persone is None:
		return None
	Lead = frappe.qb.DocType("CRM Lead").as_("_contact_lead")
	di_qualcuno = frappe.qb.from_(Lead).select(Lead.contact).where(Lead.contact.isnotnull())
	delle_sue = frappe.qb.from_(Lead).select(Lead.contact).where(Lead.name.isin(persone))
	Riga = frappe.qb.DocType("CRM Contacts").as_("_contact_deal")
	sulle_sue = frappe.qb.from_(Riga).select(Riga.contact).where(Riga.parenttype == "CRM Deal")
	trattative = oh.visible_deals(user)
	if trattative is not None:
		sulle_sue = sulle_sue.where(Riga.parent.isin(trattative))
	return C.name.notin(di_qualcuno) | C.name.isin(delle_sue) | C.name.isin(sulle_sue)


def get_contact_permission_query_conditions(user: str | None = None) -> str:
	return _sql(contact_conditions(user))


def has_contact_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if _nasconde_i_recapiti(user):
		return False
	return _riga_visibile(doc, "Contact", contact_conditions(user))
