# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online visits: a service held by video (`CRM Service.online_visit`) gives each
of its appointments the link of a room (`CRM Appointment.video_link`).

- **Where the room lives.** On the agency's video server, a Jitsi Meet (`CRM
  Scheduling Settings.video_server`, permlevel 1, else `dottorcloud_video` in the
  site's configuration): a room of its own, its name random, made once when the
  appointment is saved (`visite_online_regole`). Without one, the professional's
  own fixed room (`CRM Staff Schedule.video_link`), or a link the desk pastes on
  the appointment (Meet, Zoom, Teams). Never for the demo's appointments: their
  rooms would be on a real server (`guardie.visita_di_prova`).
- **Who reads it.** The staff who read the appointment, in the agenda's panel and
  at the reception desk; the person only through their area, from a quarter of an
  hour before the start until the end (`crm.area.api.enter_online_visit`). The
  messages say it is an online visit and that one enters from the area: the room's
  link travels in no email nor SMS.
- **No room of the centre.** The engine books an online visit's service without
  the rooms its card asks for (`serve_la_stanza`).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_url

from crm.scheduling import visite_online_regole as R

#: How many minutes before the start the person enters, for the messages.
MINUTI = int(R.ANTICIPO.total_seconds() // 60)


def server() -> str | None:
	"""The agency's video server: the setting, else the site's configuration."""
	scritto = frappe.db.get_single_value("CRM Scheduling Settings", "video_server")
	return R.base_del_server(scritto) or R.base_del_server(frappe.conf.get("dottorcloud_video"))


def del_servizio(servizio: str | None) -> bool:
	"""Whether a service is held by video."""
	return bool(servizio) and bool(cint(frappe.get_cached_value("CRM Service", servizio, "online_visit")))


def serve_la_stanza(servizio, riga) -> bool:
	"""Whether a resource the service's card asks for is needed: an online visit
	needs no room of the centre, its equipment it still does."""
	if not cint(servizio.get("online_visit")):
		return True
	tipo = riga.resource_type
	if riga.resource:
		tipo = frappe.get_cached_value("CRM Resource", riga.resource, "resource_type") or tipo
	return tipo != "Room"


def del_professionista(doc) -> str | None:
	"""The first professional's own room, of whoever has one."""
	for riga in doc.staff:
		if riga.user:
			link = frappe.db.get_value("CRM Staff Schedule", {"user": riga.user}, "video_link")
			if link and R.link_valido(link):
				return link
	return None


def assicura(doc) -> None:
	"""`CRM Appointment.validate`: an online visit gets its link, once; a link
	pasted by hand must be an https address."""
	if doc.video_link:
		doc.video_link = doc.video_link.strip()
		if not R.link_valido(doc.video_link):
			frappe.throw(_("The online visit's link must be an address starting with https://"))
		return
	if not del_servizio(doc.service) or doc.status == "Cancelled":
		return
	from crm.demo import guardie

	if guardie.visita_di_prova(doc):
		return
	doc.video_link = R.link_da_dare(None, server(), del_professionista(doc))


def area_per(lead: str | None) -> str | None:
	"""Where a message sends the person to enter the visit: their area's
	appointments, opened for them if nobody ever entered it (nothing is sent: the
	message is what tells them). None for a demo person, an area the centre
	closed, or nobody to open it to."""
	if not lead:
		return None
	from crm.area import accesso, collegamento

	if collegamento._della_demo(lead):
		return None
	if not accesso.accessi_aperti(lead) and frappe.db.exists(accesso.ACCESSO, {"lead": lead}):
		# the centre closed it: never opened again by a message
		return None
	try:
		if not collegamento.apri_se_serve(lead):
			return None
	except Exception:
		frappe.clear_last_message()
		frappe.log_error(title=f"Area not opened for an online visit: {lead}")
		return None
	return get_url("/area/appointments")


def frase(area: str | None) -> str:
	"""What a message says of an online visit."""
	if area:
		return _(
			"It is an online visit: you enter it from your area, from {0} minutes before it starts: {1}"
		).format(MINUTI, area)
	return _("It is an online visit: the centre tells you how to enter it.")
