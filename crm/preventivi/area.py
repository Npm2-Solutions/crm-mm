# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The quotes in the person's area: those proposed to them and going on, in the
words they read - the services, what is done, the sums."""

from __future__ import annotations

import frappe
from frappe.utils import cint, flt, get_fullname

from crm.area import anteprima
from crm.area.api import _mia
from crm.preventivi import regole as R
from crm.preventivi.api import DOCTYPE, dettaglio_della_voce

APPUNTAMENTO = "CRM Appointment"
NELL_AREA = (R.PROPOSTO, R.ACCETTATO, R.COMPLETATO)


def della_persona(persona: str) -> list[dict]:
	"""The quotes proposed to the person and going on, the most recent first."""
	fatto = []
	for nome in frappe.get_all(
		DOCTYPE,
		filters={"lead": persona, "status": ("in", NELL_AREA)},
		pluck="name",
		order_by="creation desc",
	):
		doc = frappe.get_doc(DOCTYPE, nome)
		voci = [voce for voce in doc.items if voce.status != R.ANNULLATA]
		fatto.append(
			{
				"name": doc.name,
				"title": doc.title,
				"status": doc.status,
				"practitioner_name": get_fullname(doc.practitioner),
				"valid_until": str(doc.valid_until) if doc.valid_until else None,
				"patient_notes": doc.patient_notes,
				"currency": doc.currency,
				"totals": R.totali([voce.as_dict() for voce in voci]),
				"items": [
					{
						"description": voce.description,
						"detail": dettaglio_della_voce(voce),
						"phase": cint(voce.phase) or 1,
						"amount": flt(voce.amount),
						"status": voce.status,
						"when": str(frappe.db.get_value(APPUNTAMENTO, voce.appointment, "starts_on"))
						if voce.appointment and voce.status == R.PRENOTATA
						else None,
					}
					for voce in voci
				],
			}
		)
	return fatto


def nell_area(persona: str) -> int:
	"""How many quotes the area shows: proposed or going on."""
	return frappe.db.count(DOCTYPE, {"lead": persona, "status": ("in", (R.PROPOSTO, R.ACCETTATO))})


@frappe.whitelist()
def area_quotes(person: str) -> dict:
	"""The quotes proposed to the person and going on; in the centre's preview,
	only those whoever previews reads."""
	_mia(person, anche_in_anteprima=True)
	return {"quotes": anteprima.filtra(DOCTYPE, della_persona(person))}
