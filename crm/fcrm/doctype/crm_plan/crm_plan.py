# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's plan: which modules it has, and until when.

It is the second key of every capability (`crm.permissions.livelli`): a capability
holds when the person's level grants it *and* its module is on here. Only the agency
writes this document. The centre reads it in Settings > Plan, and can start the
trial of a module it does not have yet.

A module the plan does not list keeps its default: what the CRM did before plans
existed stays on, so no site lost anything the day plans arrived; a new module
starts off.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

from crm.permissions import livelli


class CRMPlan(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_plan_module.crm_plan_module import CRMPlanModule

		agency_email: DF.Data | None
		modules: DF.Table[CRMPlanModule]
		notes: DF.SmallText | None
		size: DF.Literal["", "Solo", "Studio", "Centre", "Polyclinic", "Large"]
		storage_gb: DF.Int
	# end: auto-generated types

	def validate(self):
		livelli.carica()
		noti = {modulo.chiave for modulo in livelli.moduli_piano()}
		visti = set()
		for riga in self.modules:
			riga.module = (riga.module or "").strip().lower()
			if riga.module not in noti:
				frappe.throw(
					_("Row {0}: {1} is not a module of the plan. Known: {2}").format(
						riga.idx, frappe.bold(riga.module), ", ".join(sorted(noti))
					)
				)
			if riga.module in visti:
				frappe.throw(_("Row {0}: {1} is listed twice").format(riga.idx, frappe.bold(riga.module)))
			visti.add(riga.module)
			if riga.status == "Trial" and not riga.trial_until:
				frappe.throw(_("Row {0}: a trial needs the day it ends").format(riga.idx))

	def on_update(self):
		# on_update runs before Frappe drops the cached document: whoever reads the
		# plan after this, in this same request, reads this one. The clinic switched
		# on here, and the dashboard asking which features the site has, among them
		frappe.clear_document_cache(self.doctype, self.name)
		livelli.dimentica_cache()
		from crm.dashboard import features

		features.forget()


#: The document's words for the registry's states.
STATI = {
	"Active": livelli.ATTIVO,
	"Trial": livelli.PROVA,
	"Read only": livelli.SOLA_LETTURA,
	"Off": livelli.SPENTO,
}

# What the listino says (docs/gestionale-medico/listino.md, 01/10/2026).

#: Ambulatori each size covers - rooms where one visits or treats, as the agenda's
#: rooms; None: past ten, each one more is paid.
AMBULATORI = {"Solo": 1, "Studio": 2, "Centre": 5, "Polyclinic": 10, "Large": None}

#: SdI credits a year that come with invoicing, by size.
CREDITI_SDI = {"Solo": 240, "Studio": 500, "Centre": 1200, "Polyclinic": 2400, "Large": 2400}

#: Signatures a year that come with the advanced signature. The phone counts
#: nothing: a year's fee switches it on, and calls, numbers and SMS are paid to
#: Twilio by whoever owns the account (the listino, 03/10/2026).
FIRME_INCLUSE = 2000

#: Used past this share of what is included, the page warns (the listino: at 80%).
AVVISO = 0.8

#: An invoice's SdI states that spent no credit: never sent, refused by the SdI
#: for its format, failed on the way.
SENZA_CREDITO = frozenset({"non_applicabile", "da_inviare", "scartata", "errore"})


def crediti_sdi(inviate, ricevute: int) -> int:
	"""SdI credits used: one an invoice sent or received, three one sent to the
	public administration; one the SdI refused for its format costs nothing.
	``inviate``: the (SdI state, recipient type) of each invoice sent. Pure."""
	spesi = sum(
		3 if destinatario == "pubblica_amministrazione" else 1
		for stato, destinatario in inviate
		if stato not in SENZA_CREDITO
	)
	return spesi + ricevute


def stato_della_riga(
	status: str,
	trial_until: datetime.date | str | None,
	expires_on: datetime.date | str | None,
	oggi: datetime.date,
) -> str:
	"""What a row of the plan means today.

	A module that ended - its trial over, or past its expiry - is not switched off:
	it turns read only. Its data stays, and only what writes goes away.
	"""
	stato = STATI.get(status, livelli.ATTIVO)
	if stato == livelli.SPENTO:
		return stato
	if expires_on and getdate(expires_on) < oggi:
		return livelli.SOLA_LETTURA
	if stato == livelli.PROVA and trial_until and getdate(trial_until) < oggi:
		return livelli.SOLA_LETTURA
	return stato


def stati_moduli() -> dict[str, str]:
	"""Module -> state, for the modules the plan lists. The others keep their default."""
	try:
		piano = frappe.get_cached_doc("CRM Plan")
	except frappe.DoesNotExistError:
		# before the doctype exists: during the migration that creates it
		return {}
	oggi = getdate(nowdate())
	return {
		riga.module: stato_della_riga(riga.status, riga.trial_until, riga.expires_on, oggi)
		for riga in piano.modules
	}
