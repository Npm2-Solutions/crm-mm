# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The language DottorCloud writes its own words in on a site, the currency it
counts in, and the framework's Italian switched on for the visitors.

What DottorCloud puts in a site once - the consents' texts, the pipelines'
stages, the libraries' instructions and names - is data written in one language,
not the interface, which follows each user's. That language is the site's,
Italian first: a site left on the framework's English while the centre is in
Italy, or nowhere said, was set up in English before anybody chose, and its people
read Italian. English is for a site that chose it and is not in Italy.

Words DottorCloud wrote in another language follow this one (a migrate, the setup
wizard); words a centre wrote stay as they are.
"""

from __future__ import annotations

import re

import frappe

# In Italian an article, or a preposition with its article, drops its vowel
# before a day read with one: «l'1 ottobre», «dall'8/3», «fino all'11 settembre».
# A sentence's date is known only once it is filled, so the rule is applied to
# the filled sentence, and only before the day of a date: the same as the SPA's
# translator (`conLApostrofo`, utils/locale.js), and a date written 11-10 or
# 11.10 too, as the site's format may write it.
_ELISIONI = {"il": "l'", "dal": "dall'", "al": "all'", "del": "dell'", "nel": "nell'", "sul": "sull'"}
_MESI = "gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic"
_DAVANTI_A_UNA_DATA = re.compile(
	rf"(^|[^\w'’])(il|dal|al|del|nel|sul) (1|8|11)(?= (?:{_MESI})|[/.-]\d)", re.IGNORECASE
)


def con_l_apostrofo(testo, lingua: str | None = None):
	"""``testo``, a sentence already filled, with the article before a date's 1, 8
	or 11 elided in Italian (``lingua``, else the session's); anything else as it is."""
	if not isinstance(testo, str):
		return testo
	if lingua is None:
		lingua = getattr(frappe.local, "lang", None) or ""
	if not lingua.lower().startswith("it"):
		return testo

	def eliso(trovato) -> str:
		prima, articolo, giorno = trovato.groups()
		parola = _ELISIONI[articolo.lower()]
		if articolo[0].isupper():
			parola = parola[0].upper() + parola[1:]
		return f"{prima}{parola}{giorno}"

	return _DAVANTI_A_UNA_DATA.sub(eliso, testo)


def scegli(lingua: str | None, paese: str | None) -> str:
	"""The rule, without a site: ``lingua`` and ``paese`` as System Settings keep them."""
	lingua = (lingua or "")[:2]
	if not lingua or (lingua == "en" and paese in (None, "", "Italy")):
		return "it"
	return lingua


def del_centro() -> str:
	"""This site's: its System Settings' language and country."""
	return scegli(
		frappe.db.get_single_value("System Settings", "language"),
		frappe.db.get_single_value("System Settings", "country"),
	)


def accendi_l_italiano() -> None:
	"""The framework's Italian switched on, at install and at every migrate.

	The framework ships it switched off (`frappe/geo/languages.csv`), and a
	visitor reads only a language the site has on: every page a patient opens
	without signing in - /prenota, the area's door, a form sent to fill, the
	sign-in - came in English to a phone set in Italian, and the setup wizard did
	not offer Italian. DottorCloud's words are Italian first (`crm/locale/it.po`).
	The Language's own save empties the framework's cache of the languages on."""
	if frappe.db.get_value("Language", "it", "enabled") == 0:
		lingua = frappe.get_doc("Language", "it")
		lingua.enabled = 1
		lingua.save(ignore_permissions=True)


def valuta() -> str:
	"""The currency the centre counts in: the one chosen in Settings, else its
	country's, the euro where nobody said where the centre is (the rule of
	``scegli``). The framework's CRM fell back on the dollar: a centre in Italy
	read "0 USD" on its dashboard, and every deal in euros was converted to
	dollars at the day's rate."""
	scelta = frappe.db.get_single_value("FCRM Settings", "currency")
	if scelta:
		return scelta
	from frappe.geo.country_info import get_country_info

	paese = frappe.db.get_single_value("System Settings", "country") or "Italy"
	return (get_country_info(paese) or {}).get("currency") or "EUR"
