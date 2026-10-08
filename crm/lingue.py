# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The language DottorCloud writes its own words in on a site, the currency it
counts in, and the two languages it speaks: Italian and English, nothing else.

What DottorCloud puts in a site once - the consents' texts, the pipelines'
stages, the libraries' instructions and names - is data written in one language,
not the interface, which follows each user's. That language is the site's,
Italian first: a site left on the framework's English while the centre is in
Italy, or nowhere said, was set up in English before anybody chose, and its people
read Italian. English is for a site that chose it and is not in Italy.

Words DottorCloud wrote in another language follow this one (a migrate, the setup
wizard, the centre choosing another in Settings > The centre > General > Language
& time); words a centre wrote stay as they are. The language a centre chose there
is its own whatever its country (`SCELTA`): an English-speaking centre in Italy.
"""

from __future__ import annotations

import re
import zoneinfo

import frappe
from frappe import _

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
	"""The rule, without a site: ``lingua`` and ``paese`` as System Settings keep
	them. One of the two DottorCloud speaks: English for a centre out of Italy
	that chose it, or chose a language DottorCloud has no words in; Italian
	everywhere else."""
	lingua = (lingua or "")[:2]
	if lingua and lingua != "it" and paese not in (None, "", "Italy"):
		return "en"
	return "it"


#: The languages DottorCloud speaks: its words are in these two (`it.po`, and the
#: English they are written in), and so every screen, page and email.
LINGUE = ("it", "en")
#: Each in its own words, as a choice of language names it to its readers.
NOMI = {"it": "Italiano", "en": "English"}
#: The language the centre chose in Settings, whatever its country (a default).
SCELTA = "crm_lingua_del_centro"


def del_centro() -> str:
	"""This site's: the one the centre chose, else its System Settings' language
	and country."""
	scelta = frappe.db.get_default(SCELTA)
	if scelta in LINGUE:
		return scelta
	return scegli(
		frappe.db.get_single_value("System Settings", "language"),
		frappe.db.get_single_value("System Settings", "country"),
	)


def solo_italiano_e_inglese() -> None:
	"""At install and at every migrate: Italian and English on, every other
	language off, and the centre's the language of whoever has not chosen their
	own.

	The framework ships Italian switched off (`frappe/geo/languages.csv`), and a
	visitor reads only a language the site has on: every page a patient opens
	without signing in - /prenota, the area's door, a form sent to fill, the
	sign-in - came in English to a phone set in Italian. And it ships sixteen
	others on, in which DottorCloud has no words: a phone set in German read the
	framework's German around DottorCloud's English. Now it reads English where
	it accepts it too, else the centre's language; the choices of language offer
	these two.

	The language System Settings keep is the one a user without their own reads
	(the framework's "lang"): the centre's (`del_centro`), never English left by
	the framework on a centre in Italy while DottorCloud wrote its words in
	Italian, nor a language it has no words in."""
	accese = set(frappe.get_all("Language", filters={"enabled": 1}, pluck="name"))
	cambiate = False
	for codice in LINGUE:
		if codice not in accese and frappe.db.exists("Language", codice):
			frappe.db.set_value("Language", codice, "enabled", 1)
			cambiate = True
	altre = sorted(accese - set(LINGUE))
	if altre:
		frappe.db.set_value("Language", {"name": ("in", altre)}, "enabled", 0)
		cambiate = True
	if cambiate:
		# what the Language's own save empties: the framework's lists of those on
		frappe.cache.delete_value("languages_with_name")
		frappe.client_cache.delete_value("languages")
	centro = del_centro()
	if frappe.db.get_single_value("System Settings", "language") != centro:
		from frappe.translate import set_default_language

		# what the settings' own save writes: the field, its default, "lang"
		frappe.db.set_single_value("System Settings", "language", centro)
		frappe.db.set_default("language", centro)
		set_default_language(centro)


def euro_come_si_scrive() -> None:
	"""The euro where the centre's language writes it: after the amount in Italian
	(«60,00 €»), before it in English («€60.00»). The framework writes every
	amount by its Currency's ``symbol_on_right``: /prenota's price, a deal's
	value and a company's revenue read «€ 60,00» to an Italian centre."""
	if not frappe.db.exists("Currency", "EUR"):
		return
	dopo = 1 if del_centro() == "it" else 0
	if frappe.db.get_value("Currency", "EUR", "symbol_on_right") != dopo:
		frappe.db.set_value("Currency", "EUR", "symbol_on_right", dopo, update_modified=False)
		frappe.clear_cache()


def utenti_in_italiano_o_inglese() -> int:
	"""Whoever had chosen another language reads the centre's (the patch, once):
	DottorCloud has no words in it. How many."""
	utenti = frappe.get_all("User", filters={"language": ("not in", ["", *LINGUE])}, pluck="name")
	if utenti:
		frappe.db.set_value("User", {"name": ("in", utenti)}, "language", "", update_modified=False)
		frappe.clear_cache()
	return len(utenti)


# ------------------------------------------------------------------ the centre's, in Settings


def fusi_europei() -> list[str]:
	"""The time zones a centre in Europe keeps its clock on: the continent's, the
	Canaries', Madeira's and the Azores'."""
	return sorted(
		zona
		for zona in zoneinfo.available_timezones()
		if zona.startswith("Europe/") or zona in ("Atlantic/Canary", "Atlantic/Madeira", "Atlantic/Azores")
	)


@frappe.whitelist()
def get_centre_language() -> dict:
	"""The centre's language and clock, as Settings shows them."""
	from crm.permissions import livelli

	livelli.verifica("impostazioni.generali")
	fuso = frappe.db.get_single_value("System Settings", "time_zone") or ITALIA["time_zone"]
	zone = fusi_europei()
	return {
		"language": del_centro(),
		"languages": [{"value": codice, "label": NOMI[codice]} for codice in LINGUE],
		"time_zone": fuso,
		"time_zones": zone if fuso in zone else [fuso, *zone],
	}


@frappe.whitelist(methods=["POST"])
def save_centre_language(language: str, time_zone: str | None = None) -> dict:
	"""The centre's language - the one DottorCloud writes in for it, and the one of
	whoever has not chosen their own - and its clock. DottorCloud's words follow
	the new language in the background; whoever kept the centre's clock follows
	the new one."""
	from crm.permissions import livelli

	livelli.verifica("impostazioni.generali")
	impostazioni = frappe.get_single("System Settings")
	fuso_prima = impostazioni.time_zone
	if language not in LINGUE:
		frappe.throw(_("Choose Italian or English"))
	# the zone it had stays a choice, wherever it is: only a new one is Europe's
	if time_zone and time_zone != fuso_prima and time_zone not in fusi_europei():
		frappe.throw(_("Choose a time zone of Europe"))
	prima = del_centro()
	impostazioni.language = language
	if time_zone:
		impostazioni.time_zone = time_zone
	impostazioni.flags.ignore_permissions = True
	impostazioni.save()
	frappe.db.set_default(SCELTA, language)
	if time_zone and fuso_prima and time_zone != fuso_prima:
		utenti_sul_fuso_del_centro(time_zone, da=fuso_prima)
	if language != prima:
		frappe.enqueue(
			"crm.lingue.dopo_il_cambio",
			queue="long",
			job_id="crm-lingua-del-centro",
			deduplicate=True,
			enqueue_after_commit=True,
		)
	return get_centre_language()


def dopo_il_cambio() -> None:
	"""The centre chose another language: DottorCloud's own words follow it - the
	consents', the libraries', the qualifications' - as after the setup wizard
	(`crm_lingua_del_centro` in hooks.py); the centre's own stay."""
	for metodo in frappe.get_hooks("crm_lingua_del_centro"):
		try:
			frappe.get_attr(metodo)()
		except Exception:
			frappe.log_error(title=f"DottorCloud: the centre's language, {metodo}")


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
	values - never over a format somebody chose. But the week, which starts on
	Monday everywhere in Europe whoever chose Sunday: the agenda, the pickers and
	the dashboard's periods count from Monday whatever the site says."""
	paese = attuali.get("country") or ""
	cambi = {}
	if attuali.get("first_day_of_the_week") != "Monday":
		cambi["first_day_of_the_week"] = "Monday"
	if paese and paese != "Italy":
		return cambi
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


def utenti_sul_fuso_del_centro(fuso: str, da: str = FUSO_DEL_FRAMEWORK) -> int:
	"""Whoever was made while the site had no zone took the framework's fallback as
	their own, and the screens showed them its hours: they follow the centre's, which
	they never chose. The same for whoever kept the centre's clock when it moves
	(`da`, the one before). How many did."""
	utenti = frappe.get_all("User", filters={"time_zone": da}, pluck="name")
	if not utenti:
		return 0
	frappe.db.set_value("User", {"name": ("in", utenti)}, "time_zone", fuso, update_modified=False)
	frappe.db.set_value(
		"DefaultValue",
		{"parent": ("in", utenti), "defkey": "time_zone", "defvalue": da},
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
