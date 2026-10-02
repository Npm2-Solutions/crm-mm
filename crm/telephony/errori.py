# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Twilio's errors in DottorCloud's words, in the reader's language (doc 52, fifth
part). The sentences and the codes they answer are in ``errori_regole``."""

from __future__ import annotations

from frappe import _

from crm.marchio import con_nome
from crm.telephony import errori_regole as R


def in_parole(codice, testo: str | None = None) -> str:
	"""What a code of Twilio's means here; for one DottorCloud has no sentence of
	its own, Twilio's words with the code."""
	numero = R.codice(codice)
	if frase := R.ERRORI.get(numero):
		return con_nome(_(frase))
	testo = (testo or "").strip()
	if numero and testo:
		return _("Twilio says: {0} (error {1})").format(testo, numero)
	if numero:
		return _("Twilio refused it (error {0}).").format(numero)
	return testo or _("Twilio refused it.")
