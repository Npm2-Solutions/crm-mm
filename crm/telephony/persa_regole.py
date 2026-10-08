# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered, without a site (doc 52).

- **Somebody the centre knows**: the automations hear «Missed Call»; what they do
  is the centre's (the recipe texts the booking page a minute later).
- **A number nobody knows**: where the centre wants it, one SMS of service to the
  number that called - an Italian or a foreign mobile of the countries the centre
  calls, never a premium-rate number nor a landline, which reads no SMS - at most
  once a day for each number.
"""

from __future__ import annotations

import datetime

import phonenumbers

from crm.telephony import uscita_regole as U

#: The kinds of number that read an SMS.
CELLULARI = frozenset(
	{phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE}
)


def a_chi_scrivere(numero: str | None, consentiti) -> str | None:
	"""The number to text, as Twilio takes it (E.164); ``None`` when it is not a
	mobile, is premium-rate or of a country the centre does not call."""
	if U.si_chiama(numero, consentiti):
		return None
	letto = U.letto(numero)
	if phonenumbers.number_type(letto) not in CELLULARI:
		return None
	return phonenumbers.format_number(letto, phonenumbers.PhoneNumberFormat.E164)


def chiave_del_giorno(numero: str, giorno: datetime.date) -> str:
	"""Once a day for each number: the day is the centre's."""
	return f"crm_sms_chiamata_persa:{numero}:{giorno.isoformat()}"
