# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's reminders (docs/crm/59): tomorrow's appointments whose
reminder is due by now have it, by email - the email stays in the part
(`crm.demo.modo`) - and about half of the people said «I'll be there» on the
booking page it linked to. The agenda shows their mark, Settings > Agenda >
Appointment reminders the last ones.

Through the reminders' own code: the engine sends (`promemoria.manda`), the
booking page confirms (`service_booking.confirm`). Only the demo's appointments,
never one of the centre's; the centre's reminders stay as the centre set them,
and the round never reminds the demo's (`crm.demo.guardie`). Loaded at night, when
no reminder is due yet, the part has nothing to send.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import get_datetime

from crm.demo import registro
from crm.demo.contesto import Contesto

APPUNTAMENTO = "CRM Appointment"
#: At most this many reminders: a morning's worth.
QUANTI = 10


def crea(ctx: Contesto) -> None:
	from crm.api import service_booking
	from crm.scheduling import promemoria as P
	from crm.scheduling import promemoria_regole as R

	ctx.avanza(_("Appointment reminders"))
	# by email, which every demo person receives: WhatsApp and SMS leave nothing here
	conf = frappe._dict(attivi=True, ore=R.ore_prima(None), whatsapp=None, sms=None, email=True)
	mandati = []
	with ctx.nella_lingua_del_centro():
		for appuntamento, riga in _dovuti(ctx, P, R, conf)[: ctx.quanti(QUANTI)]:
			P.manda(appuntamento, riga, conf)
			mandati.append(frappe.db.get_value(P.PARTECIPANTE, riga.name, "access_token"))
	ctx.rng.shuffle(mandati)
	# about half said «I'll be there» on the booking page the email linked to
	with ctx.come("Guest"):
		for token in mandati[: len(mandati) // 2 + 1] if mandati else []:
			service_booking.confirm(token)


def _dovuti(ctx: Contesto, P, R, conf) -> list[tuple]:
	"""Tomorrow's appointments of one person whose reminder is due by the rules, the
	demo's only."""
	adesso = P._adesso()
	domani = adesso.date() + datetime.timedelta(days=1)
	inizio = datetime.datetime.combine(domani, datetime.time())
	# the register as the earlier parts left it: `nomi_di_prova` knows nothing until
	# the whole demo is in
	della_demo = set(
		frappe.get_all(registro.REGISTRO, filters={"ref_doctype": APPUNTAMENTO}, pluck="ref_name")
	)
	dovuti = []
	for nome in frappe.get_all(
		APPUNTAMENTO,
		filters={
			"status": ["in", P.ATTIVI],
			"starts_on": [
				"between",
				(P._di_sistema(inizio), P._di_sistema(inizio + datetime.timedelta(days=1))),
			],
		},
		pluck="name",
		order_by="starts_on asc",
	):
		if nome not in della_demo:
			continue
		doc = frappe.get_doc(APPUNTAMENTO, nome)
		if doc.source == "External" or (doc.source == "Online" and doc.status == "Scheduled"):
			continue
		righe = [r for r in doc.participants if r.status != "Cancelled"]
		if len(righe) != 1 or righe[0].status != "Booked" or not righe[0].party:
			continue
		if not R.dovuto(P._locale(doc.starts_on), adesso, conf.ore, P._locale(get_datetime(doc.creation))):
			continue
		dovuti.append((doc, righe[0]))
	return dovuti
