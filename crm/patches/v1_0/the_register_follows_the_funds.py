# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The qualification register as the funds and the Agenzia read it (05/10/2026).

Only where a centre's record still holds what DottorCloud shipped; what a centre
changed stays as it wrote it:

- Agrotecnico and perito agrario are two ENPAIA funds, 4% and 2%: the one entry
  becomes the agrotecnico's, and the perito agrario's is seeded.
- An STP produces business income (Ris. 35/E/2018), no withholding: the studio
  associato keeps its own entry, and the STP's is seeded.
- The commercial agent's commission was withheld on the whole amount: DottorCloud
  does not compute a reduced base nor ENASARCO, so the entry is switched off.
- The midwife is in the INPS separate management, 4% optional.
- The psychologist's and the vet's notes say what changes in 2027.
"""

import frappe

QUALIFICA = "CRM Professional Qualification"

#: code -> (old shipped name, old shipped notes)
VECCHIE = {
	"agrotecnico": ("Agrotecnico / perito agrario", None),
	"agente_commercio": (
		"Agente e rappresentante di commercio",
		"Commissions do not follow the professional pattern: the withholding is 23% of a reduced base, "
		"and ENASARCO is a contribution split with the principal, not a rivalsa charged to the client. "
		"Configure it explicitly.",
	),
	"associazione_professionale": (
		"Associazione professionale / STP",
		"An association keeps the withholding but as a legal person (RT02). The fund depends on the "
		"professionals it groups.",
	),
	"ostetrica": (
		"Ostetrica / ostetrico",
		"The reference fund has to be confirmed: nothing is assumed here.",
	),
	"psicologo": (
		"Psicologo / psicoterapeuta",
		"ENPAP contributo integrativo 2% on the gross fee, mandatory and shown on the invoice.",
	),
	"veterinario": (
		"Medico veterinario",
		"Its own deadline in mid-March: a separate batch. Veterinary companies (S.r.l., STP) have the "
		"option, not the duty.",
	),
}


def _spedite(testo: str | None) -> set[str]:
	"""The shipped words in every language DottorCloud ships them in."""
	if not testo:
		return {""}
	return {testo, frappe._(testo, lang="it")}


def execute():
	if not frappe.db.exists("DocType", QUALIFICA):
		return
	from crm import lingue
	from crm.invoicing.engine.professioni import professione as ordinaria
	from crm.invoicing.install import parole_di, semina_qualifiche
	from crm.tessera_sanitaria.engine.professioni import PROFESSIONI
	from crm.tessera_sanitaria.install import semina_qualifiche as semina_sanitarie

	lingua = lingue.del_centro()
	for codice, (nome, note) in VECCHIE.items():
		attuale = frappe.db.get_value(
			QUALIFICA, codice, ["qualification_name", "notes", "fund_type"], as_dict=True
		)
		if not attuale:
			continue
		# a centre that wrote its own words keeps them, and its choices
		if (attuale.qualification_name or "").strip() not in _spedite(nome) or (
			attuale.notes or ""
		).strip() not in _spedite(note):
			continue
		if codice == "agente_commercio":
			frappe.db.set_value(QUALIFICA, codice, "enabled", 0)
			continue
		professione = PROFESSIONI.get(codice) or ordinaria(codice)
		valori = parole_di(professione, lingua)
		if codice == "ostetrica" and not attuale.fund_type:
			valori.update({"fund_type": "TC22", "fund_rate": 4, "fund_mandatory": 0})
		frappe.db.set_value(QUALIFICA, codice, valori)

	# the entries that are new: the perito agrario, the STP
	semina_qualifiche()
	semina_sanitarie()
