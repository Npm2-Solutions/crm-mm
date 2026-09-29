# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings > Plan: what the centre has, what it used this month, and how it grows.

The plan is the agency's to write (`CRM Plan`, System Manager only). The centre sees
it here, and can do one thing on its own: start the 14-day trial of a module it does
not have. The request goes to the agency, which confirms it and bills it from the
month after (listino.md, "Come si amplia il piano"). Going over the size never blocks
anything: the page says so, and proposes the size above.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, get_last_day, getdate, now, nowdate

from crm.fcrm.doctype.crm_plan.crm_plan import AGENDE
from crm.permissions import livelli
from crm.permissions.livelli import richiede

#: Days a trial started from the CRM lasts.
GIORNI_DI_PROVA = 14

#: The plan's words for the registry's states, as the page shows them.
STATO = {
	livelli.ATTIVO: "active",
	livelli.PROVA: "trial",
	livelli.SOLA_LETTURA: "read_only",
	livelli.SPENTO: "off",
}


@frappe.whitelist()
@richiede("piano.vedi")
def get_plan() -> dict:
	"""The plan as the centre sees it."""
	piano = frappe.get_cached_doc("CRM Plan")
	righe = {riga.module: riga for riga in piano.modules}
	stati = livelli.moduli_attivi()
	moduli = []
	for modulo in livelli.moduli_piano():
		riga = righe.get(modulo.chiave)
		stato = livelli.stato_modulo(modulo.chiave, stati)
		moduli.append(
			{
				"key": modulo.chiave,
				"label": modulo.etichetta,
				"description": modulo.descrizione,
				"state": STATO[stato],
				"listed": bool(riga),
				"included_in_service": bool(riga and riga.source == "Agency service"),
				"service": riga.service if riga else None,
				"trial_until": riga.trial_until if riga else None,
				"expires_on": riga.expires_on if riga else None,
				"can_start_trial": stato == livelli.SPENTO and livelli.puo("piano.amplia"),
			}
		)
	agende = agende_attive()
	incluse = AGENDE.get(piano.size) if piano.size else None
	return {
		"size": piano.size or None,
		"agendas": {
			"active": agende,
			"included": incluse,
			"over": bool(incluse and agende > incluse),
		},
		"modules": moduli,
		"usage": consumi(),
		"agency": livelli.e_agenzia(frappe.session.user),
		"trial_days": GIORNI_DI_PROVA,
	}


@frappe.whitelist(methods=["POST"])
@richiede("piano.amplia")
def start_trial(module: str) -> dict:
	"""Start the trial of a module the centre does not have, and tell the agency."""
	livelli.carica()
	noti = {modulo.chiave: modulo for modulo in livelli.moduli_piano()}
	if module not in noti:
		frappe.throw(_("{0} is not a module of the plan").format(frappe.bold(module)))
	if livelli.stato_modulo(module, livelli.moduli_attivi()) != livelli.SPENTO:
		frappe.throw(_("{0} is already part of the plan").format(noti[module].etichetta))

	piano = frappe.get_single("CRM Plan")
	piano.set("modules", [riga for riga in piano.modules if riga.module != module])
	piano.append(
		"modules",
		{
			"module": module,
			"status": "Trial",
			"trial_until": add_days(nowdate(), GIORNI_DI_PROVA),
			"requested_by": frappe.session.user,
			"requested_on": now(),
		},
	)
	# the centre may start a trial, not write the plan: this one change, on its behalf
	piano.save(ignore_permissions=True)
	risposta = get_plan()
	risposta["agency_notified"] = _avvisa_agenzia(piano, noti[module].etichetta)
	return risposta


def _avvisa_agenzia(piano, modulo: str) -> bool:
	"""Tell the agency. The trial has started either way: a mail that could not go
	out is said on screen, so the centre can tell them another way."""
	destinatari = [piano.agency_email] if piano.agency_email else _system_managers()
	if not destinatari:
		return False
	try:
		_manda_richiesta(destinatari, modulo)
	except Exception:
		frappe.log_error(title="Plan: the agency could not be told about a trial")
		return False
	return True


def _manda_richiesta(destinatari: list[str], modulo: str) -> None:
	chi = frappe.utils.get_fullname(frappe.session.user)
	frappe.sendmail(
		recipients=destinatari,
		subject=_("{0} started a trial of {1} on {2}").format(chi, modulo, frappe.local.site),
		message=_(
			"{0} ({1}) started the {2}-day trial of {3} on {4}. Confirm it in the site's CRM Plan to bill it "
			"from next month, or let it end: the module then turns read only."
		).format(chi, frappe.session.user, GIORNI_DI_PROVA, modulo, frappe.utils.get_url()),
	)


def _system_managers() -> list[str]:
	users = frappe.get_all(
		"Has Role",
		filters={"role": "System Manager", "parenttype": "User", "parent": ["not in", ["Administrator"]]},
		pluck="parent",
		distinct=True,
	)
	return frappe.get_all("User", filters={"name": ["in", users or [""]], "enabled": 1}, pluck="email")


def agende_attive(giorno: str | None = None) -> int:
	"""Practitioners with at least one appointment this month.

	What the size counts: someone who receives appointments, even if they never open
	the CRM. Rooms, equipment, front desk and managers do not count.
	"""
	giorno = getdate(giorno or nowdate())
	Appointment = frappe.qb.DocType("CRM Appointment")
	Staff = frappe.qb.DocType("CRM Appointment Staff")
	righe = (
		frappe.qb.from_(Staff)
		.join(Appointment)
		.on(Appointment.name == Staff.parent)
		.select(Staff.user)
		.distinct()
		.where(
			(Staff.parenttype == "CRM Appointment")
			& (Appointment.status != "Cancelled")
			& (Appointment.starts_on >= get_first_day(giorno))
			& (Appointment.starts_on < add_days(get_last_day(giorno), 1))
		)
	).run(pluck=True)
	return len([user for user in righe if user])


def consumi(giorno: str | None = None) -> dict:
	"""What the centre used this month, as the agency bills it."""
	giorno = getdate(giorno or nowdate())
	periodo = ["between", [get_first_day(giorno), get_last_day(giorno)]]
	uso = {"whatsapp": None, "sms": None, "call_minutes": None}
	if frappe.db.table_exists("WhatsApp Message"):
		uso["whatsapp"] = frappe.db.count("WhatsApp Message", {"type": "Outgoing", "creation": periodo})
	uso["sms"] = frappe.db.count("CRM SMS Message", {"type": "Outgoing", "creation": periodo})
	secondi = frappe.get_all(
		"CRM Call Log",
		filters={"creation": periodo, "status": "Completed"},
		fields=[{"SUM": "duration", "as": "total"}],
	)
	uso["call_minutes"] = round((secondi[0].total or 0) / 60) if secondi else 0
	return uso
