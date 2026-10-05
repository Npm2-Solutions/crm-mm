# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Features: what the centre has, what it used this month,
and how it grows.

The plan is the agency's to write (`CRM Plan`, System Manager only). The centre sees
it here: first what the product it signed up for comprises - the base and its
vertical, DottorCloud's clinic with the patient area - on, nothing to switch; then
the extras, each with what it adds. It can do one thing on its own: start the 14-day
trial of an extra it does not have. The request goes to the agency, which confirms it
and bills it from the month after (listino.md, "Come si amplia il piano"). Going over
the size never blocks anything: the page says so, and proposes the size above.
"""

from __future__ import annotations

from collections.abc import Iterable

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now, nowdate

from crm import verticali
from crm.fcrm.doctype.crm_plan.crm_plan import (
	AMBULATORI,
	AVVISO,
	CREDITI_SDI,
	FIRME_INCLUSE,
	crediti_sdi,
)
from crm.permissions import livelli
from crm.permissions.catalogo import BASE
from crm.permissions.livelli import ModuloPiano, richiede

#: Days a trial started from the CRM lasts.
GIORNI_DI_PROVA = 14

#: The plan's words for the registry's states, as the page shows them.
STATO = {
	livelli.ATTIVO: "active",
	livelli.PROVA: "trial",
	livelli.SOLA_LETTURA: "read_only",
	livelli.SPENTO: "off",
}


def compresi(moduli: Iterable[ModuloPiano], verticale: str | None) -> set[str]:
	"""What the product the centre signed up for comprises: the base and what it
	comprises (the client area), the module of its vertical - the clinic, for
	DottorCloud - and what that comprises. The other modules are extras, which the centre adds when it needs them."""
	per_chiave = {modulo.chiave: modulo for modulo in moduli}
	dentro: set[str] = set()
	da_vedere = [BASE, *([verticale] if verticale else [])]
	while da_vedere:
		chiave = da_vedere.pop()
		if chiave in dentro or chiave not in per_chiave:
			continue
		dentro.add(chiave)
		da_vedere.extend(per_chiave[chiave].comprende)
	return dentro


@frappe.whitelist()
@richiede("piano.vedi")
def get_plan() -> dict:
	"""The plan as the centre sees it."""
	piano = frappe.get_cached_doc("CRM Plan")
	righe = {riga.module: riga for riga in piano.modules}
	stati = livelli.moduli_attivi()
	verticale = verticali.attiva()
	nel_prodotto = compresi(livelli.moduli_piano(), verticale.piano if verticale else None)
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
				# part of the product: on, nothing to switch; the others are extras
				"included": modulo.chiave in nel_prodotto,
				# where one sets it up: the settings' pages, as the menu names them
				"settings": list(modulo.impostazioni),
				"listed": bool(riga),
				"included_in_service": bool(riga and riga.source == "Agency service"),
				# on because a module the plan has comprises it: the clinic, the client area
				"comprised_by": [
					altro.etichetta
					for altro in livelli.moduli_piano()
					if modulo.chiave in altro.comprende
					and livelli.stato_modulo(altro.chiave, stati) != livelli.SPENTO
				],
				"service": riga.service if riga else None,
				"trial_until": riga.trial_until if riga else None,
				"expires_on": riga.expires_on if riga else None,
				"can_start_trial": stato == livelli.SPENTO and livelli.puo("piano.amplia"),
			}
		)
	sale = ambulatori()
	comprese = AMBULATORI.get(piano.size) if piano.size else None
	accesi = {modulo["key"] for modulo in moduli if modulo["state"] in ("active", "trial")}
	return {
		"size": piano.size or None,
		"rooms": {
			"count": sale,
			"included": comprese,
			"over": bool(comprese and sale > comprese),
		},
		"modules": moduli,
		"usage": consumi(piano.size, accesi),
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
		header=frappe.utils.escape_html(_("A trial of {0} has started").format(modulo)),
		with_container=True,
		message=_(
			"{0} ({1}) started the {2}-day trial of {3} on {4}. Confirm it in the site's plan (Settings > Plan) to bill it "
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


def ambulatori() -> int:
	"""What the size counts (listino.md): the ambulatori, the agenda's rooms where
	one visits or treats - a physiotherapy gym counts as one. Practitioners and
	users are unlimited."""
	return frappe.db.count("CRM Resource", {"resource_type": "Room", "enabled": 1})


def consumi(taglia: str | None = None, accesi: set[str] = frozenset(), giorno: str | None = None) -> dict:
	"""What the centre used, as the agency bills it: the SdI credits and the
	advanced signatures of the year, each with what the plan includes. WhatsApp
	is not counted, Meta bills the centre; nor are calls and SMS, which Twilio
	bills to whoever owns the account, and Twilio's page shows what they cost."""
	giorno = getdate(giorno or nowdate())
	anno = ["between", [getdate(f"{giorno.year}-01-01"), getdate(f"{giorno.year}-12-31")]]
	uso = {"sdi_credits": None, "signatures": None}
	if "fatturazione" in accesi:
		inviate = frappe.get_all(
			"CRM Invoice",
			filters={"channel": "sdi", "sdi_sent_on": anno},
			fields=["sdi_status", "recipient_type"],
		)
		ricevute = frappe.db.count("CRM Supplier Invoice", {"creation": anno})
		uso["sdi_credits"] = {
			"used": crediti_sdi([(r.sdi_status, r.recipient_type) for r in inviate], ricevute),
			"included": CREDITI_SDI.get(taglia) if taglia else None,
		}
	if "firma" in accesi:
		uso["signatures"] = {
			"used": frappe.db.count(
				"CRM Form", {"provider": ["is", "set"], "provider_status": "Signed", "signed_on": anno}
			),
			"included": FIRME_INCLUSE,
		}
	for voce in uso.values():
		if voce and voce.get("included"):
			voce["warn"] = voce["used"] >= AVVISO * voce["included"]
	return uso
