"""Fiscal identifiers: codice fiscale, partita IVA, EU VAT numbers, IBAN.

The operating rule: **validate the check character, not the length.** A codice
fiscale encodes surname, first name and date of birth, so comparing it with the
registry catches the swapped patient - the most expensive mistake there is,
because the expense lands in somebody else's pre-filled tax return.

EU VAT numbers matter here in a way they did not in the original design: this
system runs in Europe and invoices across it, so a client in Berlin or Madrid is
an ordinary case, not an exception to be hand-waved into `codice destinatario
XXXXXXX`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

_DISPARI = {
	"0": 1,
	"1": 0,
	"2": 5,
	"3": 7,
	"4": 9,
	"5": 13,
	"6": 15,
	"7": 17,
	"8": 19,
	"9": 21,
	"A": 1,
	"B": 0,
	"C": 5,
	"D": 7,
	"E": 9,
	"F": 13,
	"G": 15,
	"H": 17,
	"I": 19,
	"J": 21,
	"K": 2,
	"L": 4,
	"M": 18,
	"N": 20,
	"O": 11,
	"P": 3,
	"Q": 6,
	"R": 8,
	"S": 12,
	"T": 14,
	"U": 16,
	"V": 10,
	"W": 22,
	"X": 25,
	"Y": 24,
	"Z": 23,
}
_PARI = {c: i for i, c in enumerate("0123456789")}
_PARI.update({c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")})

#: Omocodia substitutions: digits become letters, in seven fixed positions.
_OMOCODIA = {
	"0": "L",
	"1": "M",
	"2": "N",
	"3": "P",
	"4": "Q",
	"5": "R",
	"6": "S",
	"7": "T",
	"8": "U",
	"9": "V",
}
_OMOCODIA_INV = {v: k for k, v in _OMOCODIA.items()}
_POSIZIONI_NUMERICHE = (6, 7, 9, 10, 12, 13, 14)

_MESI = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "H": 6, "L": 7, "M": 8, "P": 9, "R": 10, "S": 11, "T": 12}

_CIFRA_O_OMOCODO = "0-9" + "".join(_OMOCODIA.values())
_PATTERN = re.compile(
	rf"^[A-Z]{{6}}[{_CIFRA_O_OMOCODO}]{{2}}[ABCDEHLMPRST][{_CIFRA_O_OMOCODO}]{{2}}"
	rf"[A-Z][{_CIFRA_O_OMOCODO}]{{3}}[A-Z]$"
)

_VOCALI = set("AEIOU")


@dataclass(frozen=True)
class DatiCodiceFiscale:
	"""Registry data read back out of the codice fiscale."""

	codice: str
	codice_normalizzato: str
	cognome_nome: str
	data_nascita: date | None
	sesso: str | None
	codice_catastale: str
	omocodia: bool


def _pulisci(valore: str | None) -> str:
	return re.sub(r"[^A-Z0-9]", "", (valore or "").upper())


def carattere_controllo(primi_quindici: str) -> str:
	"""The 16th character, computed from the first 15."""
	if len(primi_quindici) != 15:
		raise ValueError("fifteen characters are required")
	totale = 0
	for indice, carattere in enumerate(primi_quindici.upper()):
		# Positions are 1-indexed in the specification: index 0 is "odd".
		tabella = _DISPARI if indice % 2 == 0 else _PARI
		try:
			totale += tabella[carattere]
		except KeyError as exc:
			raise ValueError(f"character not admitted: {carattere!r}") from exc
	return chr(ord("A") + totale % 26)


def normalizza(codice: str) -> str:
	"""Bring an omocodia codice fiscale back to its base numeric form.

	The check character is **recomputed**: the normalised form is itself a valid
	codice fiscale, and it is the one to deduplicate two omocodes of the same
	person on.
	"""
	codice = _pulisci(codice)
	if len(codice) != 16:
		return codice
	caratteri = list(codice)
	for pos in _POSIZIONI_NUMERICHE:
		caratteri[pos] = _OMOCODIA_INV.get(caratteri[pos], caratteri[pos])
	primi_quindici = "".join(caratteri[:15])
	try:
		return primi_quindici + carattere_controllo(primi_quindici)
	except ValueError:
		return "".join(caratteri)


def valido(codice: str | None) -> bool:
	"""True when the codice fiscale is formally valid, **omocodia included**.

	An omocodia code is valid. It is not an error, and it is the classic stumble
	of a validator written by eye.
	"""
	codice = _pulisci(codice)
	if len(codice) != 16 or not _PATTERN.match(codice):
		return False
	return carattere_controllo(codice[:15]) == codice[15]


def analizza(codice: str) -> DatiCodiceFiscale:
	"""Validate and decode. Raises `ValueError` when the code is not valid."""
	grezzo = _pulisci(codice)
	if not valido(grezzo):
		raise ValueError(f"codice fiscale not valid: {codice!r}")
	normale = normalizza(grezzo)
	anno_due = int(normale[6:8])
	giorno = int(normale[9:11])
	sesso = "F" if giorno > 40 else "M"
	if sesso == "F":
		giorno -= 40
	mese = _MESI[normale[8]]
	# The century is not encoded: pick the one that does not produce a future date.
	anno = 2000 + anno_due
	if anno > date.today().year:
		anno -= 100
	try:
		nascita: date | None = date(anno, mese, giorno)
	except ValueError:
		nascita = None
	return DatiCodiceFiscale(
		codice=grezzo,
		codice_normalizzato=normale,
		cognome_nome=normale[:6],
		data_nascita=nascita,
		sesso=sesso,
		codice_catastale=normale[11:15],
		omocodia=grezzo != normale,
	)


def _lettere(valore: str) -> str:
	senza_accenti = unicodedata.normalize("NFKD", valore or "")
	senza_accenti = "".join(c for c in senza_accenti if not unicodedata.combining(c))
	return re.sub(r"[^A-Z]", "", senza_accenti.upper())


def _tripletta_cognome(cognome: str) -> str:
	lettere = _lettere(cognome)
	consonanti = [c for c in lettere if c not in _VOCALI]
	vocali = [c for c in lettere if c in _VOCALI]
	return "".join((consonanti + vocali + ["X", "X", "X"])[:3])


def _tripletta_nome(nome: str) -> str:
	lettere = _lettere(nome)
	consonanti = [c for c in lettere if c not in _VOCALI]
	if len(consonanti) >= 4:
		# With four or more consonants, take the first, the third and the fourth.
		return consonanti[0] + consonanti[2] + consonanti[3]
	vocali = [c for c in lettere if c in _VOCALI]
	return "".join((consonanti + vocali + ["X", "X", "X"])[:3])


def coerente_con_anagrafica(
	codice: str,
	cognome: str | None = None,
	nome: str | None = None,
	data_nascita: date | None = None,
	sesso: str | None = None,
) -> list[str]:
	"""Compare the codice fiscale with the declared registry data.

	Returns the list of inconsistencies (empty means everything lines up). It does
	not raise: this is a plausibility check, and on foreign or double surnames it
	produces false positives that belong in front of an operator, not in an
	automatic block.
	"""
	problemi: list[str] = []
	try:
		dati = analizza(codice)
	except ValueError as exc:
		return [str(exc)]

	if cognome:
		atteso = _tripletta_cognome(cognome)
		if atteso != dati.cognome_nome[:3]:
			problemi.append(
				f"surname {cognome!r} would give {atteso!r}, the code carries {dati.cognome_nome[:3]!r}"
			)
	if nome:
		atteso = _tripletta_nome(nome)
		if atteso != dati.cognome_nome[3:6]:
			problemi.append(
				f"first name {nome!r} would give {atteso!r}, the code carries {dati.cognome_nome[3:6]!r}"
			)
	if data_nascita and dati.data_nascita and data_nascita != dati.data_nascita:
		problemi.append(
			f"date of birth declared {data_nascita.isoformat()}, "
			f"the code encodes {dati.data_nascita.isoformat()}"
		)
	if sesso and dati.sesso and sesso.upper()[:1] != dati.sesso:
		problemi.append(f"sex declared {sesso}, the code encodes {dati.sesso}")
	return problemi


def partita_iva_valida(piva: str | None) -> bool:
	"""Italian VAT number: eleven digits with the Luhn-style check digit.

	Careful: doctors without a VAT number are assigned an eleven-digit code by the
	Sistema TS to use in its place. That code does **not** pass this check - use
	`identificativo_ts_valido` on the tracciato's `pIva` field.
	"""
	piva = _pulisci(piva)
	if len(piva) != 11 or not piva.isdigit():
		return False
	totale = 0
	for indice, cifra in enumerate(int(c) for c in piva[:10]):
		if indice % 2 == 0:
			totale += cifra
		else:
			doppio = cifra * 2
			totale += doppio - 9 if doppio > 9 else doppio
	return (10 - totale % 10) % 10 == int(piva[10])


def identificativo_ts_valido(valore: str | None) -> bool:
	"""The tracciato's `pIva` field: exactly eleven digits.

	Accepts both a real VAT number and the eleven-digit substitute the Sistema TS
	issues to professionals who do not have one.
	"""
	valore = _pulisci(valore)
	return len(valore) == 11 and valore.isdigit()


# ------------------------------------------------------------- EU VAT numbers

#: Format of the VAT number per member state, without the country prefix. Format
#: only: it says the number is well formed, never that it exists or is active.
#: Only VIES can say that, and it is a network call - it does not belong here.
_FORMATI_IVA_UE: dict[str, str] = {
	"AT": r"U\d{8}",
	"BE": r"[01]\d{9}",
	"BG": r"\d{9,10}",
	"CY": r"\d{8}[A-Z]",
	"CZ": r"\d{8,10}",
	"DE": r"\d{9}",
	"DK": r"\d{8}",
	"EE": r"\d{9}",
	"EL": r"\d{9}",
	"ES": r"[A-Z0-9]\d{7}[A-Z0-9]",
	"FI": r"\d{8}",
	"FR": r"[A-Z0-9]{2}\d{9}",
	"HR": r"\d{11}",
	"HU": r"\d{8}",
	"IE": r"(\d{7}[A-Z]{1,2}|\d[A-Z*+]\d{5}[A-Z])",
	"IT": r"\d{11}",
	"LT": r"(\d{9}|\d{12})",
	"LU": r"\d{8}",
	"LV": r"\d{11}",
	"MT": r"\d{8}",
	"NL": r"\d{9}B\d{2}",
	"PL": r"\d{10}",
	"PT": r"\d{9}",
	"RO": r"\d{2,10}",
	"SE": r"\d{12}",
	"SI": r"\d{8}",
	"SK": r"\d{10}",
	# Not the EU, but neighbours an Italian invoice meets constantly.
	"CH": r"\d{9}(MWST|TVA|IVA)?",
	"GB": r"(\d{9}|\d{12}|GD\d{3}|HA\d{3})",
	"NO": r"\d{9}(MVA)?",
	"SM": r"\d{5}",
}

#: Member states, for the "is this an intra-EU supply" question.
STATI_UE: frozenset[str] = frozenset(
	{
		"AT",
		"BE",
		"BG",
		"CY",
		"CZ",
		"DE",
		"DK",
		"EE",
		"ES",
		"FI",
		"FR",
		"GR",
		"EL",
		"HR",
		"HU",
		"IE",
		"IT",
		"LT",
		"LU",
		"LV",
		"MT",
		"NL",
		"PL",
		"PT",
		"RO",
		"SE",
		"SI",
		"SK",
	}
)


def separa_partita_iva_ue(valore: str | None) -> tuple[str | None, str]:
	"""Split a VAT number into `(country, number)`.

	`IT01234567890` and `01234567890` both come back with the number; only the
	first one comes back with a country. The caller decides what a missing
	country means - here it is not guessed.
	"""
	pulito = _pulisci(valore)
	if len(pulito) > 2 and pulito[:2].isalpha() and pulito[:2] in _FORMATI_IVA_UE:
		return pulito[:2], pulito[2:]
	return None, pulito


def partita_iva_ue_valida(valore: str | None, paese: str | None = None) -> bool:
	"""Format check of an EU VAT number.

	`paese` is used when the number does not carry its own prefix. An unknown
	country returns False rather than True-by-default: an invoice that travels
	with a malformed VAT number comes back, and it comes back late.
	"""
	prefisso, numero = separa_partita_iva_ue(valore)
	stato = (prefisso or paese or "").upper()
	if stato == "GR":
		stato = "EL"
	formato = _FORMATI_IVA_UE.get(stato)
	if not formato or not numero:
		return False
	if stato == "IT":
		return partita_iva_valida(numero)
	return bool(re.fullmatch(formato, numero))


def e_intracomunitario(paese: str | None) -> bool:
	"""True for a member state other than Italy."""
	stato = (paese or "").upper()
	return stato in STATI_UE and stato != "IT"


# --------------------------------------------------------------------- IBAN

_IBAN_LUNGHEZZE: dict[str, int] = {
	"AD": 24,
	"AT": 20,
	"BE": 16,
	"BG": 22,
	"CH": 21,
	"CY": 28,
	"CZ": 24,
	"DE": 22,
	"DK": 18,
	"EE": 20,
	"ES": 24,
	"FI": 18,
	"FR": 27,
	"GB": 22,
	"GR": 27,
	"HR": 21,
	"HU": 28,
	"IE": 22,
	"IS": 26,
	"IT": 27,
	"LI": 21,
	"LT": 20,
	"LU": 20,
	"LV": 21,
	"MC": 27,
	"MT": 31,
	"NL": 18,
	"NO": 15,
	"PL": 28,
	"PT": 25,
	"RO": 24,
	"SE": 24,
	"SI": 19,
	"SK": 24,
	"SM": 27,
}


def iban_valido(iban: str | None) -> bool:
	"""IBAN with the mod-97 check and the country's declared length.

	The length matters as much as the checksum: a truncated IBAN can still pass
	mod-97 by chance, and a wrong IBAN on an invoice is a payment that never
	arrives with nobody being told.
	"""
	pulito = _pulisci(iban)
	if len(pulito) < 15 or not pulito[:2].isalpha():
		return False
	atteso = _IBAN_LUNGHEZZE.get(pulito[:2])
	if atteso is not None and len(pulito) != atteso:
		return False
	riordinato = pulito[4:] + pulito[:4]
	numerico = "".join(str(ord(c) - 55) if c.isalpha() else c for c in riordinato)
	return int(numerico) % 97 == 1
