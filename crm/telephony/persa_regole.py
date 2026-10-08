# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered, without a site (doc 52).

- **Somebody the centre knows**: the automations hear «Missed Call»; what they do
  is the centre's (the recipe texts the booking page a minute later).
- **A number nobody knows**: where the centre wants it, one SMS of service to the
  number that called - an Italian or a foreign mobile of the countries the centre
  calls, never a premium-rate number nor a landline, which reads no SMS - at most
  once a day for each number.

When a call counts as missed is the centre's (Settings > Phone > Answering
service, «Missed calls»): nobody picked up after ringing (on to start with),
there was nobody to ring, the answering service takes every call.
"""

from __future__ import annotations

import datetime

import phonenumbers

from crm.telephony import uscita_regole as U

#: The kinds of number that read an SMS.
CELLULARI = frozenset(
	{phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE}
)


#: The cases of a missed call, each with its switch on `CRM Answering Settings` and
#: what a centre that never saved one reads.
NESSUNO_RISPONDE = "nessuno_risponde"
NESSUNO_DA_FAR_SQUILLARE = "nessuno_da_far_squillare"
SEGRETERIA = "segreteria"
CASI = {
	NESSUNO_RISPONDE: ("missed_when_nobody_answers", 1),
	NESSUNO_DA_FAR_SQUILLARE: ("missed_when_nobody_to_ring", 0),
	SEGRETERIA: ("missed_when_service_answers", 0),
}


def conta(caso: str, impostazioni) -> bool:
	"""Whether a call that ended this way counts as missed, as the centre chose."""
	campo, prima = CASI[caso]
	valore = (impostazioni or {}).get(campo)
	return bool(int(prima if valore is None else valore))


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
	"""The lock two jobs of the same day race for; once a day is the register's
	(`crm.telephony.persa.gia_scritto`). The day is the centre's."""
	return f"crm_sms_chiamata_persa:{numero}:{giorno.isoformat()}"
