# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Connectors to the online booking platforms clients already use.

Every connector turns its platform's bookings into ``ExternalBooking`` objects;
``crm.booking_platforms.sync`` turns those into ``CRM Appointment`` rows. The
registry below is the only place that knows the platforms by name — the
``platform`` Select of ``CRM Booking Connection`` holds the labels.

Three kinds of connector, in order of preference:

1. **API** — the platform has one (or one for partners): bookings are pulled
   and pushed, cancellations and blocked time can flow back.
2. **Calendar feed** — the platform exports a private .ics: bookings are read.
3. **Notification email** — the platform only e-mails: bookings are parsed.

And one door out for every platform that can import a calendar (Treatwell's
"Calendario esterno", Fresha, Cal.com, Google): the CRM's own busy feed, served
per connection and per professional by ``crm.api.booking_platforms.busy_feed``.
"""

from __future__ import annotations

from crm.booking_platforms.base import BookingPlatform
from crm.booking_platforms.docplanner import Docplanner
from crm.booking_platforms.email_parser import NotificationEmail, email_preset
from crm.booking_platforms.generic_webhook import GenericWebhook
from crm.booking_platforms.ical import ICalFeed
from crm.booking_platforms.schedulers import (
	Acuity,
	Booksy,
	CalCom,
	Calendly,
	EasyAppointments,
	MicrosoftBookings,
	Setmore,
	SimplyBook,
	Timify,
)

_BUSY_FEED = (
	"To block on the platform the hours already booked in the CRM, paste each "
	"professional's CRM busy-feed address in the platform's external calendar setting."
)

Treatwell = email_preset(
	"treatwell",
	"Treatwell / Uala",
	"beauty",
	"https://www.treatwell.it",
	("treatwell.it", "treatwell.com", "uala.it"),
	"Treatwell (which absorbed Uala) has no public API. In Treatwell Connect → Team → "
	"staff member → 'Calendario esterno' paste the CRM busy-feed address of that "
	"professional: CRM appointments then block Treatwell slots. Bookings reach the CRM "
	"through the notification emails.",
)
Fresha = email_preset(
	"fresha",
	"Fresha",
	"beauty",
	"https://www.fresha.com/it",
	("fresha.com",),
	"Fresha has no merchant API. Calendar → Sync lets each team member import the CRM "
	"busy feed as blocked time; bookings come in through the notification emails (or the "
	"export link, if your workspace shows one).",
)
Elty = email_preset(
	"elty",
	"Elty",
	"medical",
	"https://elty.it",
	("elty.it",),
	"Elty integrates only with selected practice software (AlfaDocs, MEG). Until a direct "
	"partnership exists, bookings arrive from Elty's notification emails. " + _BUSY_FEED,
)
IDoctors = email_preset(
	"idoctors",
	"iDoctors",
	"medical",
	"https://www.idoctors.it",
	("idoctors.it",),
	"iDoctors syncs its agenda with Google Calendar: connect the same Google Calendar to "
	"the CRM (Settings → Google Calendar) for two-way availability, and use this "
	"connection for its notification emails.",
)
Doctolib = email_preset(
	"doctolib",
	"Doctolib (Dottori.it)",
	"medical",
	"https://www.doctolib.it",
	("doctolib.it", "doctolib.com", "dottori.it"),
	"Doctolib's API is reserved to certified partners; bookings arrive from its notification emails.",
)
TopDoctors = email_preset(
	"topdoctors",
	"Top Doctors",
	"medical",
	"https://www.topdoctors.it",
	("topdoctors.it", "topdoctors.com"),
)
Pazienti = email_preset("pazienti", "Pazienti.it", "medical", "https://www.pazienti.it", ("pazienti.it",))
MioDottoreEmail = email_preset(
	"miodottore_email",
	"MioDottore (email)",
	"medical",
	"https://www.miodottore.it",
	("miodottore.it", "docplanner.com"),
	"For practices without Docplanner partner credentials: MioDottore booking, change and "
	"cancellation emails become appointments.",
)

PROVIDERS: list[type[BookingPlatform]] = [
	Docplanner,
	MioDottoreEmail,
	Treatwell,
	Fresha,
	Booksy,
	Elty,
	IDoctors,
	Doctolib,
	TopDoctors,
	Pazienti,
	SimplyBook,
	Calendly,
	CalCom,
	Acuity,
	MicrosoftBookings,
	Timify,
	Setmore,
	EasyAppointments,
	ICalFeed,
	NotificationEmail,
	GenericWebhook,
]

REGISTRY: dict[str, type[BookingPlatform]] = {cls.label: cls for cls in PROVIDERS}


def register(cls: type[BookingPlatform]) -> None:
	"""Add a connector at runtime — for a platform shipped by another app."""
	REGISTRY[cls.label] = cls


def provider_class(platform: str) -> type[BookingPlatform]:
	if platform in REGISTRY:
		return REGISTRY[platform]
	for cls in REGISTRY.values():
		if platform in (cls.key, cls.label):
			return cls
	raise KeyError(platform)


def get_provider(conn) -> BookingPlatform:
	return provider_class(conn.get("platform"))(conn)


def catalog() -> list[dict]:
	return [cls.describe() for cls in REGISTRY.values()]
