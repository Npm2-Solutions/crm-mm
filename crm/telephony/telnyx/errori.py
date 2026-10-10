# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Telnyx's errors in DottorCloud's words, in the reader's language (doc 65). The
sentences and the codes they answer are in ``errori_regole``."""

from __future__ import annotations

from frappe import _

from crm.marchio import con_nome
from crm.telephony.telnyx import errori_regole as R


def in_parole(codice, testo: str | None = None) -> str:
	"""What a code of Telnyx's means here; for one DottorCloud has no sentence of
	its own, Telnyx's words with the code."""
	numero = R.codice(codice)
	if frase := R.ERRORI.get(numero):
		return con_nome(_(frase))
	testo = (testo or "").strip()
	if numero and testo:
		return _("Telnyx says: {0} (error {1})").format(testo, numero)
	if numero:
		return _("Telnyx refused it (error {0}).").format(numero)
	return testo or _("Telnyx refused it.")


def della_chiamata(sip: str | None) -> str:
	"""Why a call did not leave, from the SIP reason Telnyx gave it ("403 D13");
	'' for one DottorCloud has no sentence for."""
	for parola in (sip or "").replace(",", " ").split():
		if frase := R.CHIAMATE.get(parola.upper()):
			return _(frase)
	return ""
