# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Starting a visit from the last one, without a site.

What the last visit on the same sheet answered goes into the new draft through the
version published now (`crm.moduli.schema.pulisci`): a question that is no longer
there, or asks for another kind of answer, drops. What is evidence of that visit
never comes along: a signature, an attachment, a consent - each is given again,
or it was not given.
"""

from __future__ import annotations

from crm.moduli import schema as S

#: The kinds of answer that are evidence of the visit they were given in.
MAI_RICOPIATI = frozenset({S.FIRMA, S.FILE})
#: The components that record a yes of the person's, given at that visit.
COMPONENTI_MAI_RICOPIATI = frozenset({"consent", "signature", "attachment"})


def si_ricopia(campo: dict) -> bool:
	tipo = S.componente(campo.get("type"))
	return bool(
		tipo
		and tipo.risposta
		and tipo.valore not in MAI_RICOPIATI
		and campo.get("type") not in COMPONENTI_MAI_RICOPIATI
	)


def da_ricopiare(schema, risposte: dict | None) -> dict:
	"""The last visit's ``risposte`` as the new version ``schema`` keeps them."""
	ammessi = {campo.get("id") for campo in S.campi(schema) if si_ricopia(campo)}
	scelte = {chiave: valore for chiave, valore in (risposte or {}).items() if chiave in ammessi}
	puliti, _errori, _stato = S.pulisci(schema, scelte)
	return puliti
