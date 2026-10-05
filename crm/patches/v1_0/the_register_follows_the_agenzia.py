# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The qualification register as the Agenzia reads it (05/10/2026).

The register is seeded once and the practice owns it after that, so what
DottorCloud got wrong reaches a centre only here, and only where the centre's
records still hold DottorCloud's own words:

- A facility's visit is exempt under n. 18, like anybody's (Ris. 39/E/2004): n. 19
  is hospital care. The facilities' qualifications and the service cards the
  healthcare preset wrote cite n. 18.
- The massaggiatore capo bagnino has no report to the Sistema TS yet (the Agenzia's
  FAQ of 11/03/2026): exempt, out of the SdI, on paper or PDF.
"""

from datetime import date

import frappe

QUALIFICA = "CRM Professional Qualification"
SCHEDA = "CRM Billable Service"

#: What the register shipped for the two facilities.
VECCHIO_N19 = "art. 10, n. 19, DPR 633/72 (dal 2027: art. 37, c. 1, lett. u, D.Lgs. 10/2026)"
#: What the healthcare preset wrote on a facility's service cards.
VECCHIA_SCHEDA_N19 = (
	"Operazione esente da IVA ai sensi dell'art. 10, n. 19, del D.P.R. 633/1972 "
	"(dal 01/01/2027: art. 37, comma 1, lett. u), del D.Lgs. 10/2026)."
)
VECCHIO_NOME_MCB = "Massoterapista (massaggiatore capo bagnino)"
VECCHIE_NOTE_MCB = (
	"Arte ausiliaria ex art. 99 R.D. 1265/1934: the service is EXEMPT under art. 10 n. 18, the "
	"electronic invoice through the SdI is FORBIDDEN, the Sistema TS report is DUE (Ris. AdE 9/2026).",
	"Arte ausiliaria ex art. 99 R.D. 1265/1934: la prestazione è ESENTE ai sensi dell'art. 10 n. 18, "
	"la fattura elettronica allo SdI è VIETATA, la comunicazione al Sistema TS è DOVUTA (Ris. AdE 9/2026).",
)


def execute():
	if not frappe.db.exists("DocType", QUALIFICA):
		return
	from crm import lingue
	from crm.invoicing.engine import diciture
	from crm.invoicing.install import parole_di
	from crm.tessera_sanitaria.engine.professioni import ESENZIONE_PROFESSIONISTA, PROFESSIONI

	for codice in ("struttura_autorizzata", "struttura_accreditata"):
		if frappe.db.get_value(QUALIFICA, codice, "exemption_reference") == VECCHIO_N19:
			frappe.db.set_value(QUALIFICA, codice, "exemption_reference", ESENZIONE_PROFESSIONISTA)

	if frappe.db.exists("DocType", SCHEDA):
		nuova = diciture.esenzione(date(2026, 1, 1))
		for nome in frappe.get_all(SCHEDA, filters={"exemption_reference": VECCHIA_SCHEDA_N19}, pluck="name"):
			frappe.db.set_value(SCHEDA, nome, "exemption_reference", nuova)

	mcb = frappe.db.get_value(
		QUALIFICA,
		"massoterapista",
		["ts_required", "qualification_name", "notes"],
		as_dict=True,
	)
	if mcb:
		valori = {}
		# a centre that switched the report off already, or changed the words, keeps them
		if mcb.ts_required and (mcb.notes or "").strip() in VECCHIE_NOTE_MCB:
			valori.update({"ts_required": 0, "ts_required_since": 0})
			valori.update(parole_di(PROFESSIONI["massoterapista"], lingue.del_centro()))
		elif (mcb.qualification_name or "").strip() == VECCHIO_NOME_MCB:
			valori["qualification_name"] = parole_di(PROFESSIONI["massoterapista"], lingue.del_centro())[
				"qualification_name"
			]
		if valori:
			frappe.db.set_value(QUALIFICA, "massoterapista", valori)
