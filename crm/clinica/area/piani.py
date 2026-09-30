# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's plans in the patient area, beside the CRM's (`crm.piani.area`): a
diet's shopping list. The dental care plans are quotes (`crm.preventivi.area`).

- **The shopping list** (`area_shopping_list`): what to buy for the days ahead -
  the diet's foods and how much, the groups to choose from with their portions -
  from two days back to five weeks ahead.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, getdate

from crm.area.api import _mia
from crm.clinica import piani
from crm.clinica import piani_regole as R
from crm.piani import area as area_dei_piani
from crm.piani import regole


@frappe.whitelist()
def area_shopping_list(person: str, plan: str, start: str | None = None, days: int = 7) -> dict:
	"""What to buy for the days ahead: the diet's foods and how much, the groups
	to choose from with their portions. From two days back to five weeks ahead."""
	_mia(person)
	doc = area_dei_piani.della_persona(person, plan)
	if doc.plan_type not in R.DIETE_TIPI:
		frappe.throw(_("Only a diet has a shopping list"))
	oggi = getdate()
	dal = getdate(start) if start else oggi
	if not (add_days(oggi, -regole.GIORNI_RECUPERO) <= dal <= add_days(oggi, R.MAX_GIORNI_SPESA)):
		frappe.throw(_("This day is not shown"))
	# the plan's own words, not the tables': no calories on a shopping list
	return piani.lista_per_il_paziente(doc, dal, days)
