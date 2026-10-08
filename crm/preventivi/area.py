# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The quotes in the person's area: those proposed to them and going on, in the
words they read - the services, what is done, the sums. A proposed one still
valid is answered there (`crm.preventivi.firma`): accepted and signed, or not."""

from __future__ import annotations

import frappe
from frappe.utils import cint, flt, get_fullname, getdate

from crm.area import accesso, anteprima
from crm.area.api import _mia
from crm.demo import guardie
from crm.preventivi import rate
from crm.preventivi import rate_regole as RR
from crm.preventivi import regole as R
from crm.preventivi.api import DOCTYPE, dettaglio_della_voce

APPUNTAMENTO = "CRM Appointment"
NELL_AREA = (R.PROPOSTO, R.ACCETTATO, R.COMPLETATO)


def _pagamento(doc, persona: str, online: bool, fatture: dict) -> dict | None:
	"""A quote paid in instalments, as the person reads it: each payment, what is paid
	and what comes next, «Pay online» on an instalment invoiced and still to pay."""
	if doc.payment != RR.A_RATE or not doc.instalments:
		return None
	righe = rate.righe(doc)
	return {
		"summary": rate.riassunto(doc, lette=righe) if doc.status != R.BOZZA else None,
		"count": sum(1 for riga in righe if riga["kind"] == RR.RATA and riga["status"] != RR.ANNULLATA),
		"rows": [
			{
				"kind": riga["kind"],
				"number": riga["number"],
				"due_on": riga["due_on"],
				"amount": riga["amount"],
				"status": riga["status"],
				"late": riga["late"],
				# its invoice, while it is the person's to pay: «Pay online»
				"invoice": riga["invoice"] if riga["invoice"] in fatture else None,
				"to_pay": bool(
					riga["invoice"] in fatture
					and not fatture[riga["invoice"]].collected_on
					and fatture[riga["invoice"]].sdi_status != "scartata"
				),
				"pay_online": bool(
					online
					and riga["status"] == RR.FATTURATA
					and riga["invoice"] in fatture
					and not fatture[riga["invoice"]].collected_on
					and not guardie.mai_a_stripe(("CRM Invoice", riga["invoice"]))
				),
			}
			for riga in righe
			if riga["status"] != RR.ANNULLATA
		],
	}


def della_persona(persona: str) -> list[dict]:
	"""The quotes proposed to the person and going on, the most recent first."""
	from crm.area.api import _fatture
	from crm.pagamenti import collegamento

	online = (
		collegamento.collegato()
		and not anteprima.in_anteprima()
		and not guardie.mai_a_stripe(("CRM Lead", persona))
	)
	fatture = {riga.name: riga for riga in _fatture(persona)}
	fatto = []
	for nome in frappe.get_all(
		DOCTYPE,
		filters={"lead": persona, "status": ("in", NELL_AREA)},
		pluck="name",
		order_by="creation desc",
	):
		doc = frappe.get_doc(DOCTYPE, nome)
		voci = [voce for voce in doc.items if voce.status != R.ANNULLATA]
		valido_fino = getdate(doc.valid_until) if doc.valid_until else None
		fatto.append(
			{
				"name": doc.name,
				"title": doc.title,
				"status": doc.status,
				# still to answer here, or past its day; signed here, and when
				"can_answer": R.da_rispondere(doc.status, valido_fino, getdate()) is None,
				"expired": doc.status == R.PROPOSTO and bool(valido_fino and valido_fino < getdate()),
				"signed_on": str(doc.signed_on) if doc.signed_on else None,
				"has_pdf": bool(doc.signed_pdf or doc.quote_pdf),
				"clinical": cint(doc.clinical),
				"practitioner_name": get_fullname(doc.practitioner),
				"valid_until": str(doc.valid_until) if doc.valid_until else None,
				"patient_notes": doc.patient_notes,
				"currency": doc.currency,
				"totals": R.totali([voce.as_dict() for voce in voci]),
				"payment": _pagamento(doc, persona, online, fatture),
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
	riga = _mia(person, anche_in_anteprima=True)
	return {
		"quotes": anteprima.filtra(DOCTYPE, della_persona(person)),
		# a code verified just now: the signature knows who signs
		"verified": accesso.verificato_da_poco() and not anteprima.in_anteprima(),
		# whoever only follows the person reads, and does not answer
		"can_answer": riga.relation in (accesso.SE_STESSO, accesso.TUTORE) and not anteprima.in_anteprima(),
	}
