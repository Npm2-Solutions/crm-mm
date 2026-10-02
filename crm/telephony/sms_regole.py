# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The SMS of the centre, without a site (doc 52, fourth part).

- **One sender**: the centre's name - up to eleven letters, digits and spaces,
  not digits alone, what Twilio takes as a name - or one of its numbers that can
  send SMS, when the centre wants the answers.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import re
import unicodedata

#: Twilio's longest name for a sender.
LUNGHEZZA_NOME = 11

#: Words of a centre's name that say what it is, not which one: the first to go
#: when the name is too long to be the sender's.
GENERICHE = frozenset(
	{
		"CENTRO",
		"STUDIO",
		"POLIAMBULATORIO",
		"AMBULATORIO",
		"CLINICA",
		"ISTITUTO",
		"LABORATORIO",
		"MEDICO",
		"MEDICA",
		"MEDICI",
		"DENTISTICO",
		"ODONTOIATRICO",
		"FISIOTERAPICO",
		"DOTT",
		"DOTTOR",
		"DOTTORESSA",
		"DR",
		"DI",
		"DEL",
		"DELLA",
		"DEI",
		"E",
		"C",
		"SRL",
		"SRLS",
		"SNC",
		"SAS",
		"SPA",
		"STP",
	}
)


def problema_del_nome(nome: str | None) -> str:
	"""Why ``nome`` cannot be the sender's name; '' when it can."""
	nome = (nome or "").strip()
	if not nome:
		return "Write the name people will see as the sender."
	if len(nome) > LUNGHEZZA_NOME:
		return "The name can be at most 11 characters, spaces included."
	if not re.fullmatch(r"[A-Za-z0-9 ]+", nome):
		return "The name can have only letters without accents, digits and spaces."
	if nome.replace(" ", "").isdigit():
		return "The name cannot be digits alone: it would look like a number."
	return ""


def nome_dal_centro(nome_centro: str | None) -> str:
	"""A sender's name made from the centre's: accents taken away, only letters,
	digits and spaces, eleven characters at most, never a word cut in half. A name
	too long loses first the words that say what the centre is ("Centro Medico
	Aurora" is "Aurora"), then the last words; '' when nothing is left."""
	semplice = unicodedata.normalize("NFKD", nome_centro or "").encode("ascii", "ignore").decode()
	# D'Amico is one word
	semplice = re.sub(r"['’]", "", semplice)
	semplice = re.sub(r"[^A-Za-z0-9 ]+", " ", semplice)
	semplice = re.sub(r"\s+", " ", semplice).strip()
	if not problema_del_nome(semplice):
		return semplice
	parole = semplice.split()
	if not parole:
		return ""
	proprie = [parola for parola in parole if parola.upper() not in GENERICHE] or parole
	scelte: list[str] = []
	for parola in proprie:
		if len(" ".join([*scelte, parola])) > LUNGHEZZA_NOME:
			break
		scelte.append(parola)
	nome = " ".join(scelte) or proprie[0][:LUNGHEZZA_NOME]
	return "" if problema_del_nome(nome) else nome
