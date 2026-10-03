# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The language DottorCloud writes its own words in on a site.

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
