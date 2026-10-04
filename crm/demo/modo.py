# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How a part of the demo is made: through the screens' own code, with nothing
leaving the site.

The records go through their controllers and the modules' doc events, so a person
gets a contact, an appointment attended makes a client, a booking moves the deal:
the demo is the product's behaviour replayed, not rows written next to it. What
those same paths would send - an email, a job that writes to somebody, a message
to the browser, an automation, the agenda's mirror into the framework's calendar, the
global search - does not leave while a part runs (`in_prova`): an email stays in the part, where
the demo person it was for reads it (a link, a code), and every record made is written down in
the register (`crm.demo.registro`).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import frappe
import frappe.utils.background_jobs as lavori

from crm.demo import registro

#: The flags the modules already listen to, each muting one thing that would leave:
#: the automations, the appointments' mirror into the calendar (and its daily
#: email), the booking platforms, the booking page's emails, every email sent now.
SILENZI = (
	"in_crm_automation",
	"in_appointment_sync",
	"in_platform_sync",
	"in_service_booking_api",
	"mute_emails",
)


def _niente(*args, **kwargs):
	return None


def _trattieni(corrente: registro.Raccolta):
	"""`frappe.sendmail` while a part runs: the email stays in the part, for the demo
	person it is written to (`registro.posta_per`), and never leaves."""

	def sendmail(recipients=None, sender="", subject="No Subject", message="No Message", *args, **kwargs):
		if isinstance(recipients, str):
			recipients = [indirizzo.strip() for indirizzo in recipients.replace(";", ",").split(",")]
		corrente.posta.append(
			{
				"recipients": [indirizzo for indirizzo in recipients or () if indirizzo],
				"subject": subject,
				"message": message,
			}
		)

	return sendmail


@contextmanager
def in_prova(parte: str) -> Iterator[registro.Raccolta]:
	"""Make one part: what it creates is written down, and kept only whole.

	On the way out the part's work is committed - after-commit callbacks still see
	the muted senders - and written in the register; a part that fails is rolled
	back, and what a step committed on its own anyway is still written down, so
	that taking the demo away finds it.
	"""
	corrente = registro.Raccolta(parte=parte)
	prima = {flag: frappe.flags.get(flag) for flag in SILENZI}
	originali = {
		(frappe, "sendmail"): frappe.sendmail,
		(frappe, "enqueue"): frappe.enqueue,
		(lavori, "enqueue"): lavori.enqueue,
		(frappe, "publish_realtime"): frappe.publish_realtime,
	}
	corrente.pubblica = frappe.publish_realtime
	frappe.local.dati_di_prova = corrente
	for flag in SILENZI:
		frappe.flags[flag] = True
	# nor the framework's global search, which DottorCloud's screens never read: a
	# demo record queued there would be written back after the demo is gone
	ricerca = frappe.local.conf.get("disable_global_search")
	frappe.local.conf["disable_global_search"] = 1
	for (modulo, nome), _f in originali.items():
		setattr(modulo, nome, _niente)
	frappe.sendmail = _trattieni(corrente)
	riuscita = False
	try:
		yield corrente
		frappe.db.commit()
		riuscita = True
	finally:
		if not riuscita:
			frappe.db.rollback()
		try:
			registro.scrivi(corrente, esistenti_soltanto=not riuscita)
			frappe.db.commit()
		finally:
			for (modulo, nome), funzione in originali.items():
				setattr(modulo, nome, funzione)
			for flag, valore in prima.items():
				frappe.flags[flag] = valore
			frappe.local.conf["disable_global_search"] = ricerca
			frappe.local.dati_di_prova = None
