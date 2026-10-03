# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Calls going out from DottorCloud, without a site (doc 52, third part).

- **Where a call may go**: the countries the centre chose (Italy to start with),
  never a premium-rate number - the commonest fraud on a stolen telephone line
  calls those, for money. A number is read with its country, an Italian one
  written without the +39 too.
- **Which number it shows**: one of the centre's; an Italian mobile shown on a
  call to Italy is blocked since 19 November 2025 (AGCOM 106/25/CONS: a call
  from abroad - Twilio's - with an Italian mobile as its number), so the screen
  says so. An Italian landline of another operator's, only verified in Twilio,
  may be blocked the same way since 19 August 2025: the screen warns.
- **Twilio's own permissions**: the countries the space may call, set the same
  way in Twilio, so a key that leaked could not call anywhere else either.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import json
import re

import phonenumbers

#: Italy, where a centre calls to start with.
ITALIA = "IT"
#: The number types never called, whatever the country.
A_PAGAMENTO = frozenset({phonenumbers.PhoneNumberType.PREMIUM_RATE})


def letto(numero: str | None) -> phonenumbers.PhoneNumber | None:
	"""A number as written, its country found: +44…, 0044…, or Italian without +39."""
	scritto = (numero or "").strip()
	if not scritto:
		return None
	if scritto.startswith("00"):
		scritto = "+" + scritto[2:]
	try:
		letto_ = phonenumbers.parse(scritto, ITALIA)
	except phonenumbers.NumberParseException:
		return None
	return letto_ if phonenumbers.is_possible_number(letto_) else None


def paese_di(numero: str | None) -> str:
	"""The country of a number (ISO 3166 alpha-2); '' when it cannot be read."""
	letto_ = letto(numero)
	return (phonenumbers.region_code_for_number(letto_) or "") if letto_ else ""


def paesi(valore) -> list[str]:
	"""The countries the centre chose, as stored - "IT, CH", a JSON list - as
	codes, sorted, Italy when nothing is left."""
	if isinstance(valore, str):
		try:
			valore = json.loads(valore)
		except ValueError:
			valore = re.split(r"[\s,;]+", valore)
	codici = {
		str(codice).strip().upper()
		for codice in (valore or [])
		if re.fullmatch(r"[A-Za-z]{2}", str(codice).strip())
	}
	return sorted(codici) or [ITALIA]


def si_chiama(numero: str | None, consentiti) -> str:
	"""Why a number may not be called; '' when it may."""
	letto_ = letto(numero)
	if not letto_:
		return "This number cannot be read: write it with its country code, +39 for Italy."
	if phonenumbers.number_type(letto_) in A_PAGAMENTO:
		return (
			"Premium-rate numbers are never called: they are where a stolen line is made to call, for money."
		)
	paese = phonenumbers.region_code_for_number(letto_) or ""
	if paese not in paesi(consentiti):
		return "Calls to this country are not allowed: the manager adds it in Settings → Phone → Telephony → Twilio."
	return ""


def cellulare_italiano(numero: str | None) -> bool:
	"""Whether a number is an Italian mobile: shown on a call from abroad to Italy,
	since 19/11/2025 the call is blocked."""
	letto_ = letto(numero)
	return bool(
		letto_
		and phonenumbers.region_code_for_number(letto_) == ITALIA
		and phonenumbers.number_type(letto_) == phonenumbers.PhoneNumberType.MOBILE
	)


def bloccata_in_italia(mostrato: str | None, chiamato: str | None) -> bool:
	"""Whether a call showing ``mostrato`` to ``chiamato`` is one AGCOM has blocked."""
	return cellulare_italiano(mostrato) and paese_di(chiamato) == ITALIA


def incerta_in_italia(mostrato: str | None, chiamato: str | None, verificato: bool) -> bool:
	"""Whether a call showing ``mostrato`` to ``chiamato`` may arrive without that
	number, or not arrive: an Italian landline of another operator's, only verified
	in Twilio, shown on a call to Italy. Since 19/08/2025 an Italian operator may
	block a call from abroad that shows an Italian landline of somebody else's
	network (AGCOM 106/25/CONS), and Twilio shows a verified Italian number in Italy
	only as far as the operators let it. A number bought in Twilio, or moved there,
	is shown for certain."""
	return (
		bool(verificato)
		and paese_di(mostrato) == ITALIA
		and not cellulare_italiano(mostrato)
		and paese_di(chiamato) == ITALIA
	)


#: Twilio's three switches of a country: its ordinary numbers, its special ones,
#: the ones it flags for toll fraud.
INTERRUTTORI = (
	"low_risk_numbers_enabled",
	"high_risk_special_numbers_enabled",
	"high_risk_tollfraud_numbers_enabled",
)


def cambi_dei_permessi(consentiti, attuali: list[dict]) -> list[dict]:
	"""What Twilio's permissions of the space must change, and only that: the
	countries chosen callable at their ordinary numbers - never their special and
	toll-fraud ones - and every other country switched off. ``attuali``: the
	countries Twilio has something switched on for now, each with its three
	switches. Nothing when all is in place."""
	scelti = paesi(consentiti)
	ora = {a["iso_code"]: a for a in attuali or []}
	voluto = dict(zip(INTERRUTTORI, (True, False, False), strict=True))
	spento = dict.fromkeys(INTERRUTTORI, False)
	cambi = []
	for paese in sorted(set(scelti) | set(ora)):
		desiderato = voluto if paese in scelti else spento
		attuale = {chiave: bool(ora.get(paese, {}).get(chiave)) for chiave in INTERRUTTORI}
		if attuale != desiderato:
			cambi.append({"iso_code": paese, **desiderato})
	return cambi
