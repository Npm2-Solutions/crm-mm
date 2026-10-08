# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's summary: what one needs to know of them at a glance.

A person's page opens on it from the People list, the agenda, a search: one
person, two doors (docs/crm/54). From the conversations and from a
message's notification the page opens on the chat instead, and the same summary
sits beside the conversation. Who the person is and their next appointment are in
the head of the page; the summary says the rest in a few lines, each a tap from the
tab that holds it - the last thing said, which the person carries
(`last_conversation_*`), their appointments, which the head already asked for, and
the lines below.

Each module adds its own the way it adds a place to the client area
(`registra_voce`): the agenda what the person has going (cycles, subscriptions, a
place in a waiting list), invoicing what is left to collect, the forms what the
person owes, the quotes the ones waiting for an answer. A line decides for itself
what the session reads, and says nothing rather than refusing: the summary opens
for whoever reads the person. A line that fails is left out and logged, and the
rest still opens.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import frappe

from crm.permissions import livelli


@dataclass(frozen=True)
class Voce:
	chiave: str
	#: What the line says about this person (a CRM Lead) to the session: left out
	#: when it says nothing.
	per_persona: Callable[[str], Any]


_voci: dict[str, Voce] = {}


def registra_voce(voce: Voce) -> None:
	_voci[voce.chiave] = voce


def voci() -> list[Voce]:
	return list(_voci.values())


@frappe.whitelist()
def get_summary(lead: str) -> dict[str, Any]:
	"""Every line that has something to say about this person, by its key."""
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	livelli.carica()
	fatto: dict[str, Any] = {}
	for voce in _voci.values():
		detti = len(frappe.local.message_log)
		try:
			valore = voce.per_persona(lead)
		except frappe.PermissionError:
			# a refusal is a line the session does not read, not a page that
			# does not open: what it said goes with it
			del frappe.local.message_log[detti:]
			continue
		except Exception:
			del frappe.local.message_log[detti:]
			frappe.log_error(
				title=f"Summary line {voce.chiave} not read",
				reference_doctype="CRM Lead",
				reference_name=lead,
			)
			continue
		if valore:
			fatto[voce.chiave] = valore
	return fatto


# ------------------------------------------------------------------ the base's lines

#: A task still to do: not done, not given up.
COMPITI_CHIUSI = ("Done", "Canceled")
#: How many of a list the summary names; the rest is a number and its tab.
QUANTI = 3


def da_fare(lead: str) -> dict | None:
	"""The tasks on the person still to do, the ones due first, then the ones with
	no day. The Tasks tab shows the same ones (`get_linked_tasks`)."""
	righe = frappe.get_list(
		"CRM Task",
		filters={
			"reference_doctype": "CRM Lead",
			"reference_docname": lead,
			"status": ["not in", COMPITI_CHIUSI],
		},
		fields=["name", "title", "status", "priority", "due_date", "assigned_to"],
		limit_page_length=0,
	)
	if not righe:
		return None
	righe.sort(key=lambda riga: (riga.due_date is None, str(riga.due_date or "")))
	return {
		"count": len(righe),
		"tasks": [
			{**riga, "due_date": str(riga.due_date) if riga.due_date else None} for riga in righe[:QUANTI]
		],
	}


def in_corso(lead: str) -> dict | None:
	"""What the person has going beyond one appointment: the cycles of sessions
	going on, the subscriptions running or suspended, their places in a waiting
	list - what the Subscriptions tab holds, each by the capability that reads it
	there."""
	fatto = {}
	if livelli.puo("agenda.vedi"):
		fatto["cycles"] = _cicli(lead)
	if livelli.puo("agenda.vedi") or livelli.puo("agenda.abbonamenti"):
		fatto["subscriptions"] = _abbonamenti(lead)
	if livelli.puo("agenda.attese"):
		fatto["waiting"] = _in_attesa(lead)
	fatto = {chiave: righe for chiave, righe in fatto.items() if righe}
	return fatto or None


def _nome_del_servizio(servizio: str | None) -> str | None:
	if not servizio:
		return None
	return frappe.db.get_value("CRM Service", servizio, "service_name") or servizio


def _cicli(lead: str) -> list[dict]:
	from crm.scheduling import cicli
	from crm.scheduling import cicli_regole as C

	fatto = []
	for nome in frappe.get_list(
		cicli.CICLO, filters={"lead": lead, "status": C.ATTIVO}, pluck="name", order_by="creation asc"
	):
		riga = cicli.riga(frappe.get_doc(cicli.CICLO, nome))
		# a cycle past its last day is not going on, whatever it still holds
		if riga["status"] != C.ATTIVO:
			continue
		fatto.append(
			{
				"name": riga["name"],
				"service": _nome_del_servizio(riga["service"]),
				"counts": riga["counts"],
				"next": riga["next"],
				"valid_until": riga["valid_until"],
			}
		)
	return fatto


