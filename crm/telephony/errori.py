# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The carrier's errors in DottorCloud's words, in the reader's language (doc 52,
fifth part; doc 64). The sentences and the codes they answer are in
``errori_regole`` for Twilio, in ``telnyx.errori_regole`` for Telnyx."""

from __future__ import annotations

from frappe import _

from crm.marchio import con_nome
from crm.telephony import errori_regole as R


def in_parole(codice, testo: str | None = None, operatore: str = "twilio") -> str:
	"""What a code of the carrier's (Twilio's unless ``operatore`` says Telnyx)
	means here; for one DottorCloud has no sentence of its own, the carrier's words
	with the code."""
	if operatore == "telnyx":
		from crm.telephony.telnyx import errori

		return errori.in_parole(codice, testo)
	numero = R.codice(codice)
	if frase := R.ERRORI.get(numero):
		return con_nome(_(frase))
	testo = (testo or "").strip()
	if numero and testo:
		return _("Twilio says: {0} (error {1})").format(testo, numero)
	if numero:
		return _("Twilio refused it (error {0}).").format(numero)
	return testo or _("Twilio refused it.")
