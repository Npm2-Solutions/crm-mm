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

import frappe


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
