# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, get_datetime, getdate, now_datetime

from crm.permissions.livelli import puo
from crm.scheduling import cicli, pricing
from crm.scheduling.availability import find_conflicts, settings


class CRMAppointment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_appointment_participant.crm_appointment_participant import (
			CRMAppointmentParticipant,
		)
		from crm.fcrm.doctype.crm_appointment_resource.crm_appointment_resource import (
			CRMAppointmentResource,
		)
		from crm.fcrm.doctype.crm_appointment_staff.crm_appointment_staff import CRMAppointmentStaff

		booking: DF.Link | None
		booking_connection: DF.Link | None
		cancellation_reason: DF.SmallText | None
		color: DF.Color | None
		conflict_note: DF.SmallText | None
		currency: DF.Link | None
		ends_on: DF.Datetime
		customer_notes: DF.SmallText | None
		event: DF.Link | None
		external_id: DF.Data | None
		external_platform: DF.Data | None
		external_url: DF.Data | None
		location: DF.Data | None
		notes: DF.SmallText | None
		override_conflicts: DF.Check
		participants: DF.Table[CRMAppointmentParticipant]
		per_participant: DF.Check
		price_list: DF.Link | None
		price_source: DF.Data | None
		reschedule_count: DF.Int
		resources: DF.Table[CRMAppointmentResource]
		series: DF.Data | None
		session_cycle: DF.Link | None
		source: DF.Literal["Internal", "Online", "External"]
		service: DF.Link
		staff: DF.Table[CRMAppointmentStaff]
		starts_on: DF.Datetime
		status: DF.Literal["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"]
		title: DF.Data | None
		total_amount: DF.Currency | None
		unit_price: DF.Currency | None
	# end: auto-generated types

	def before_validate(self):
		self.apply_service_defaults()

	def validate(self):
		self.participants_are_people()
		self.validate_times()
		self.validate_participants()
		self.stamp_arrivals()
		self.close_from_attendance()
		self.set_title()
		self.check_conflicts()
		# a session of a cycle joins it before the price, and costs its share after
		cicli.aggancia(self)
		pricing.apply_to(self)
		cicli.prezzo(self)

	def on_update(self):
		self.sync_event()
		self.notify_online_client()
		self.update_last_visit()
		cicli.appuntamento_aggiornato(self)

	def on_trash(self):
		self.remove_event()

	def after_delete(self):
		cicli.appuntamento_eliminato(self)

	# --- defaults ---------------------------------------------------------

	def apply_service_defaults(self):
		"""Fill in from the service what the caller did not specify."""
		if not self.service:
			return
		service = frappe.get_cached_doc("CRM Service", self.service)
		if self.starts_on and not self.ends_on:
			# the professional's own length for this service wins over the service's
			users = {row.user for row in self.staff if row.user}
			own = [cint(row.get("duration")) for row in service.staff if row.user in users]
			minutes = max(own) if own and all(own) else cint(service.duration)
			self.ends_on = add_to_date(get_datetime(self.starts_on), minutes=minutes, as_datetime=True)
		if not self.color:
			self.color = service.color
		if not self.location and service.get("location"):
			self.location = service.location
		if not self.location:
			# the room the appointment runs in is the most useful default location
			for row in self.resources:
				location = frappe.db.get_value("CRM Resource", row.resource, "location")
				if location:
					self.location = location
					break
		if not self.price_list:
			self.price_list = pricing.default_price_list()
		for row in self.resources:
			if row.resource and not row.quantity:
				row.quantity = 1

	def set_title(self):
		names = [row.participant_name for row in self.participants if row.participant_name]
		who = ", ".join(names[:2])
		if len(names) > 2:
			who = _("{0} +{1}").format(who, len(names) - 2)
		self.title = f"{self.service} — {who}" if who else self.service

	# --- how it went ------------------------------------------------------

	def update_last_visit(self):
		"""The person's last visit and its service: administrative data the recalls
		pick people by (docs/gestionale-medico, the second seam), never the record."""
		if self.status == "Cancelled":
			return
		giorno = getdate(self.starts_on)
		for row in self.participants:
			came = row.status == "Attended" or (
				self.status == "Completed" and row.status not in ("No Show", "Cancelled")
			)
			person = person_of(row.party_type, row.party) if came else None
			if not person:
				continue
			last = frappe.db.get_value("CRM Lead", person, "last_visit")
			if not last or getdate(last) <= giorno:
				frappe.db.set_value(
					"CRM Lead",
					person,
					{"last_visit": giorno, "last_service": self.service},
					update_modified=False,
				)

	def stamp_arrivals(self):
		"""The desk checked somebody in: the waiting room counts from now."""
		for row in self.participants:
			if row.status == "Arrived" and not row.arrived_at:
				row.arrived_at = now_datetime()

	def close_from_attendance(self):
		"""The participants say how it went (docs/gestionale-medico, fase 1): once each
		of them came or did not, it is Completed, or No Show when nobody came. The
		visit, the check-in and the invoice close it this way, without somebody
		remembering to. Cancelled stays cancelled, and one still waiting stays open."""
		if self.status == "Cancelled":
			return
		attivi = [row for row in self.participants if row.status != "Cancelled"]
		if not attivi or any(row.status in ("Booked", "Arrived") for row in attivi):
			return
		self.status = "Completed" if any(row.status == "Attended" for row in attivi) else "No Show"

	# --- validation -------------------------------------------------------

	def participants_are_people(self):
		"""A participant is a person: a contact or a deal picked by an older screen, or
		by a flow that starts from them (the dialer on a deal), becomes the person
		behind it. One that has no person behind it stays as it is."""
		for row in self.participants:
			person = person_of(row.party_type, row.party)
			if person:
				row.party_type, row.party = "CRM Lead", person

	def validate_times(self):
		if get_datetime(self.ends_on) <= get_datetime(self.starts_on):
			frappe.throw(_("End time must be after start time"))

	def validate_participants(self):
		if not self.service:
			return
		service = frappe.get_cached_doc("CRM Service", self.service)
		active = [row for row in self.participants if row.status != "Cancelled"]
		maximum = cint(service.max_participants) or 1
		if len(active) > maximum:
			frappe.throw(
				_("{0} takes at most {1} participants, {2} listed").format(self.service, maximum, len(active))
			)
		seen = set()
		for row in active:
			if not row.party:
				continue
			key = (row.party_type, row.party)
			if key in seen:
				frappe.throw(_("{0} is listed twice among the participants").format(row.participant_name))
			seen.add(key)

	def check_conflicts(self):
		"""Block a clashing appointment — unless a manager deliberately forces it.

		A forced booking is not silently accepted: what it collided with is written
		to ``conflict_note`` so the clash stays visible on the record.
		"""
		conflicts = find_conflicts(self)
		if not conflicts:
			self.conflict_note = None
			return
		if self.flags.external_booking:
			# a booking that already exists on an external platform cannot be refused:
			# keep it, and keep the clash visible for whoever has to solve it
			self.conflict_note = "\n".join(conflicts)
			return
		config = settings()
		may_override = cint(config.allow_override) and puo("agenda.sovrapponi")
		if cint(self.override_conflicts) and may_override:
			self.conflict_note = "\n".join(conflicts)
			return
		frappe.throw(
			"<br>".join([_("This appointment cannot be booked:"), *conflicts]),
			title=_("Scheduling conflict"),
		)

	def notify_online_client(self):
		"""A client who booked online hears about approval or cancellation."""
		if self.source != "Online":
			return
		try:
			from crm.api.service_booking import on_appointment_status_change

			on_appointment_status_change(self)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Appointment {self.name}: client notification failed")

	# --- calendar mirror --------------------------------------------------

	def sync_event(self):
		"""Mirror the appointment into a framework ``Event``.

		That is what puts it on the classic calendar and inside the per-user Google
		Calendar sync. The mirror is one-way: the appointment is the source of
		truth, the Event is a projection of it.
		"""
		if frappe.flags.in_appointment_sync or not cint(settings().sync_to_event):
			return
		if self.status == "Cancelled":
			self.remove_event()
			return

		owner = self.staff[0].user if self.staff else self.owner
		payload = {
			"subject": self.title or self.name,
			"starts_on": self.starts_on,
			"ends_on": self.ends_on,
			"status": "Open",
			"event_type": "Private",
			"description": self.notes,
			"color": self.color,
			"reference_doctype": "CRM Appointment",
			"reference_docname": self.name,
		}
		frappe.flags.in_appointment_sync = True
		try:
			if self.event and frappe.db.exists("Event", self.event):
				event = frappe.get_doc("Event", self.event)
				event.update(payload)
			else:
				event = frappe.get_doc({"doctype": "Event", **payload})
				event.owner = owner
			event.set("event_participants", self._event_participants())
			event.save(ignore_permissions=True)
			if event.name != self.event:
				self.db_set("event", event.name, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Appointment {self.name}: calendar sync failed")
		finally:
			frappe.flags.in_appointment_sync = False

	def _event_participants(self) -> list[dict]:
		rows = []
		for row in self.staff[1:]:
			email = frappe.db.get_value("User", row.user, "email")
			if email:
				rows.append({"reference_doctype": "User", "reference_docname": row.user, "email": email})
		for row in self.participants:
			if row.email and row.status != "Cancelled":
				entry = {"email": row.email}
				if row.party_type == "Contact" and row.party:
					entry.update({"reference_doctype": "Contact", "reference_docname": row.party})
				rows.append(entry)
		return rows

	def remove_event(self):
		if not self.event:
			return
		frappe.flags.in_appointment_sync = True
		try:
			if frappe.db.exists("Event", self.event):
				frappe.delete_doc("Event", self.event, ignore_permissions=True, delete_permanently=True)
			self.db_set("event", None, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Appointment {self.name}: calendar cleanup failed")
		finally:
			frappe.flags.in_appointment_sync = False


def person_of(party_type: str | None, party: str | None) -> str | None:
	"""The person (``CRM Lead``) behind a participant, whatever it was picked as."""
	if not party:
		return None
	if party_type in (None, "", "CRM Lead"):
		return party if party_type == "CRM Lead" else None
	if party_type == "Contact":
		return frappe.db.get_value("CRM Lead", {"contact": party}, "name")
	if party_type == "CRM Deal":
		return frappe.db.get_value("CRM Deal", party, "lead")
	return None
