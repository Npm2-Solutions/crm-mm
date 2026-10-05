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
# 11.10 too, as the site's format may write it, with its day's zero too
# («dall'08/10/2026»: Italy's format writes it).
_ELISIONI = {"il": "l'", "dal": "dall'", "al": "all'", "del": "dell'", "nel": "nell'", "sul": "sull'"}
_MESI = "gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic"
_DAVANTI_A_UNA_DATA = re.compile(
	rf"(^|[^\w'’])(il|dal|al|del|nel|sul) (0?1|0?8|11)(?= (?:{_MESI})|[/.-]\d)", re.IGNORECASE
)


def con_l_apostrofo(testo, lingua: str | None = None):
	"""``testo``, a sentence already filled, with the article before a date's 1, 8
	or 11 (01, 08) elided in Italian (``lingua``, else the session's); anything else as it is."""
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


# What the setup wizard writes for a centre in Italy (the Country's formats),
# and the week from Monday that DottorCloud keeps everywhere
ITALIA = {
	"time_zone": "Europe/Rome",
	"currency": "EUR",
	"date_format": "dd/mm/yyyy",
	"number_format": "#.###,##",
	"first_day_of_the_week": "Monday",
}

#: The zone the framework falls back on where a site has none, and gives as their
#: own to every user made meanwhile (`User.set_time_zone`)
FUSO_DEL_FRAMEWORK = "Asia/Kolkata"

# What a site holds before anybody chose: the framework's own values, which a
# format chosen in Settings never is
_DEL_FRAMEWORK = {
	"time_zone": ("",),
	"currency": ("",),
	"date_format": ("", "yyyy-mm-dd"),
	"number_format": ("", "#,###.##"),
	"first_day_of_the_week": ("", "Sunday"),
}


def per_l_italia(attuali: dict) -> dict:
	"""The rule, without a site: what to write over System Settings' ``attuali``
	so that a site nobody set up reads as a centre in Italy.

	A country chosen elsewhere keeps everything; in Italy, only what is still
	empty; where nobody said, Italy, with its formats over the framework's own
	values - never over a format somebody chose."""
	paese = attuali.get("country") or ""
	if paese and paese != "Italy":
		return {}
	cambi = {}
	if not attuali.get("language"):
		# the one field of these the framework asks for: left empty, no save of
		# the settings went through, the Formats page's either
		cambi["language"] = "it"
	for campo, valore in ITALIA.items():
		attuale = attuali.get(campo) or ""
		if attuale == valore:
			continue
		if not attuale or (not paese and attuale in _DEL_FRAMEWORK[campo]):
			cambi[campo] = valore
	if not paese:
		cambi["country"] = "Italy"
	return cambi


def italia_dove_nessuno_ha_scelto() -> None:
	"""After every migrate: a site the setup wizard never ran on - its country
	empty - reads as a centre in Italy (``per_l_italia``).

	The framework left it on India's time zone (Asia/Kolkata, its fallback for an
	empty one): now, today and every reminder were three hours and a half ahead
	of the centre, and the dates were written «2026-10-05», the amounts
	«€ 50,000.00». The times already kept stay as they were written: an
	appointment's hours are the ones the desk chose on the agenda. The users made
	meanwhile took Kolkata as their own zone: they follow Rome. The language is
	written only where there is none, Italian as ``scegli`` reads such a site: a
	language chosen stays."""
	campi = ("country", "language", *ITALIA)
	impostazioni = frappe.get_single("System Settings")
	cambi = per_l_italia({campo: impostazioni.get(campo) for campo in campi})
	if not cambi:
		return
	impostazioni.update(cambi)
	impostazioni.flags.ignore_permissions = True
	try:
		impostazioni.save()
	except Exception:
		# a site whose settings no longer validate (another field of theirs)
		# still migrates: the formats wait for the next one
		frappe.log_error(title="DottorCloud: the site's Italian formats")
		return
	if "time_zone" in cambi:
		utenti_sul_fuso_del_centro(cambi["time_zone"])


def utenti_sul_fuso_del_centro(fuso: str) -> int:
	"""Whoever was made while the site had no zone took the framework's fallback as
	their own, and the screens showed them its hours: they follow the centre's, which
	they never chose. How many did."""
	utenti = frappe.get_all("User", filters={"time_zone": FUSO_DEL_FRAMEWORK}, pluck="name")
	if not utenti:
		return 0
	frappe.db.set_value("User", {"name": ("in", utenti)}, "time_zone", fuso, update_modified=False)
	frappe.db.set_value(
		"DefaultValue",
		{"parent": ("in", utenti), "defkey": "time_zone", "defvalue": FUSO_DEL_FRAMEWORK},
		"defvalue",
		fuso,
		update_modified=False,
	)
	frappe.clear_cache()
	return len(utenti)


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