def _abbonamenti(lead: str) -> list[dict]:
	from crm.scheduling import abbonamenti
	from crm.scheduling import abbonamenti_regole as R

	fatto = []
	for nome in frappe.get_list(
		abbonamenti.ABBONAMENTO,
		filters={"lead": lead, "status": ["in", (R.ATTIVO, R.SOSPESO)]},
		pluck="name",
		order_by="starts_on asc",
	):
		riga = abbonamenti.riga(frappe.get_doc(abbonamenti.ABBONAMENTO, nome))
		if riga["status"] not in (R.ATTIVO, R.SOSPESO):
			continue
		fatto.append(
			{
				key: riga[key]
				for key in (
					"name",
					"subscription_type",
					"status",
					"ends_on",
					"entries",
					"entries_count",
					"used",
					"suspended_until",
				)
			}
		)
	return fatto


def _in_attesa(lead: str) -> list[dict]:
	from crm.scheduling import attese
	from crm.scheduling import attese_regole as R

	fatto = []
	for nome in frappe.get_list(
		attese.VOCE,
		filters={"lead": lead, "status": ["in", R.APERTE]},
		pluck="name",
		order_by="creation asc",
	):
		voce = attese.descrivi(frappe.get_doc(attese.VOCE, nome))
		fatto.append(
			{
				key: voce.get(key)
				for key in (
					"name",
					"service_name",
					"staff_name",
					"class_session",
					"class_starts_on",
					"until",
					"status",
					"urgent",
					"choice",
					"days",
					"since",
				)
			}
		)
	return fatto


def assenze(lead: str) -> dict | None:
	"""The appointments the person did not show up to in the last year, for whoever
	reads the agenda: as the online booking counts them (`booking_rules.missed`)."""
	if not livelli.puo("agenda.vedi"):
		return None
	from frappe.utils import add_months, now_datetime

	appuntamento = frappe.qb.DocType("CRM Appointment")
	posto = frappe.qb.DocType("CRM Appointment Participant")
	adesso = now_datetime()
	righe = (
		frappe.qb.from_(posto)
		.join(appuntamento)
		.on(posto.parent == appuntamento.name)
		.select(appuntamento.name, appuntamento.starts_on)
		.where((posto.party_type == "CRM Lead") & (posto.party == lead))
		.where(appuntamento.starts_on.between(add_months(adesso, -12), adesso))
		.where(
			(posto.status == "No Show")
			| ((appuntamento.status == "No Show") & posto.status.isin(("Booked", "No Show")))
		)
		.orderby(appuntamento.starts_on)
		.run(as_dict=True)
	)
	giorni = {riga.name: riga.starts_on for riga in righe}
	if not giorni:
		return None
	return {"count": len(giorni), "last": str(max(giorni.values()))}


def trattative(lead: str) -> dict | None:
	"""The person's deals still open, the last one moved first: the stage each is
	at, in the pipeline it belongs to."""
	if not livelli.puo("trattative.vedi"):
		return None
	from crm.api.lead import deal_names_of

	nomi = deal_names_of(lead)
	if not nomi:
		return None
	righe = frappe.get_list(
		"CRM Deal",
		filters={"name": ["in", sorted(nomi)]},
		fields=["name", "status", "pipeline", "deal_value", "currency", "modified"],
		order_by="modified desc",
		limit_page_length=0,
	)
	chiuse = set(frappe.get_all("CRM Deal Status", filters={"type": ["in", ("Won", "Lost")]}, pluck="name"))
	aperte = [riga for riga in righe if riga.status not in chiuse]
	if not aperte:
		return None
	return {
		"count": len(aperte),
		"deals": [
			{
				"name": riga.name,
				"status": riga.status,
				"pipeline": riga.pipeline,
				"deal_value": riga.deal_value,
				"currency": riga.currency,
			}
			for riga in aperte[:QUANTI]
		],
	}


def registra() -> None:
	"""The base's lines; the modules add theirs from their own `registra()`."""
	registra_voce(Voce("in_progress", in_corso))
	registra_voce(Voce("tasks", da_fare))
	registra_voce(Voce("deals", trattative))
	registra_voce(Voce("no_shows", assenze))
