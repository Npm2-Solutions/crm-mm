# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
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
		livelli.dimentica_cache()


#: The document's words for the registry's states.
STATI = {
	"Active": livelli.ATTIVO,
	"Trial": livelli.PROVA,
	"Read only": livelli.SOLA_LETTURA,
	"Off": livelli.SPENTO,
}

#: Agendas each size covers; None is "no limit".
AGENDE = {"Solo": 1, "Studio": 3, "Centre": 8, "Polyclinic": 15, "Large": None}


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
